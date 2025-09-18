import os
import platform
from rq import Worker, SimpleWorker
from redis import Redis
from app.config import settings

redis_conn = Redis.from_url(settings.redis_url)

listen = ["gemini"]


def build_worker():
    """
    On macOS, RQ's default Worker uses fork() which can crash with
    Objective-C libs. Prefer SimpleWorker (no forking).
    You can force SimpleWorker anywhere via USE_SIMPLE_WORKER=1.
    """
    force_simple = os.getenv("USE_SIMPLE_WORKER", "").strip() == "1"
    is_macos = platform.system() == "Darwin"

    if force_simple or is_macos:
        return SimpleWorker(listen, connection=redis_conn)

    return Worker(listen, connection=redis_conn)


if __name__ == "__main__":
    worker = build_worker()
    worker.work()
