import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'JustTest')
    MONGODB_URI = os.getenv('MONGODB_URI')

    MODE = 'online'

    OPENAI_API_KEY1 = os.getenv('OPENAI_API_KEY1')
    OPENAI_API_KEY2 = os.getenv('OPENAI_API_KEY2')
    OPENAI_API_KEY3 = os.getenv('OPENAI_API_KEY3')