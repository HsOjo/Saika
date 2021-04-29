try:
    from geventwebsocket.gunicorn.workers import GeventWebSocketWorker

    worker = GeventWebSocketWorker
except ImportError:
    worker = None
