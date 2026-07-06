import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'JustTest')
    MONGODB_URI = os.getenv('MONGODB_URI')

    MODE = 'online'

    OPENAI_API_KEY1 = os.getenv('OPENAI_API_KEY1')
    OPENAI_API_KEY2 = os.getenv('OPENAI_API_KEY2')
    OPENAI_API_KEY3 = os.getenv('OPENAI_API_KEY3')

    # Gemini models used across the app. GOOGLE_API_KEY is a single key
    # (no rotation, unlike the OpenAI keys above).
    # - HIGH: response/feedback text generation
    # - LOW: grading and post-processing
    # - VISION: image/PDF-to-text recognition
    GEMINI_MODEL_HIGH = os.getenv('GEMINI_MODEL_HIGH', 'gemini-3-flash-preview')
    GEMINI_MODEL_LOW = os.getenv('GEMINI_MODEL_LOW', GEMINI_MODEL_HIGH)
    GEMINI_MODEL_VISION = os.getenv('GEMINI_MODEL_VISION', GEMINI_MODEL_HIGH)
    MAX_CONTENT_LENGTH = 10 * 1000 * 1000  # 10 MB