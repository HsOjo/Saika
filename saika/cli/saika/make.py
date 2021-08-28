import importlib
import importlib.util
import os
import shutil
import sys
from distutils.command import build_ext
from typing import Any, List

import click

from saika import common
from saika.decorator import *
from saika.environ import Environ


def is_pkg_module(module):
    module_path = importlib.util.find_spec(module).origin
    return os.path.basename(module_path).startswith('__init__')


def gen_compile_template(paths: List[str], work_dir, lib_dir, tmp_dir='', cpy_dir=''):
    return '''#!%(executable)s
import multiprocessing
import os
import sys
import tempfile
from distutils.core import setup

from Cython.Build import cythonize

work_dir = '%(work_dir)s'
tmp_dir = '%(tmp_dir)s' or tempfile.mkdtemp()
cpy_dir = '%(cpy_dir)s' or tmp_dir
lib_dir = '%(lib_dir)s' or tmp_dir

os.chdir(work_dir)
sys.argv = [
    sys.argv[0], 'build', 
    '--build-base', tmp_dir, 
    '--build-lib', lib_dir,
    '--build-temp', tmp_dir,
    '-j', multiprocessing.cpu_count(),
]

paths = """%(paths)s""".split('\\n')

setup(
    ext_modules=cythonize(
        paths, compiler_directives=dict(
            language_level=sys.version_info.major
        ),
        build_dir=cpy_dir,
    )
)
''' % dict(
        executable=sys.executable,
        paths='\n'.join([
            os.path.relpath(path)
            for path in paths
        ]),
        work_dir=os.path.abspath(work_dir),
        lib_dir=os.path.abspath(lib_dir),
        tmp_dir=tmp_dir,
        cpy_dir=cpy_dir,
    )


def build_lib_modules(modules, lib_dir=None):
    work_dir = Environ.program_dir
    if lib_dir is None:
        lib_dir = os.path.join(work_dir, 'build/Cythonize')
    os.makedirs(lib_dir, exist_ok=True)

    paths = {}
    pkgs = []
    for module in modules:
        module_path = importlib.util.find_spec(module).origin
        if not os.path.basename(module_path).startswith('__init__'):
            paths[module] = module_path
        else:
            pkgs.append(module)

    path_setup = os.path.join(lib_dir, 'build.py')
    with open(path_setup, 'w') as io:
        io.write(gen_compile_template(list(paths.values()), work_dir, lib_dir, cpy_dir=lib_dir))

    os.chmod(path_setup, 0o755)
    os.system(path_setup)

    _get_ext_filename = getattr(build_ext, 'build_ext').get_ext_filename
    get_ext_filename = lambda pkg: _get_ext_filename(None, pkg)

    lib_files = []
    for module in modules:
        if module not in pkgs:
            lib_files.append(get_ext_filename(module))

    return dict(
        lib_dir=lib_dir,
        lib_files=lib_files,
        pkg_modules=pkgs,
    )


@doc('Make Spec', 'Use for PyInstaller.')
@click.option('-n', '--name')
@click.option('-k', '--key', default=common.generate_uuid().replace('-', '')[:16])
@click.option('-F', '--onefile', is_flag=True)
@click.option('-b', '--build', is_flag=True)
@click.option('-c', '--cythonize', is_flag=True)
@click.option('-p', '--plaintext-py', is_flag=True)
@click.option('-d', '--datas', nargs=2, multiple=True)
@click.option('-h', '--hiddenimports', multiple=True)
@click.option('-P', '--collect-py-module', multiple=True)
@click.option('-D', '--collect-data', multiple=True)
@click.option('-B', '--collect-binaries', multiple=True)
@click.option('-S', '--collect-submodules', multiple=True)
@click.option('-A', '--collect-all', multiple=True)
@click.argument('main')
def make(main: str, build: bool, cythonize: bool, collect_py_module: tuple, **opts):
    app_modules = Environ.app.sub_modules
    ext_modules = Environ.app.ext_modules + [
        'logging.config', 'gunicorn.glogging',
    ]
    all_modules = app_modules + ext_modules
    root_modules = [i for i in all_modules if '.' not in i]

    opts['collect_data'] = list(opts.get('collect_data', ())) + root_modules

    datas = opts['datas'] = list(opts.get('datas', ()))
    hidden_imports = opts['hiddenimports'] = list(opts.get('hiddenimports', ()))

    if cythonize:
        try:
            from Cython.Build import cythonize
        except ImportError:
            raise Exception('You should install Cython first.')

        lib_info = build_lib_modules(app_modules)
        lib_dir = lib_info['lib_dir']
        lib_files = lib_info['lib_files']
        for lib_file in lib_files:
            lib_path = os.path.join(lib_dir, lib_file)
            datas.append((
                lib_path, os.path.dirname(lib_file)
            ))

        hidden_imports += ext_modules + lib_info['pkg_modules']
    else:
        hidden_imports += all_modules

    def add_module_data(module: Any, rel_path):
        datas.append((
            os.path.join(module.__path__[0], rel_path),
            os.path.join(module.__package__, os.path.dirname(rel_path)),
        ))

    def collect_module_py(module):
        module_name = module.__name__
        module_dir = os.path.dirname(module.__file__)

        sub_modules = common.walk_modules(module)
        sub_files = common.walk_files(module_dir, lambda d, f, p: f.endswith('.py'))
        sub_files = [f.replace(
            module_dir, module_name
        ).replace('/__init__', '').replace('.py', '').replace('/', '.') for f in sub_files]

        py_files = list(set(sub_files) - set(sub_modules))
        py_files = ['%s.py' % file.replace('.', '/').replace('%s/' % module_name, '', 1) for file in py_files]

        for py_file in py_files:
            add_module_data(module, py_file)

    collect_py_module = [*collect_py_module, 'flask_migrate']
    for name in collect_py_module:
        collect_module_py(importlib.import_module(name))

    opts.setdefault('copy_metadata', [])
    opts.setdefault('recursive_copy_metadata', [])
    if opts.get('plaintext_py'):
        opts.pop('key')

    try:
        from PyInstaller.building import makespec, build_main
    except ImportError:
        raise Exception('You should install PyInstaller first.')

    path_spec = makespec.main([main], **opts)

    if build:
        opts_build = {}
        dist_path = './dist'
        shutil.rmtree(dist_path, True)
        opts_build.setdefault('distpath', dist_path)
        opts_build.setdefault('workpath', './build')
        build_main.main(None, path_spec, True, **opts_build)
