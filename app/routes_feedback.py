import json
import re
import uuid
import traceback

from datetime import datetime

from flask import (
    request,
    jsonify,
    Blueprint
)

bp_feedback = Blueprint(
    "bp_feedback",
    __name__,
)

from app import (
    database,
)

from app.config import (
    DEFAULT_MODEL,
    HAVE_LOGPROB,
    KEYWORD_PATH,
)

from app.text_prompts import (
    JUDGE,
)

from app.llm_utils import (
    llm_generate,
)

from app.utils import (
    format_response_html,
)

from app.judge import (
    multi_agent_judge,
    run_score_extract,
    is_consistent,
)

from app.feedback_post_process_utils import (
    run_feedback_post_process_llm,
)

from app.pattern_utils import (
    decide_adaptive_pattern,
    parse_feedback_pattern,
    parse_teaching_text
)


# default data
with open(KEYWORD_PATH, "r") as f:
    KEYWORD_INFO = json.load(f)

# ====================
# QA Demo
# ====================

@bp_feedback.route(
    "/api/demo/calculus",
    methods=["POST"],
)
def catch_demo_answer():

    data = request.get_json()

    q_index = (
        data.get("question_index")
        if data else None
    )

    if q_index is None:

        return jsonify({
            "success": False,
            "error": "Missing question_index",
        }), 400

    with open(
        "app/static/data/calculus_qa_example.json",
        "r",
    ) as f:

        demo_data = json.load(f)

    q_index_str = (
        f"q{int(q_index) + 1}"
    )

    demo_data_this = demo_data.get(
        q_index_str
    )

    if not demo_data_this:

        return jsonify({
            "success": False,
            "answer_code_list": [],
            "answer_img_list": [],
            "error":
            f"Question {q_index_str} "
            f"not found",
        })

    answer_code_list = [
        demo_data_this[f"a{a_idx}"]
        ["answer_code"]
        for a_idx in range(1, 6)
    ]

    answer_img_list = [
        demo_data_this[f"a{a_idx}"]
        ["image"]
        for a_idx in range(1, 6)
    ]

    response = {
        "success": True,
        "answer_code_list":
        answer_code_list,
        "answer_img_list":
        answer_img_list,
        "question_code":
        demo_data_this["content"],
    }

    return jsonify(response)


# ====================
# Update Style Config
# ====================

@bp_feedback.route(
    "/api/comment/update_style",
    methods=["POST"],
)
def update_style_config():

    data = request.get_json()

    tid = data.get("tid")

    try:

        if not tid:

            raise ValueError(
                "Missing required field: tid"
            )

        config_data = {
            "style_keywords":
            data.get(
                "style_keywords",
                [],
            ),

            "feedback_templates":
            data.get(
                "feedback_templates",
                [],
            ),

            "feedback_pattern":
            data.get(
                "feedback_pattern",
                "",
            ),

            "custom_rubric":
            data.get(
                "custom_rubric",
                "",
            ),
        }

        existing_record = (
            database["comment_config"]
            .find_one({"tid": tid})
        )

        if existing_record:

            current_config_list = (
                existing_record.get(
                    "config",
                    [],
                )
            )

            current_config_list.append(
                config_data
            )

            database["comment_config"]\
            .find_one_and_update(
                {"tid": tid},
                {
                    "$set": {
                        "config":
                        current_config_list,

                        "updated_at":
                        datetime.utcnow(),
                    }
                }
            )

        else:

            new_record = {
                "tid": tid,
                "config":
                [config_data],

                "created_at":
                datetime.utcnow(),

                "updated_at":
                datetime.utcnow(),
            }

            database["comment_config"]\
            .insert_one(new_record)

        response = {
            "success": True,
        }

    except Exception as e:

        traceback.print_exc()

        response = {
            "success": False,
            "error": str(e),
        }

    return jsonify(response)


# ====================
# Retrieve Style Config
# ====================

@bp_feedback.route(
    "/api/comment/retrieve_style",
    methods=["POST"],
)
def retrieve_style_config():

    data = request.get_json()

    tid = data.get("tid")

    try:

        if not tid:

            raise ValueError(
                "Missing required field: tid"
            )

        existing_record = (
            database["comment_config"]
            .find_one({"tid": tid})
        )

        if existing_record:

            config_list = (
                existing_record.get(
                    "config",
                    [],
                )
            )

            if (
                config_list
                and len(config_list) > 0
            ):

                last_config = (
                    config_list[-1]
                )

                response = {
                    "success": True,
                    "config": last_config,
                    "message":
                    f"Retrieved "
                    f"{len(config_list)} "
                    f"configurations",
                }

            else:

                response = {
                    "success": False,
                    "error":
                    "No configurations found",
                }

        else:

            response = {
                "success": False,
                "error":
                f"No record found "
                f"for tid: {tid}",
            }

    except Exception as e:

        traceback.print_exc()

        response = {
            "success": False,
            "error": str(e),
        }

    return jsonify(response)


# ====================
# Feedback Generation
# ====================

def comment_generate(
    system_info,
    answer_text,
    question_text,
    reference_text,
    history_prompt_dict,
    predefined_flag="",
    suggestion=None,
):

    try:

        style_keywords = (
            system_info.get(
                "style_keywords",
                [],
            )
        )

        feedback_templates = (
            system_info.get(
                "feedback_templates",
                [],
            )
        )

        feedback_pattern = (
            system_info.get(
                "feedback_pattern",
                "",
            )
        )

        custom_rubric = (
            system_info.get(
                "custom_rubric",
                "",
            )
        )

        if suggestion is not None:

            grading_suggestion = (
                suggestion.get("grading")
            )

            feedback_suggestion = (
                suggestion.get("feedback")
            )

        else:

            grading_suggestion = None

            feedback_suggestion = None

        judge_input_text = (
            f"# Question:\n"
            f"{question_text}\n\n"

            f"# Assessment Rubric:\n"
            f"{reference_text}\n\n"

            f"# Student Answer:\n"
            f"{answer_text}\n\n"
        )

        if (
            grading_suggestion
            and str(grading_suggestion).strip()
        ):

            judge_input_text += (
                "\n\n# Grading Suggestion "
                "from Human Expert:\n"
                f"{grading_suggestion}"
            )

        grading_result = (
            multi_agent_judge(
                base_prompt=judge_input_text,
                system_prompt=JUDGE,
            )
        )

        if grading_result["pass"] is False:

            return {
                "success": True,
                "feedback_text":
                "We can not process this "
                "answer. Please involve "
                "human experts.",
                "feedback_prob": None,
                "style_keywords":
                style_keywords,
                "feedback_templates":
                feedback_templates,
                "feedback_pattern":
                feedback_pattern,
                "custom_rubric":
                custom_rubric,
                "grade_success": True,
                "grade": None,
                "grade_history":
                grading_result.get(
                    "dialogue_history",
                    [],
                ),
            }

        full_score = run_score_extract(
            user_prompt=(
                f"# Grading Rubric:\n"
                f"```\n"
                f"{reference_text}\n"
                f"```"
            )
        )

        if is_consistent(
            full_score,
            grading_result["score"],
            0.25,
        ):

            return {
                "success": True,
                "feedback_text":
                "Congratulations! "
                "The answer fully meets "
                "the requirements.",
                "feedback_prob": None,
                "style_keywords":
                style_keywords,
                "feedback_templates":
                feedback_templates,
                "feedback_pattern":
                feedback_pattern,
                "custom_rubric":
                custom_rubric,
                "grade_success": True,
                "grade":
                grading_result["score"],
                "grade_history":
                grading_result.get(
                    "dialogue_history",
                    [],
                ),
            }

        if (
            "adaptive"
            in feedback_pattern.lower()
        ):

            selected_pattern_key = (
                decide_adaptive_pattern(
                    question=question_text,
                    answer=answer_text,
                    model=DEFAULT_MODEL,
                )
            )

            from_adaptive = True

        else:

            selected_pattern_key = (
                feedback_pattern
            )

            from_adaptive = False

        pattern_dict = (
            parse_feedback_pattern(
                feedback_pattern=
                selected_pattern_key,

                custom_rubric=
                custom_rubric,

                from_adaptive=
                from_adaptive,
            )
        )

        pattern_body = (
            pattern_dict.get(
                "pattern_body",
                None,
            )
        )

        if (
            reference_text
            and len(reference_text.strip()) > 0
        ):

            question_text += (
                "\n ## Rubric: "
                + reference_text
            )

        if grading_result.get(
            "reasoning",
            None,
        ):

            question_text += (
                f"\n ## Score of this "
                f"Answer: "
                f"{grading_result.get('score')}\n"
            )

            question_text += (
                "## Reasons for Grading: "
                f"{grading_result.get('reasoning')}"
            )

        user_prompt = (
            parse_teaching_text(
                question=question_text,
                answer=answer_text.strip(),
                style_keywords=
                style_keywords,

                feedback_templates=
                feedback_templates,
            )
        )

        if (
            feedback_suggestion
            and str(feedback_suggestion).strip()
        ):

            feedback_suggestion_text = (
                "\n\n# Suggestion for "
                "Feedback Generation:\n"
                f"{feedback_suggestion}"
            )

            user_prompt = (
                user_prompt.replace(
                    "[PLACEHOLDER]",
                    feedback_suggestion_text,
                )
            )

        feedback_obj = llm_generate(
            user_prompt=user_prompt,
            system_prompt=pattern_body,
            model=DEFAULT_MODEL,
            max_tokens=2048,
            enable_logprob=HAVE_LOGPROB,
        )

        feedback_text = (
            feedback_obj.text
        )

        feedback_prob = (
            feedback_obj.logprob
        )

        score_text = re.sub(
            r"-(\d)",
            r"- \1",
            str(grading_result["score"]),
        )

        try:

            feedback_text_processed = (
                run_feedback_post_process_llm(
                    user_text=feedback_text
                )
            )

            feedback_text = (
                feedback_text_processed[
                    "text"
                ]
            )

        except Exception:

            feedback_text += "\n>"

        feedback_text += (
            f"\n\n<<< Grade: "
            f"{score_text} >>>\n\n"
        )

        return {
            "success": True,
            "feedback_text":
            feedback_text,

            "feedback_prob":
            feedback_prob,

            "style_keywords":
            style_keywords,

            "feedback_templates":
            feedback_templates,

            "feedback_pattern":
            selected_pattern_key,

            "from_adaptive":
            from_adaptive,

            "custom_rubric":
            custom_rubric,

            "pattern_body":
            pattern_body,

            "grade_success": True,

            "grade":
            grading_result["score"],

            "grade_history":
            grading_result.get(
                "dialogue_history",
                [],
            ),
        }

    except Exception as e:

        traceback.print_exc()

        return {
            "success": False,
            "error": str(e),
        }


# ====================
# Submit Feedback
# ====================

@bp_feedback.route(
    "/api/comment/submit",
    methods=["POST"],
)
def comment_submit():

    try:

        tid = request.form.get("tid")

        archive_tid = (
            request.form
            .get("archive_tid", "")
            .strip()
        )

        aid = request.form.get(
            "aid",
            str(uuid.uuid4()),
        )

        qid = request.form.get("qid")

        question_this = (
            request.form.get(
                "question",
                "",
            )
        )

        assessment_this = (
            request.form.get(
                "assessment",
                "",
            )
        )

        answer_text = (
            request.form.get(
                "answer",
                "",
            )
        )

        predefined_flag = (
            request.form.get(
                "predefined_flag",
                "",
            )
        )

        grading_suggestion = (
            request.form.get(
                "suggestion_grading"
            )
        )

        feedback_suggestion = (
            request.form.get(
                "suggestion_feedback"
            )
        )

        history_prompt_dict = None

        if archive_tid:

            history_record = (
                database["comment_config"]
                .find_one({
                    "tid": archive_tid
                })
            )

            if not history_record:

                raise ValueError(
                    f"Archive system "
                    f"not found: "
                    f"{archive_tid}"
                )

            history_system_info = (
                history_record["config"]
            )

            system_info = (
                history_system_info[-1]
                if isinstance(
                    history_system_info,
                    list,
                )
                else history_system_info
            )

        else:

            current_record = (
                database["comment_config"]
                .find_one({"tid": tid})
            )

            if not current_record:

                raise ValueError(
                    "Feedback system "
                    "not found"
                )

            current_system_info = (
                current_record["config"]
            )

            system_info = (
                current_system_info[-1]
                if isinstance(
                    current_system_info,
                    list,
                )
                else current_system_info
            )

        if not answer_text.strip():

            return jsonify({
                "success": False,
                "error":
                "Student answer "
                "cannot be empty",
            })

        generate_result = (
            comment_generate(
                system_info=system_info,
                answer_text=answer_text,
                question_text=question_this,
                reference_text=
                assessment_this,

                history_prompt_dict=
                history_prompt_dict,

                predefined_flag=
                predefined_flag,

                suggestion={
                    "grading":
                    grading_suggestion,

                    "feedback":
                    feedback_suggestion,
                },
            )
        )

        if not generate_result["success"]:

            return jsonify(
                generate_result
            )

        max_attempt_record = (
            database["comment"]
            .find_one(
                {"tid": tid},
                sort=[
                    ("attempt_id", -1)
                ],
            )
        )

        next_attempt_id = (
            max_attempt_record.get(
                "attempt_id",
                -1,
            ) + 1
            if max_attempt_record
            else 0
        )

        database["comment"].insert_one({

            "tid": tid,

            "aid": aid,

            "question": qid,

            "attempt_id":
            next_attempt_id,

            "student_answer":
            answer_text,

            "generated_response":
            generate_result[
                "feedback_text"
            ],

            "grade_history":
            generate_result[
                "grade_history"
            ],

            "system_config": {

                "style_keywords":
                generate_result[
                    "style_keywords"
                ],

                "feedback_templates":
                generate_result[
                    "feedback_templates"
                ],

                "feedback_pattern":
                generate_result[
                    "feedback_pattern"
                ],

                "feedback_pattern_from_adaptive":
                generate_result[
                    "from_adaptive"
                ],

                "custom_rubric":
                generate_result[
                    "custom_rubric"
                ],

                "pattern_body":
                generate_result[
                    "pattern_body"
                ],
            },

            "feedback_prob":
            generate_result[
                "feedback_prob"
            ],

            "generated_at":
            datetime.utcnow(),
        })

        return jsonify({
            "success": True,
            "tid": tid,
            "aid": aid,
            "attempt_id":
            next_attempt_id,
        })

    except Exception as e:

        traceback.print_exc()

        return jsonify({
            "success": False,
            "error": str(e),
        })


# ====================
# Load Feedback
# ====================

@bp_feedback.route(
    "/api/comment/load",
    methods=["GET"],
)
def comment_load():

    tid = request.args.get("tid")

    attempt_id = request.args.get(
        "attempt_id"
    )

    keyword_info = KEYWORD_INFO

    try:

        result = database["comment"]\
        .find_one({
            "tid": tid,
            "attempt_id":
            int(attempt_id),
        })

        response_text = result.get(
            "generated_response",
            "",
        )

        grade_history_body = result.get(
            "grade_history",
            None,
        )

        system_config = result.get(
            "system_config",
            dict(),
        )

        style_keywords = (
            system_config.get(
                "style_keywords",
                [],
            )
        )

        style_keywords = (
            style_keywords.split(",")
            if isinstance(
                style_keywords,
                str,
            )
            else style_keywords
        )

        style_keywords_print = [
            keyword_info.get(
                kw.strip(),
                {},
            ).get("name", "")
            for kw in style_keywords
        ]

        style_keywords_text = "; ".join(
            s.strip()
            for s
            in style_keywords_print
            if s.strip()
        )

        feedback_templates = (
            system_config.get(
                "feedback_templates",
                [],
            )
        )

        feedback_pattern = (
            system_config.get(
                "feedback_pattern",
                "",
            )
        )

        pattern_custom_flag = (
            feedback_pattern == ""
            or "custom"
            in feedback_pattern.lower()
        )

        style_pattern_text = (
            "Custom"
            if pattern_custom_flag
            else feedback_pattern
        )

        custom_rubric = (
            system_config.get(
                "custom_rubric",
                "",
            )
        )

        pattern_body = (
            system_config.get(
                "pattern_body",
                "",
            )
        )

        if response_text:

            certainty_score = result.get(
                "feedback_prob",
                "-1",
            )

            formatted_response = (
                format_response_html(
                    response_text=
                    response_text,

                    certainty_score=
                    certainty_score,
                )
            )

            return jsonify({
                "success": True,

                "response":
                formatted_response,

                "grade_history":
                grade_history_body,

                "keyword_text":
                str(style_keywords_text),

                "template_text":
                str(feedback_templates),

                "pattern_text":
                str(style_pattern_text),

                "custom_rubric":
                str(custom_rubric),

                "pattern_body":
                str(pattern_body),
            })

        return jsonify({
            "success": False,
            "response": None,
        })

    except Exception as e:

        traceback.print_exc()

        return jsonify({
            "success": False,
            "error": str(e),
        })
