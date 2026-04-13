import re, html, json


from pathlib import Path
from typing import Union, List

import app.prompts as prompts
from app.llm_utils import llm_generate_gemini


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


## extract full score
def extract_full_score(text):
    vals=re.findall(r'"points"\s*:\s*"?(-?\d+(?:\.\d+)?)"?',text)
    nums=[float(v) for v in vals]
    total=sum(x for x in nums if x>=0)
    s=f"{total:.2f}".rstrip("0").rstrip(".")
    final = s if s!="" else "0"
    print(f"Get Full Score as {final}")
    return final


## Response Generation 
def format_keyword_block(keyword: str, info: dict) -> str:
    # component 1 with 4 keywords
    short = info.get("short", "NA").strip()
    detail = info.get("detail", "NA").strip()
    return (f"""KEYWORD: {keyword} \n SUMMARY: {short} \n DETAILS: {detail}""")


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
    selection_prompt_tmp = prompts.ADAPTIVE_DECIDE
    selection_prompt_tmp += str(adaptive_pattern_dict)
    qa_query = f"# Question: {question}; # Studeng Answer: {answer}; \n # Your Selection (one word in [conceptual, procedural, correctness]):"
    select_pattern_text, _ = llm_generate_gemini(
                           input_text=qa_query,
                           system_text=selection_prompt_tmp,
                           model=model, 
                           max_retry=5, 
                           have_log=False)
    
    matched_pattern_key = best_match_by_lcs(select_pattern_text, pattern_info.keys())
    if matched_pattern_key.lower() not in ['conceptual', 'procedural', 'correctness']:
        matched_pattern_key = 'conceptual'
    return matched_pattern_key.capitalize()


def parse_feedback_pattern(
        feedback_pattern: str = None, 
        custom_rubric: str = None, 
        model: str = 'gpt-4o-mini',
        from_adaptive: bool = False,
        **kwarg) -> str:
    app_dir = find_app_dir()
    json_path = app_dir / "static" / "data" / "pattern_info.json"
    with open(json_path, "r", encoding="utf-8") as f:
        pattern_info = json.load(f)
    
    pattern_input_lower = feedback_pattern.lower().strip()
    # default_pattern_key, default_pattern = next(iter(pattern_info.items()))  # default = first one
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
        system_text = str(customize_prompt)
        input_text = f"""User Rubric: {custom_rubric}"""
        pattern_body, pattern_prob = llm_generate_gemini(
            input_text=input_text, system_text=system_text, 
            model=model, max_retry=5, have_log=False)
        if pattern_body is None:
            matched_pattern_key = "Custom (override by Plain)"
            pattern_body = pattern_info.get("Plain")
            
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
    app_dir = find_app_dir()
    data_dir = app_dir / "static" / "data" 
    keyword_info_path = data_dir / "keyword_info.json"
    try:
        with open(keyword_info_path, "r", encoding="utf-8") as f:
            keyword_info = json.load(f)
    except Exception as e:
        keyword_info = dict()
    
    # Step 2: add macro-view-style
    if isinstance(style_keywords, str):
        keywords = [k.strip() for k in style_keywords.split(",") if k.strip()]
    elif isinstance(style_keywords, (list, tuple)):
        keywords = [str(k).strip() for k in style_keywords if str(k).strip()]
    else:
        keywords = []
    
    # keyword formatting
    keyword_full_text = ""
    for kw in keywords:
        matched_kw = best_match_by_lcs(kw, keywords)
        info = keyword_info.get(matched_kw , None)
        if info is not None:
            kw_text_this = format_keyword_block(matched_kw, info)
            keyword_full_text += f"""\n\n{kw_text_this}"""
            
    macro_trait_prompt = prompts.MACRO_TRAIT_BASE.format(keyword_full_text)

    if not feedback_templates:
        feedback_templates = "- Stength, - Weakness, - Improvement."
    macro_template_prompt = prompts.MACRO_TEMPLATE_BASE.format(feedback_templates)
    
    # Step 3: final user text
    final_respond_prompt = macro_trait_prompt
    final_respond_prompt += prompts.FEEDBACK_BASE
    final_respond_prompt += prompts.FEEDBACK_INPUT_BASE.format(question=question, answer=answer)
    
    final_respond_prompt += macro_template_prompt
    final_respond_prompt += prompts.FEEDBACK_OUTPUT_INSTRUCTION
    final_respond_prompt += "[PLACEHOLDER]\n"
    final_respond_prompt += prompts.FEEDBACK_NO_FORCE
    final_respond_prompt += "## Teacher (you) Response [NO MORE THAN *500* WORDS]: "
    return final_respond_prompt


def format_response_html(response_text: str = "Placeholder of Response.", certainty_score: str|float = 0):
    ## text
    html_text = html.escape(response_text)
    html_text = html_text.replace('\n', '<br>')
    html_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_text)
    
    ## conf
    # certainty_score_default = -1
    # case = 0
    # if certainty_score is not None:
    #     if isinstance(certainty_score, float) and certainty_score>100:
    #         processed_certainty_score = float(certainty_score)
    #         processed_certainty_score = f"{processed_certainty_score:.2e}"
    #         case = 1
    #     elif isinstance(certainty_score, float):
    #         processed_certainty_score = float(certainty_score)
    #         processed_certainty_score = round(processed_certainty_score, 4)
    #         case = 2
    #     elif isinstance(certainty_score, int):
    #         processed_certainty_score = certainty_score
    #         case = 3
    #     else:
    #         processed_certainty_score = str(certainty_score)[:6]
    #         case = 4
    #     print(f">>9>>>Case{case}: {certainty_score} to {processed_certainty_score}; {type(processed_certainty_score)}")
    # else:
    #     processed_certainty_score = -999
        
    # ppl_note = """Note - PPL=1: fully certainty; - PPL→∞: increasing uncertainty."""
    # confidence_display =f'<span style="color:#fb827a;font-weight:bold;">[PPL: {processed_certainty_score}] {ppl_note} </span>'
    # formatted_html = f"{html_text} <br> ----- <br> {confidence_display}"
    # return formatted_html
    return html_text




# def encode_image(image_path: str) -> str:
#     with open(image_path, 'rb') as image_file:
#         return base64.standard_b64encode(image_file.read()).decode('utf-8')


# def parse_structured_json(text: str):
#     match = re.search(r"\{[\s\S]*\}", text)
#     if not match:
#         raise ValueError(f"No JSON object found in: {text}")

#     json_str = match.group(0)
#     try:
#         return json.loads(json_str)
#     except Exception as e:
#         raise ValueError(f"Failed to parse JSON: {json_str}") from e


# def ppl_from_response(response, min_logprob=-100):
#     logps = []
#     for item in response.choices[0].logprobs.content:
#         lp = item.logprob
#         if lp is None:
#             continue
#         if lp < min_logprob: 
#             continue
#         logps.append(lp)
#     if not logps:
#         return None
#     return float(np.exp(-np.mean(logps)))

# =========================