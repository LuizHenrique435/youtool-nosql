from pymongo import MongoClient
from conf import MONGO_URI, DB_NAME

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def save_video_data(video_id, data):
    db['youtube_data'].replace_one(
        {"video_id": video_id},
        data,
        upsert=True
    )
