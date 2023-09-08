import multiprocessing
import os

import uvicorn

from background_tasks import polling_queue

if __name__ == "__main__":
    process = multiprocessing.Process(
        target=polling_queue, args=(int(os.getenv("POLLING_TIMEOUT", 60)),)
    )
    process.start()

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
