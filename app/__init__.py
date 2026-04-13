import os
import itertools
from flask import Flask
from app.config import Config
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# init Flask
app = Flask(__name__)
app.config.from_object(Config)

# ========= API KEY =========
# API_KEYS = app.config.get("OPENAI_API_KEYS", [])
# key_iter_obj = itertools.cycle(API_KEYS) if API_KEYS else None

# def key_iter():
#     if not key_iter_obj:
#         raise RuntimeError("No OPENAI API keys configured")
#     return next(key_iter_obj)

# ========= READ API KEY =========
for key, value in os.environ.items():
    if "API_KEY" in key:
        print(f"{key}: {str(value)[:5]} ... {str(value)[-5:]}")
        
# ========= MongoDB =========
mongo_client = MongoClient(app.config.get('MONGODB_URI'))
print("Link to MongoDB successful.")

database = mongo_client['auto_feedback']
print("Link to MongoDB database successful.")

# collection 
if "assets" not in database.list_collection_names():
    database.create_collection("assets")
print("Check collection `assets` successful.")

indexes = database["assets"].index_information()
if "sha256_1" not in indexes:
    database["assets"].create_index(
        "sha256",
        unique=True,
        partialFilterExpression={"sha256": {"$exists": True}},
    )
print("Check index sha256 successful.")

