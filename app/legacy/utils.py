import base64

import json
from pathlib import Path
from typing import Union, List

import os
import html
import re

from app.prompts import *
from app.pattern_prompt import *



def find_app_dir(max_depth=3):
    start = Path(__file__).resolve().parent
    cur = start
    for _ in range(max_depth + 1):
        candidate = cur / "app"
        if candidate.exists():
            return candidate.resolve()
        if cur.parent == cur:
            break
        cur = cur.parent
    for depth in range(1, max_depth + 1):
        for p in start.rglob("app"):
            try:
                if len(p.relative_to(start).parts) <= depth:
                    return p.resolve()
            except ValueError:
                continue
    return start






## Response Generation 
def format_keyword_block(keyword: str, info: dict) -> str:
    # component 1 with 4 keywords
    keyword_name = info.get("name", keyword).strip()
    short_summary = info.get("short", "N/A").strip()
    keyword_group = info.get("subgroup_name", "Keyword").strip()
    subgroup_info = info.get("subgroup_info", "").strip()
    good_examples = info.get("good_examples", "N/A").strip()
    bad_examples = info.get("bad_examples", "N/A").strip()

    return (
        f" - TRAIT KEYWORD: {keyword_name} \n"
        f" -- Introduction to {keyword_name.upper()}: {short_summary} \n"
        f" -- TRAIT TYPE: {keyword_group} \n"
        f" -- Subgroup Information (with Opposite Traits to Avoid): {subgroup_info} \n" if subgroup_info else ""
        f" -- EXAMPLES aligning with {keyword_name.upper()} Trait: {good_examples} \n"
        f" -- EXAMPLES failing on {keyword_name.upper()} Trait: {bad_examples} \n\n")



def longest_common_substring_len(a: str, b: str) -> int:
    a, b = a.lower(), b.lower()
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    best = 0
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                best = max(best, dp[i][j])
    return best


def best_match_by_lcs(query: str, candidates: list) -> str | None:
    best_score, best_candidate = 0, None
    for c in candidates:
        score = longest_common_substring_len(query, c)
        if score > best_score:
            best_score = score
            best_candidate = c
    return best_candidate

def decide_adaptive_pattern(question, answer, model):
    app_dir = find_app_dir()
    json_path = app_dir / "static" / "data" / "pattern_info.json"
    with open(json_path, "r", encoding="utf-8") as f:
        pattern_info = json.load(f)
    adaptive_pattern_dict = pattern_info["Adaptive"]
    selection_prompt_tmp = "You are an educational expert. Below are a pair of (question, student answer) and the guidance to select proper feedback pattern to him/her. You should response with one word in [conceptual, procedural, correctness] without any other comments or explanation. You are NOT asked to comment on or give feedback to the student answer."
    selection_prompt_tmp += str(adaptive_pattern_dict)
    qa_query = f"# Question: {question}; # Studeng Answer: {answer}; \n # Your Selection (one word in [conceptual, procedural, correctness]):"
    select_pattern_text, _ = llm_generate(
                           user_prompt=qa_query, system_prompt=selection_prompt_tmp, 
                            model=model, max_retry=5, have_log=False)
    matched_pattern_key = best_match_by_lcs(select_pattern_text, pattern_info.keys())
    if matched_pattern_key.lower() not in ['conceptual', 'procedural', 'correctness']:
        matched_pattern_key = 'conceptual'
    return matched_pattern_key.capitalize()


def parse_feedback_pattern(
        feedback_pattern: str = None, 
        custom_rubric: str = None, 
        model: str = 'gemini-3.1-flash-lite-preview',
        from_adaptive: bool = False,
        **kwarg) -> str:
    
    app_dir = find_app_dir()
    json_path = app_dir / "static" / "data" / "pattern_info.json"
    with open(json_path, "r", encoding="utf-8") as f:
        pattern_info = json.load(f)
    
    pattern_input_lower = feedback_pattern.lower().strip()
    default_pattern_key, default_pattern = next(iter(pattern_info.items()))  # default = first one
    pattern_body, case_num = None, 0
    if from_adaptive:
        case_num = -1
        matched_pattern_key = best_match_by_lcs(pattern_input_lower, pattern_info.keys())
        pattern_body = pattern_info.get(matched_pattern_key.capitalize(), {})
        focus_selection_rule = pattern_info['Adaptive']['focus_selection_rule'].get(matched_pattern_key.lower(), "")
        pattern_body['primary_content_focus'] = f"{focus_selection_rule} \n {pattern_body['primary_content_focus']}"
        pattern_body['feedback_scope_rule'] = pattern_info['Adaptive']['feedback_scope_rule']
        pattern_body['exclusions'] = f"{pattern_info['Adaptive']['exclusions']} \n {pattern_body['exclusions']}"
    if len(pattern_input_lower) > 0 and 'custom' not in pattern_input_lower:
        case_num = 1
        # Case 1: Pre-defined Pattern
        matched_pattern_key = best_match_by_lcs(pattern_input_lower, pattern_info.keys())
        pattern_body = pattern_info.get(matched_pattern_key)
    elif str(custom_rubric).strip() == 0:
        case_num = 3
        # Case 3: No match and no rubric -> plain pattern
        matched_pattern_key = "Plain"
        pattern_body = pattern_info.get(matched_pattern_key)
    else:
        # Case 2: Generate personal template
        case_num = 2
        matched_pattern_key = "Custom"
        customize_prompt = pattern_info.get("Rubric")
        system_prompt = str(customize_prompt)
        user_prompt = f"""User Rubric: {custom_rubric}"""
        print(f"*** debug: generate pattern user_prompt: `{user_prompt}`")
        print(f"*** debug: generate pattern system_prompt: `{system_prompt}`")
        pattern_body, pattern_prob = llm_generate_gemini(
            user_prompt=user_prompt, system_prompt=system_prompt, image=None,
            model=model, max_retry=5, have_log=False)
        if pattern_body is None:
            matched_pattern_key = "Custom (override by Plain)"
            pattern_body = pattern_info.get("Plain")
            
    print(f"[PATTERN] Pattern Case Above: {case_num}: `{matched_pattern_key}` from `{feedback_pattern}`")
    return {"pattern_key": matched_pattern_key, 
            "pattern_body": pattern_body}


def parse_teaching_text(
        question: str,
        answer: str,
        style_keywords: Union[str, List[str]],
        feedback_templates: str = "",
        # grading: list[str, str]
        ) -> str:
    
    # Step 1: optional, add grading information
    # grading_rubric, grading_text = grading
    # grading_prompt = ""
    app_dir = find_app_dir()
    data_dir = app_dir / "static" / "data" 
    keyword_info_path = data_dir / "keyword_info.json"
    try:
        with open(keyword_info_path, "r", encoding="utf-8") as f:
            keyword_info = json.load(f)
    except Exception as e:
        keyword_info = dict()
        
    # if grading_rubric and grading_text:
    #     grading_prompt = GRADING_REFERENCE.format(grading_rubric=grading_rubric, grading_text=grading_text)
    
    # Step 2: add macro-view-style
    if isinstance(style_keywords, str):
        keywords = [k.strip() for k in style_keywords.split(",") if k.strip()]
    elif isinstance(style_keywords, (list, tuple)):
        keywords = [str(k).strip() for k in style_keywords if str(k).strip()]
    else:
        keywords = []
    
    # keyword formatting
    keyword_full_text = ""
    for kw_idx, kw in enumerate(keywords):
        matched_kw = best_match_by_lcs(kw, keywords)
        info = keyword_info.get(matched_kw , None)
        if info is not None:
            kw_text_this = format_keyword_block(matched_kw, info)
            keyword_full_text += f"""### TRAIT KEYWORD {kw_idx+1}: \n {kw_text_this}"""
            
    macro_trait_prompt = MACRO_TRAIT_BASE.format(keyword_full_text)

    if not feedback_templates:
        feedback_templates = "- Stength, - Weakness, - Improvement."
    macro_template_prompt = MACRO_TEMPLATE_BASE.format(feedback_templates)
    
    # Step 3: final user text
    final_respond_prompt = macro_trait_prompt
    final_respond_prompt += FEEDBACK_BASE
    final_respond_prompt += FEEDBACK_INPUT_BASE.format(question=question, answer=answer)
    
    # if grading_prompt: 
    #     final_respond_prompt += grading_prompt
        
    final_respond_prompt += macro_template_prompt
    final_respond_prompt += FEEDBACK_OUTPUT_INSTRUCTION
    final_respond_prompt += "[PLACEHOLDER]\n"
    final_respond_prompt += "# IMPORTANT: if there is no meanful content in a section of given template, you may just skip this section; for example, if the response is almost perfect and your template contains the section of weakness, do not need to force saying something when there is little.\n"
    final_respond_prompt += "## Teacher (you) Response [NO MORE THAN *500* WORDS]: "
    return final_respond_prompt


def format_response_html(response_text: str = "Placeholder of Response.", certainty_score: str|float = 0):
    ## text
    html_text = html.escape(response_text)
    html_text = html_text.replace('\n', '<br>')
    html_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_text)
    
    ## conf
    certainty_score_default = -1
    case = 0
    if certainty_score is not None:
        if isinstance(certainty_score, float) and certainty_score>100:
            processed_certainty_score = float(certainty_score)
            processed_certainty_score = f"{processed_certainty_score:.2e}"
            case = 1
        elif isinstance(certainty_score, float):
            processed_certainty_score = float(certainty_score)
            processed_certainty_score = round(processed_certainty_score, 4)
            case = 2
        elif isinstance(certainty_score, int):
            processed_certainty_score = certainty_score
            case = 3
        else:
            processed_certainty_score = str(certainty_score)[:6]
            case = 4
        print(f">>9>>>Case{case}: {certainty_score} to {processed_certainty_score}; {type(processed_certainty_score)}")
    else:
        processed_certainty_score = -999
        
    # ppl_note = "*NOTE - PPL=1: fully certainty; - PPL→∞: increasing uncertainty."
    
    # confidence_display =f'<span style="color:#fb827a;font-weight:bold;">[PPL: {processed_certainty_score}] {ppl_note} </span>'
    # formatted_html = f"{html_text} <br> ----- <br> {confidence_display}"
    # return formatted_html
    return html_text





# =========================



    
      

## extract full score
def extract_full_score(text):
    vals=re.findall(r'"points"\s*:\s*"?(-?\d+(?:\.\d+)?)"?',text)
    nums=[float(v) for v in vals]
    total=sum(x for x in nums if x>=0)
    s=f"{total:.2f}".rstrip("0").rstrip(".")
    return s if s!="" else "0"