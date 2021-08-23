import os
import sys

worker = None
fork_killer = True

try:
    from geventwebsocket.gunicorn.workers import GeventWebSocketWorker
    from gunicorn.workers.base_async import AsyncWorker


    class SaikaWorker(GeventWebSocketWorker):
        def notify(self):
            AsyncWorker.notify(self)
            if fork_killer:
                # Fix fork child process from self.
                ppid = os.getppid()
                if ppid not in [self.ppid, self.pid]:
                    self.log.info("Parent changed, shutting down: %s", self)
                    sys.exit(0)


    worker = SaikaWorker
except ImportError:
    pass


def gevent_patch():
    try:
        from gevent import monkey

        monkey.patch_all()
    except ImportError:
        pass


def set_fork_killer(enable=True):
    """Attention: Must exit fork process..."""
    global fork_killer
    fork_killer = enable
