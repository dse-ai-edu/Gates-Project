import os

# def split_openai_api_keys():
#     raw = os.getenv("OPENAI_API_KEYS")
#     if not raw:
#         return []
#     keys = [k.strip() for k in raw.replace("\n", ",").split(",") if k.strip()]
#     for i, key in enumerate(keys, 1):
#         os.environ[f"OPENAI_API_KEY{i}"] = key
#     return keys


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'JustTest')
    MONGODB_URI = os.getenv('MONGODB_URI')

    MODE = 'online'
    
    # OPENAI_API_KEYS = split_openai_api_keys()

    MAX_CONTENT_LENGTH = 10 * 1000 * 1000  # 10 MB