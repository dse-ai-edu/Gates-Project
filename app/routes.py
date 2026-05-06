import os
import json
import uuid
import traceback

from datetime import datetime
from pathlib import Path

from flask import (
    render_template,
    request,
    jsonify,
)

import app.utils as utils

from app import app, database

from app.routes_image import *
from app.routes_feedback import *

from app.pattern_utils import (
    load_keywords_by_subgroup,
    load_default_keywords,
    return_keyword_combination_example,
    load_pattern_items,
)


# ====================
# Default Parameters
# ====================

DEFAULT_MODEL = os.environ.get(
    "DEFAULT_MODEL",
    "gemini-3.1-flash-lite-preview",
)

BASE_DIR = Path(__file__).resolve().parent

TMP_DIR = BASE_DIR / "tmp"

TMP_DIR.mkdir(
    parents=True,
    exist_ok=True,
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

GROUPED_KEYWORDS = (
    load_keywords_by_subgroup(
        KEYWORD_PATH
    )
)

DEFAULT_KEYWORDS = (
    load_default_keywords(
        GROUPED_KEYWORDS
    )
)

PATTERN_ITEMS, DEFAULT_PATTERN = (
    load_pattern_items(
        PATTERN_PATH
    )
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


# ====================
# Page Routes
# ====================

@app.route("/")
def home():
    return render_template(
        "login.html"
    )


@app.route("/login")
def login():
    return render_template(
        "login.html"
    )


@app.route("/page_1")
def page_1():

    return render_template(
        "page_1.html",
        subgroup1_keywords=
        GROUPED_KEYWORDS.get(1, []),

        subgroup2_keywords=
        GROUPED_KEYWORDS.get(2, []),

        subgroup3_keywords=
        GROUPED_KEYWORDS.get(3, []),

        subgroup4_keywords=
        GROUPED_KEYWORDS.get(4, []),
    )


@app.route("/page_2")
def step2():

    return render_template(
        "page_2.html",
        pattern_items=PATTERN_ITEMS,
        default_pattern=
        DEFAULT_PATTERN,
    )


@app.route("/page_final")
def page_final():

    return render_template(
        "page_final.html"
    )


@app.route("/page_final_example")
def page_final_example():

    return render_template(
        "page_final_example.html"
    )


# ====================
# API Routes
# ====================

@app.route(
    "/api/login",
    methods=["POST"],
)
def api_login():

    data = request.get_json()

    username = data.get("username")

    password = data.get("password")

    try:

        if username and password:

            response = {
                "success": True,
                "user": username,
                "token": str(uuid.uuid4()),
            }

        else:

            response = {
                "success": False,
                "message":
                "Invalid credentials",
            }

    except Exception:

        traceback.print_exc()

        response = {
            "success": False,
            "message":
            "Authentication error",
        }

    return jsonify(response)


@app.route(
    "/api/configuration/final",
    methods=["POST"],
)
def configuration_final():

    data = request.get_json()

    tid = data.get("tid")

    try:

        database["comment_status"]\
        .find_one_and_update(
            {"tid": tid},
            {
                "$set": {
                    "completed": True,

                    "completed_at":
                    datetime.utcnow(),

                    "final_config":
                    data.get(
                        "finalConfiguration",
                        {},
                    ),
                }
            }
        )

        response = {
            "success": True
        }

    except Exception:

        traceback.print_exc()

        response = {
            "success": False
        }

    return jsonify(response)


@app.route(
    "/api/configuration/showexample",
    methods=["POST"],
)
def show_keyword_feedback_example():

    data = request.get_json()

    keyword_long_text = data.get(
        "keywordLongText"
    )

    try:

        example_body = (
            return_keyword_combination_example(
                keywords_str=
                keyword_long_text,

                default_keywords=
                DEFAULT_KEYWORDS,

                example_path=
                EXAMPLE_PATH,
            )
        )

        example_body["success"] = True

        response = example_body

    except Exception:

        traceback.print_exc()

        response = {
            "success": False
        }

    return jsonify(response)


# ====================
# Utility API Routes
# ====================

@app.route(
    "/api/session/create",
    methods=["POST"],
)
def session_create():

    try:

        session_id = str(uuid.uuid4())

        response = {
            "success": True,
            "session_id": session_id,
        }

    except Exception:

        traceback.print_exc()

        response = {
            "success": False
        }

    return jsonify(response)


@app.route(
    "/api/health",
    methods=["GET"],
)
def health_check():

    return jsonify({
        "status": "healthy",

        "timestamp":
        datetime.utcnow().isoformat(),

        "service":
        "feedback-generation-system",
    })