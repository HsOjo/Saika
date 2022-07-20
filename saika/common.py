import base64
import json
import os
import pkgutil
import re
import uuid

from itsdangerous import TimedJSONWebSignatureSerializer

from .environ import Environ


def obj_encrypt(obj, expires_in=None):
    return TimedJSONWebSignatureSerializer(Environ.app.secret_key, expires_in).dumps(obj).decode()


def obj_decrypt(obj_str):
    try:
        return TimedJSONWebSignatureSerializer(Environ.app.secret_key).loads(obj_str)
    except:
        return None


def obj_standard(obj, str_key=False, str_obj=False, str_type=False):
    kwargs = locals().copy()
    kwargs.pop('obj')

    this = lambda x: obj_standard(x, **kwargs)
    if type(obj) in [bool, int, float, str, type(None)]:
        return obj
    elif isinstance(obj, bytes):
        return base64.b64encode(obj).decode()
    elif isinstance(obj, list) or isinstance(obj, tuple):
        return [this(i) for i in obj]
    elif isinstance(obj, dict):
        return {str(k) if str_key else this(k): this(v) for k, v in obj.items()}
    elif isinstance(obj, type) and str_type:
        return obj.__name__
    else:
        return str(obj) if str_obj else obj


def rule_to_rest(rule_str):
    path = rule_str  # type: str
    args = {}
    args_match = re.findall('(<(.+?):(.+?)>)', rule_str)
    for [match, type_, key] in args_match:
        path = path.replace(match, ':%s' % key)
        args[key] = dict(type=type_)

    return path, args


def list_group_by(x):
    buffer = set()
    result = []
    for i in x:
        if i not in buffer:
            buffer.add(i)
            result.append(i)
    return result


def generate_uuid():
    return str(uuid.uuid4())


def to_json(obj, **kwargs):
    kwargs.setdefault('ensure_ascii', False)
    return json.dumps(obj, **kwargs)


def from_json(obj_str, **kwargs):
    return json.loads(obj_str, **kwargs)


def get_lower_name(name):
    return re.sub('[A-Z]', lambda x: '_' + x.group().lower(), name).lstrip('_')


def walk_modules(module, prefix=None, module_dir=None, include_self=True, to_dict=False):
    result = []

    if module is not None:
        module_name = module.__name__
        if include_self:
            if to_dict:
                result.append(dict(
                    endpoint=module_name,
                    is_pkg='__init__' in os.path.basename(module.__file__),
                ))
            else:
                result.append(module_name)
        if prefix is None:
            prefix = module_name

        if module_dir is None:
            # Walk package only.
            if not getattr(module, '__file__', None) or '__init__' not in os.path.basename(module.__file__):
                return result
            module_dir = os.path.dirname(module.__file__)
    elif prefix is None or module_dir is None:
        raise Exception('Must provide prefix and module_dir.')

    for module_info in pkgutil.iter_modules([module_dir]):
        module_info: pkgutil.ModuleInfo
        module_endpoint = '%s.%s' % (prefix, module_info.name)
        if to_dict:
            result.append(dict(
                endpoint=module_endpoint,
                is_pkg=module_info.ispkg,
            ))
        else:
            result.append(module_endpoint)
        if module_info.ispkg:
            result += walk_modules(
                module=None,
                prefix=module_endpoint,
                module_dir=os.path.join(module_dir, module_info.name),
                to_dict=to_dict,
            )

    return result


def walk_files(dir_, *filters):
    result = []
    for d, ds, fs in os.walk(dir_):
        for f in fs:
            p = os.path.join(d, f)
            if filters:
                drop = False
                for filter_ in filters:
                    if not filter_(d, f, p):
                        drop = True
                        break
                if drop:
                    continue
            result.append(p)

    return result
