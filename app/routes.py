import traceback
import uuid

from datetime import datetime

from flask import (
    render_template,
    request,
    jsonify,
    Blueprint
)


bp_main = Blueprint(
    "bp_main",
    __name__,
)

from app import database


from app.config import (
    KEYWORD_PATH,
    EXAMPLE_PATH,
    PATTERN_PATH,
)

from app.pattern_utils import (
    return_keyword_combination_example,
    load_keywords_by_subgroup,
    load_default_keywords,
    load_pattern_items,
)


GROUPED_KEYWORDS = load_keywords_by_subgroup(
    KEYWORD_PATH
)

DEFAULT_KEYWORDS = load_default_keywords(
    GROUPED_KEYWORDS
)

PATTERN_ITEMS, DEFAULT_PATTERN = (
    load_pattern_items(PATTERN_PATH)
)


# ====================
# Page Routes
# ====================

@bp_main.route("/")
def home():
    return render_template("login.html")


@bp_main.route("/login")
def login():
    return render_template("login.html")


@bp_main.route("/page_1")
def page_1():

    return render_template(
        "page_1.html",
        subgroup1_keywords=GROUPED_KEYWORDS.get(1, []),
        subgroup2_keywords=GROUPED_KEYWORDS.get(2, []),
        subgroup3_keywords=GROUPED_KEYWORDS.get(3, []),
        subgroup4_keywords=GROUPED_KEYWORDS.get(4, []),
    )


@bp_main.route("/page_2")
def step2():

    return render_template(
        "page_2.html",
        pattern_items=PATTERN_ITEMS,
        default_pattern=DEFAULT_PATTERN,
    )


@bp_main.route("/page_final")
def page_final():
    return render_template("page_final.html")


@bp_main.route("/page_final_example")
def page_final_example():
    return render_template(
        "page_final_example.html"
    )