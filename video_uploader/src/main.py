from fastapi import FastAPI, Response, File
import logging

from src.bunny_cdn import create_video, upload_video_from_file
from src.db import connect

# Logging

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

app = FastAPI()

conn = connect()
conn.autocommit = True


@app.post("/upload/{title}")
def upload(response: Response, title: str, file: bytes = File()):
    resp1 = create_video(title)
    response.status_code = resp1.status_code
    if resp1.status_code != 200:
        return

    video_id = resp1.json()['guid']
    requests_log.info(f'Created a video object: \n {resp1.json()}')

    resp2 = upload_video_from_file(video_id, file)
    response.status_code = resp2.status_code
    if resp2.status_code != 200:
        return
    requests_log.info(f'Uploaded the video: \n {resp2.json()}')

    with conn.cursor() as cur:
        try:
            cur.execute(r'INSERT INTO video(id) VALUES (%s);', (video_id,))
            requests_log.info(f"Created a record for video's {video_id} metadata.")
        except Exception as error:
            requests_log.error(error)
            response.status_code = 500
