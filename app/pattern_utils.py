import json

from typing import Union, List

from app.utils import (
    find_app_dir,
    best_match_by_lcs,
)

from app.llm_utils import llm_generate

from app.text_prompts import (
    MACRO_TRAIT_BASE,
    MACRO_TEMPLATE_BASE,
    FEEDBACK_BASE,
    FEEDBACK_INPUT_BASE,
    FEEDBACK_OUTPUT_INSTRUCTION,
    TEACHING_TEXT_SUFFIX,
)


# =========================

def load_default_keywords(grouped_keywords):

    subgroup_identifier_list = [
        int(identifier)
        for identifier in grouped_keywords.keys()
    ]

    subgroup_identifier_list = sorted(
        subgroup_identifier_list
    )

    result = [
        grouped_keywords[subgroup_identifier][0]["key"]
        for subgroup_identifier
        in subgroup_identifier_list
    ]

    return result

# =========================

def load_keywords_by_subgroup(keyword_path):
    with open(keyword_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    grouped = {}
    for kw, info in raw.items():
        
        subgroup = info.get("subgroup")
        if subgroup is None:
            continue
        
        group_idx = info.get("group_idx", 0)
        item_dict = {
            "key": kw,
            "name": info.get("name", kw),
            "group_idx": group_idx,
            "short": info.get("short", "")
            }
        
        if group_idx == 1:
            item_dict['subgroup_name'] = info.get("subgroup_name", f"Keyword {subgroup}")
            item_dict['subgroup_info'] = info.get("subgroup_info", f"List of Keywords of Group {subgroup}")
            
        grouped.setdefault(int(subgroup), []).append(item_dict)
        
    for subgroup, items in grouped.items():
        items.sort(key=lambda x: int(x["group_idx"]))
    return grouped

# =========================

def return_keyword_combination_example(
    keywords_str,
    default_keywords,
    example_path,
):

    with open(
        example_path,
        "r",
        encoding="utf-8",
    ) as f:

        example_data = json.load(f)

    keywords_str = keywords_str.strip("+")

    custom_keywords = keywords_str.split("+")

    default_keywords_str = "+".join(
        default_keywords
    )

    keywords_list = []

    for custom_kw, default_kw in zip(
        custom_keywords[:len(default_keywords)],
        default_keywords,
    ):

        if (
            custom_kw
            and str(custom_kw).strip() != ""
        ):

            keywords_list.append(custom_kw)

        else:

            keywords_list.append(default_kw)

    clean_keywords_str = "+".join(
        keywords_list
    )

    feedback = example_data.get(
        clean_keywords_str,
        example_data[default_keywords_str],
    )

    return {
        "question": example_data["question"],
        "answer": example_data["answer"],
        "feedback": feedback,
    }


# =========================
# Response Generation
# =========================

def format_keyword_block(
    keyword: str,
    info: dict,
) -> str:

    keyword_name = info.get(
        "name",
        keyword,
    ).strip()

    short_summary = info.get(
        "short",
        "N/A",
    ).strip()

    keyword_group = info.get(
        "subgroup_name",
        "Keyword",
    ).strip()

    subgroup_info = info.get(
        "subgroup_info",
        "",
    ).strip()

    good_examples = info.get(
        "good_examples",
        "N/A",
    ).strip()

    bad_examples = info.get(
        "bad_examples",
        "N/A",
    ).strip()

    subgroup_text = ""

    if subgroup_info:

        subgroup_text = (
            f" -- Subgroup Information "
            f"(with Opposite Traits to Avoid): "
            f"{subgroup_info} \n"
        )

    return (
        f" - TRAIT KEYWORD: "
        f"{keyword_name} \n"

        f" -- Introduction to "
        f"{keyword_name.upper()}: "
        f"{short_summary} \n"

        f" -- TRAIT TYPE: "
        f"{keyword_group} \n"

        f"{subgroup_text}"

        f" -- EXAMPLES aligning with "
        f"{keyword_name.upper()} Trait: "
        f"{good_examples} \n"

        f" -- EXAMPLES failing on "
        f"{keyword_name.upper()} Trait: "
        f"{bad_examples} \n\n"
    )


# =========================
# Find Adaptive Pattern
# =========================

def decide_adaptive_pattern(
    question,
    answer,
    model,
):

    app_dir = find_app_dir()

    json_path = (
        app_dir
        / "static"
        / "data"
        / "pattern_info.json"
    )

    with open(
        json_path,
        "r",
        encoding="utf-8",
    ) as f:

        pattern_info = json.load(f)

    adaptive_pattern_dict = (
        pattern_info["Adaptive"]
    )

    pattern_options = [
        pattern
        for pattern in pattern_info.keys()
        if pattern.lower()
        not in [
            "rubric",
            "plain",
            "adaptive",
        ]
    ]

    from app.text_prompts import (
        ADAPTIVE_PREFIX,
        ADAPTIVE_SUFFIX,
    )

    qa_query = (
        f"# Question: {question}; "
        f"# Studeng Answer: {answer}; \n"
    )

    system_prompt = (
        f"{ADAPTIVE_PREFIX.format(pattern_options=pattern_options)}\n"
        f"{str(adaptive_pattern_dict)}\n"
        f"{ADAPTIVE_SUFFIX.format(pattern_options=pattern_options)}"
    )

    response = llm_generate(
        user_prompt=qa_query,
        system_prompt=system_prompt,
        model=model,
        max_retry=5,
    )

    if response.text is None:

        raise ValueError(
            "Empty adaptive pattern response."
        )

    select_pattern_text = response.text

    matched_pattern_key = best_match_by_lcs(
        select_pattern_text,
        pattern_info.keys(),
    )

    if (
        matched_pattern_key.lower()
        not in pattern_options
    ):

        matched_pattern_key = "conceptual"

    return matched_pattern_key.capitalize()


# =========================
# Parse Feedback Pattern
# =========================

def parse_feedback_pattern(
    feedback_pattern: str = None,
    custom_rubric: str = None,
    model: str = "gemini-3.1-flash-lite-preview",
    from_adaptive: bool = False,
    **kwarg,
) -> str:

    app_dir = find_app_dir()

    json_path = (
        app_dir
        / "static"
        / "data"
        / "pattern_info.json"
    )

    with open(
        json_path,
        "r",
        encoding="utf-8",
    ) as f:

        pattern_info = json.load(f)

    pattern_input_lower = (
        feedback_pattern.lower().strip()
    )

    default_pattern_key, default_pattern = (
        next(iter(pattern_info.items()))
    )

    pattern_body = None

    case_num = 0

    if from_adaptive:

        case_num = -1

        matched_pattern_key = (
            best_match_by_lcs(
                pattern_input_lower,
                pattern_info.keys(),
            )
        )

        pattern_body = pattern_info.get(
            matched_pattern_key.capitalize(),
            {},
        )

        focus_selection_rule = (
            pattern_info["Adaptive"]
            ["focus_selection_rule"]
            .get(
                matched_pattern_key.lower(),
                "",
            )
        )

        pattern_body[
            "primary_content_focus"
        ] = (
            f"{focus_selection_rule} \n "
            f"{pattern_body['primary_content_focus']}"
        )

        pattern_body[
            "feedback_scope_rule"
        ] = (
            pattern_info["Adaptive"]
            ["feedback_scope_rule"]
        )

        pattern_body["exclusions"] = (
            f"{pattern_info['Adaptive']['exclusions']} \n "
            f"{pattern_body['exclusions']}"
        )

    if (
        len(pattern_input_lower) > 0
        and "custom"
        not in pattern_input_lower
    ):

        case_num = 1

        matched_pattern_key = (
            best_match_by_lcs(
                pattern_input_lower,
                pattern_info.keys(),
            )
        )

        pattern_body = pattern_info.get(
            matched_pattern_key
        )

    elif str(custom_rubric).strip() == "0":

        case_num = 3

        matched_pattern_key = "Plain"

        pattern_body = pattern_info.get(
            matched_pattern_key
        )

    else:

        case_num = 2

        matched_pattern_key = "Custom"

        customize_prompt = pattern_info.get(
            "Rubric"
        )

        system_prompt = str(customize_prompt)

        user_prompt = (
            f"User Rubric: {custom_rubric}"
        )

        print(
            f"*** debug: generate pattern "
            f"user_prompt: `{user_prompt}`"
        )

        print(
            f"*** debug: generate pattern "
            f"system_prompt: `{system_prompt}`"
        )

        response = llm_generate(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            model=model,
            max_retry=5,
        )

        pattern_body = response.text

        if pattern_body is None:

            matched_pattern_key = (
                "Custom (override by Plain)"
            )

            pattern_body = pattern_info.get(
                "Plain"
            )

    print(
        f"[PATTERN] Pattern Case Above: "
        f"{case_num}: "
        f"`{matched_pattern_key}` "
        f"from `{feedback_pattern}`"
    )

    return {
        "pattern_key": matched_pattern_key,
        "pattern_body": pattern_body,
    }


# =========================
# Parse Teaching Text
# =========================

def parse_teaching_text(
    question: str,
    answer: str,
    style_keywords: Union[str, List[str]],
    feedback_templates: str = "",
) -> str:

    app_dir = find_app_dir()

    data_dir = (
        app_dir
        / "static"
        / "data"
    )

    keyword_info_path = (
        data_dir
        / "keyword_info.json"
    )

    try:

        with open(
            keyword_info_path,
            "r",
            encoding="utf-8",
        ) as f:

            keyword_info = json.load(f)

    except Exception:

        keyword_info = dict()

    if isinstance(style_keywords, str):

        keywords = [
            k.strip()
            for k in style_keywords.split(",")
            if k.strip()
        ]

    elif isinstance(
        style_keywords,
        (list, tuple),
    ):

        keywords = [
            str(k).strip()
            for k in style_keywords
            if str(k).strip()
        ]

    else:

        keywords = []

    keyword_full_text = ""

    for kw_idx, kw in enumerate(keywords):

        matched_kw = best_match_by_lcs(
            kw,
            keywords,
        )

        info = keyword_info.get(
            matched_kw,
            None,
        )

        if info is not None:

            kw_text_this = (
                format_keyword_block(
                    matched_kw,
                    info,
                )
            )

            keyword_full_text += (
                f"### TRAIT KEYWORD "
                f"{kw_idx+1}: \n "
                f"{kw_text_this}"
            )

    macro_trait_prompt = (
        MACRO_TRAIT_BASE.format(
            keyword_full_text
        )
    )

    if not feedback_templates:

        feedback_templates = (
            "- Stength, "
            "- Weakness, "
            "- Improvement."
        )

    macro_template_prompt = (
        MACRO_TEMPLATE_BASE.format(
            feedback_templates
        )
    )

    final_respond_prompt = macro_trait_prompt

    final_respond_prompt += FEEDBACK_BASE

    final_respond_prompt += (
        FEEDBACK_INPUT_BASE.format(
            question=question,
            answer=answer,
        )
    )

    final_respond_prompt += (
        macro_template_prompt
    )

    final_respond_prompt += (
        FEEDBACK_OUTPUT_INSTRUCTION
    )

    final_respond_prompt += (
        "[PLACEHOLDER]\n"
    )

    final_respond_prompt += (
        TEACHING_TEXT_SUFFIX
    )

    return final_respond_prompt




def load_pattern_items(pattern_path):
    with open(pattern_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # 1. filter: only show_on_page > 0
    items = []
    for key, info in raw.items():
        show = info.get("show_on_page", -1)
        if show > 0:
            items.append({
                "key": key,
                "name": info.get("name", key),
                "short": info.get("short", ""),
                "show_on_page": show,
                "default_select": info.get("default_select", None),
                "need_additional_info": info.get("need_additional_info", 0)
            })

    # 2. sort by show_on_page
    items.sort(key=lambda x: x["show_on_page"])

    # 3. determine default
    default_candidates = [x for x in items if x["default_select"] is not None]

    if default_candidates:
        default_key = max(default_candidates, key=lambda x: x["default_select"])["key"]
    else:
        default_key = min(items, key=lambda x: x["show_on_page"])["key"]

    return items, default_key
