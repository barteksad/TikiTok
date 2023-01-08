import src.db as db

from typing import Union
import numpy as np

import firebase_admin
from firebase_admin import auth

from fastapi import FastAPI, Response, Header
from fastapi.middleware.cors import CORSMiddleware
import logging

from dotenv import load_dotenv
import os

load_dotenv()

LIKE_CLASS_FACTOR = float(os.environ['LIKE_CLASS_FACTOR'])
N_CLASSES = int(os.environ['N_CLASSES'])
# Logging
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger("requests.packages.urllib3")
logger.setLevel(logging.INFO)
logger.propagate = True

app = FastAPI()
# GOOGLE_APPLICATION_CREDENTIALS env variable must be a path to firebase admin .json file.
firebase = firebase_admin.initialize_app()

# CORS setup
origins = [os.environ["DOMAIN"]]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

postgres_conn = db.connect()
postgres_conn.autocommit = False
postgres = postgres_conn.cursor()

def check_id_token(token: str):
    token = token.removeprefix("Bearer ")
    return auth.verify_id_token(token)

@app.get("/get_likes/{video_id}")
def handle_get_likes(
    response: Response,
    video_id: str,
    authorization: Union[str, None] = Header(default=None)):

    """Check if user already liked the video and get it likes count."""
    try:
        if authorization is None:
            raise Exception("No authorization header.")
        user = check_id_token(authorization)
    except Exception as error:
        logger.error(f"Cannot verify token {authorization}. Reason: {error}.")
        response.status_code = 403
        return {"message": f"Invalid ID token."}
    
    logger.info(f"Successfully authorized user {user['user_id']} {user['email']}.")
    try:
        liked = check_if_liked(video_id, user['user_id'])
        likes_count = get_likes_count(video_id)
    except Exception as error:
        logger.error(f"Cannot get likes for video {video_id}. Reason: {error}.")
        response.status_code = 500
        return {"message": f"Cannot get likes for video {video_id}."}
    return {"liked": liked, "likes_count": likes_count}

@app.post("/like_clicked/{video_id}")
def handle_post_like(
    response: Response,
    video_id: str,
    authorization: Union[str, None] = Header(default=None)):

    """Handle like click event."""
    try:
        if authorization is None:
            raise Exception("No authorization header.")
        user = check_id_token(authorization)
    except Exception as error:
        logger.error(f"Cannot verify token {authorization}. Reason: {error}.")
        response.status_code = 403
        return {"message": f"Invalid ID token."}

    logger.info(f"Successfully authorized user {user['user_id']} {user['email']}.")

    """Check if user already liked the video. If not, add like to the database. Update preference vector."""
    try:
        if not check_if_liked(video_id, user["user_id"]):
            factor = LIKE_CLASS_FACTOR
            postgres.execute("""INSERT INTO likes (video_id, user_id) VALUES (%s, %s);""", (video_id, user["user_id"]))
            logger.info(f"User {user['user_id']} liked video {video_id}.")
        else:
            factor = -LIKE_CLASS_FACTOR
            postgres.execute("""DELETE FROM likes WHERE video_id = %s AND user_id = %s;""", (video_id, user["user_id"]))
            logger.info(f"User {user['user_id']} unliked video {video_id}.")
        logger.info(f"Successfully clicked like video {video_id} by user {user['user_id']}. Factor: {factor}.")

        """Get user's preference vector and video class"""
        postgres.execute("""SELECT class1, class2, class3 FROM video WHERE id = %s;""", (video_id,))
        maybe_video = postgres.fetchone()
        if maybe_video is None:
            raise Exception("Video not found.")
        else:
            classes = maybe_video
        logger.info(f"Video {video_id} has classes {classes}.")

        postgres.execute("""SELECT vector FROM preferences WHERE user_id = %s;""", (user["user_id"],))
        maybe_vector = postgres.fetchone()
        if maybe_vector is None:
            logger.info(f"User {user['user_id']} has no vector. Creating new one.")
            existed = False
            vector = np.zeros(N_CLASSES, dtype=np.float32)
        else:
            existed = True
            (vector,) = maybe_vector
            vector = np.array(vector, dtype=np.float32)

        like_classes_vector = np.zeros(N_CLASSES, dtype=np.float32)
        like_classes_vector[list(classes)] = 1.
        vector =  vector * (1. - LIKE_CLASS_FACTOR) + factor * like_classes_vector
        if existed:
            postgres.execute("""UPDATE preferences SET vector = %s WHERE user_id = %s;""", (list(map(float, vector)), user["user_id"]))
        else:
            postgres.execute("""INSERT INTO preferences (user_id, vector) VALUES (%s, %s);""", (user["user_id"], list(map(float, vector))))
        postgres_conn.commit()
    except Exception as error:
        logger.error(f"Error processing like. Reason: {error}.")
        response.status_code = 500
        return {"message": f"Internal server error."}

def check_if_liked(video_id: str, user_id: str) -> bool:
    postgres.execute(r'SELECT COUNT(1) FROM likes WHERE video_id = %s AND user_id = %s;', (video_id, user_id))
    return postgres.fetchone() == (1,)

def get_likes_count(video_id: str) -> int:
    postgres.execute(r'SELECT COUNT(1) FROM likes WHERE video_id = %s;', (video_id,))
    if (count := postgres.fetchone()) is None:
        raise Exception("Video not found.")
    else:
        return count[0]