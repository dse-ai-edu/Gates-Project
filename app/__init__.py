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
database = mongo_client['auto_feedback'] 

# s3_client = boto3.client(
#     's3',
#     region_name='us-east-2',
#     aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
#     aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
# )

from app import routes
# from app import files