import os
# import boto3
import itertools
from flask import Flask
from app.config import Config
from pymongo import MongoClient

from dotenv import load_dotenv

load_dotenv()

API_KEYS = [os.getenv('OPENAI_API_KEY1'),
            os.getenv('OPENAI_API_KEY2'),
            os.getenv('OPENAI_API_KEY3'),]

key_iter = itertools.cycle(API_KEYS)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

mongo_client = MongoClient(os.getenv('MONGODB_URI'))
print(f"Link to MongoDB successful.")
database = mongo_client['auto_feedback'] 
print(f"Link to MongoDB database successful.") 

if "assets" not in database.list_collection_names():
    database.create_collection("assets")
print(f"Link to MongoDB database `assets` successful.") 

indexes = database["assets"].index_information()
if "sha256_1" not in indexes:
    database["assets"].create_index("sha256", unique=True, partialFilterExpression={"sha256": {"$exists": True}},)
print("Check assets with unique key sha256 successful.")

# s3_client = boto3.client(
#     's3',
#     region_name='us-east-2',
#     aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
#     aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
# )

from app import routes
# from app import files