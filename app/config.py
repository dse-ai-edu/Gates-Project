import os

from pathlib import Path

import app.utils as utils


BASE_DIR = Path(__file__).resolve().parent

TMP_DIR = BASE_DIR / "tmp"

TMP_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


DEFAULT_MODEL = os.environ.get(
    "DEFAULT_MODEL",
    "gemini-3.1-flash-lite-preview",
)


log_prob_text = os.environ.get(
    "HAVE_LOGPROB",
    "0",
)

HAVE_LOGPROB = any(
    pos_k in str(log_prob_text).lower()
    for pos_k in [
        "yes",
        "true",
        "1",
    ]
)


app_dir = utils.find_app_dir()

KEYWORD_PATH = (
    app_dir
    / "static"
    / "data"
    / "keyword_info.json"
)

EXAMPLE_PATH = (
    app_dir
    / "static"
    / "data"
    / "feedback_example.json"
)

PATTERN_PATH = (
    app_dir
    / "static"
    / "data"
    / "pattern_info.json"
)


class Config:

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "JustTest",
    )

    MONGODB_URI = os.getenv(
        "MONGODB_URI"
    )

    MODE = "online"

    OPENAI_API_KEY1 = os.getenv(
        "OPENAI_API_KEY1"
    )

    OPENAI_API_KEY2 = os.getenv(
        "OPENAI_API_KEY2"
    )

    OPENAI_API_KEY3 = os.getenv(
        "OPENAI_API_KEY3"
    )

    MAX_CONTENT_LENGTH = (
        10 * 1000 * 1000
    )