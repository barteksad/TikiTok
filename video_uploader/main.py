from fastapi import FastAPI, Response
import logging

from bunny_cdn import *



# Logging
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True
# Write logs to file
requests_log.addHandler(logging.FileHandler("requests.log"))

app = FastAPI()


@app.post("/upload/{title}")
def root(response: Response, title: str, file: bytes = File()):
    resp1 = create_video(title)
    response.status_code = resp1.status_code
    if resp1.status_code == 200:
        resp2 = upload_video_from_file(resp1.json()['guid'], file)
        response.status_code = resp2.status_code

    return
