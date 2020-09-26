import os
from concurrent.futures.thread import ThreadPoolExecutor

PROCESSING_THREAD_POOL = ThreadPoolExecutor(max_workers=((os.cpu_count() / 2) or 4))

QUERYING_THREAD_POOL = ThreadPoolExecutor(max_workers=(os.cpu_count() or 4))
