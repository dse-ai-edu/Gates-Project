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


@bp_main.route(
    "/api/login",
    methods=["POST"],
)
def api_login():

    try:

        data = request.get_json()

        username = data.get("username")
        password = data.get("password")

        if username and password:

            return jsonify({
                "success": True,
                "user": username,
                "token": str(uuid.uuid4()),
            })

        return jsonify({
            "success": False,
            "message": "Invalid credentials",
        })

    except Exception as e:

        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": str(e),
        })


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
    

@bp_main.route('/api/configuration/showexample', methods=['POST'])
def show_keyword_feedback_example():
    """Save final configuration and mark system as complete"""
    data = request.get_json()
    keywordLongText = data.get('keywordLongText')
    try:
        example_body = return_keyword_combination_example(keywords_str=keywordLongText, default_keywords=DEFAULT_KEYWORDS, example_path=EXAMPLE_PATH)
        example_body['success'] = True
        response = example_body
    except:
        traceback.print_exc()
        response = {'success': False}
    return jsonify(response)

