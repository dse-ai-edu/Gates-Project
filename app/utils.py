import base64
import openai
import traceback
import numpy as np

import json
from pathlib import Path
from typing import Union, List

import numpy as np

import os
import html
import re

from app import key_iter

from app.prompts import *
from app.pattern_prompt import *

from pathlib import Path


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


# Multi Modal LLM
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def verify_response(response_text):
    # leave if for now and we will implement it later based on need
    return True

# def vllm_generate(input_text:str, system_text:str=None, input_image:list=None, max_retry:int=3, **kwarg):
#     if input_image:
#         image_list = [encode_image('./app/'+x) for x in input_image]
#         messages = [{
#             'role':'user',
#             'content':[{"type": "image_url", "image_url": 
#                         {"url": "data:image/png;base64,{}".format(x),},} for x in image_list] \
#                             + [{"type": "text","text":input_text},]
#         }]
#     else:
#         messages = [{'role':'user','content':input_text},]
    
#     if system_text is not None:
#         messages = [{'role':'system','content':system_text},] + messages
    
#     for _ in range(max_retry):
#         try:
#             client = openai.OpenAI(api_key=next(key_iter))
#             response = client.chat.completions.create(
#                 messages=messages, **kwarg
#             )
#             response_text = response.choices[0].message.content
#             if response.choices[0].logprobs:
#                 response_prob = response.choices[0].logprobs.content[0].logprob
#                 response_prob = np.round(np.exp(response_prob)*100, 2)
#             else:
#                 response_prob = None
#             return response_text, response_prob
#         except:
#             traceback.print_exc()
    
#     raise SystemError('failed to generate response with llm.')


def ppl_from_response(response, min_logprob=-100):
    logps = []
    for item in response.choices[0].logprobs.content:
        lp = item.logprob
        if lp is None:
            continue
        if lp < min_logprob: 
            continue
        logps.append(lp)
    if not logps:
        return None
    return float(np.exp(-np.mean(logps)))

# LLM main calling
def llm_generate(
    input_text: str, 
    system_text: str = None, 
    model: str = 'gpt-4o-mini', 
    max_retry: int = 3, 
    max_tokens: int = 2048,
    have_log: bool = False, 
    # **kwarg
    ) -> str:
    
    user_msg = {'role':'user','content': str(input_text)}
    if system_text is not None:
        system_msg = {'role':'system','content':str(system_text)}
        messages = [system_msg, user_msg]
    else:
        messages = [user_msg]  
        
    for _ in range(max_retry):
        print(f"[SYS] Num of Try: {_}:")
        try:
            client = openai.OpenAI(api_key=next(key_iter))
            if have_log: 
                print(f"!!! debug: before response generation A: ")
                response = client.chat.completions.create(
                    messages=messages, 
                    model=model,
                    max_tokens=max_tokens if max_tokens is not None else 2048,
                    top_logprobs=1,
                    logprobs=True,
                    # **kwarg
                    )
                
                response_showing = f"{str(response)[:200]} ... {str(response)[-200:]}" if len(str(response)) > 450 else str(response)
                
                print(f"!!! debug: after response generation A, {response_showing}")
                
            else:
                print(f"!!! debug: before response generation B: ")
                response = client.chat.completions.create(messages=messages, model=model, max_tokens=max_tokens)
                response_showing = f"{str(response)[:200]} ... {str(response)[-200:]}" if len(str(response)) > 450 else str(response)
                print(f"!!! debug: after response generation B, {response_showing}")
                
            response_text = response.choices[0].message.content
            response_text_showing = f"{str(response_text)[:200]} ... {str(response_text)[-200:]}" if len(str(response_text)) > 450 else str(response_text)
            print(f"!!! debug: response_text: {response_text_showing}")
            if hasattr(response.choices[0], "logprobs") and response.choices[0].logprobs is not None:
                print(f"--- LOGPROB: ")
                # with open("tmp0202.json", "w") as g:
                #     response_dict = response.model_dump()
                #     json.dump(response_dict, g, ensure_ascii=False, indent=2)
                print(f"--- TEXT: {response_text}")
                print(f"--- Len of log content: {len(response.choices[0].logprobs.content)}")
                response_prob = ppl_from_response(response)
            else:
                response_prob = None
            print(f"!!! debug: response_prob: {response_prob}")
            return response_text, response_prob
        except Exception as e:
            error_msg = str(e)
            print(f"!!! debug: response_prob error: {error_msg}")
            continue
    return error_msg, None


## Response Generation 
def format_keyword_block(keyword: str, info: dict) -> str:
    # component 1 with 4 keywords
    short = info.get("short", "NA").strip()
    detail = info.get("detail", "NA").strip()
    return (f"KEYWORD: {keyword} \n SUMMARY: {short} \n DETAILS: {detail}")


# def parse_teaching_style(
#         teach_style: str = None, 
#         teach_example: str = None, 
#         resource: str = None, 
#         example: str = None,
#         **kwarg) -> str:

#     # Step 1: Process teach_style
#     standard_template = str(TP_PLAIN) # default = plain style
#     teach_style_lower = teach_style.lower().strip()
#     if "tpha" in teach_style_lower:
#         standard_template = str(TP_HUMOROUS_ACTIVE)
#     elif "tprl" in teach_style_lower:
#         standard_template = str(TP_RIGOROUS_LOGICAL)
#     elif "tpcs" in teach_style_lower:
#         standard_template = str(TP_CARING_SHARING)
#     else:
#         standard_template = ""
#     #  
#     # Step 2: Generate personal template
#     personal_template = ""
#     if teach_example:
#         teach_style_custom_text = str(teach_example).strip()
#         from app.prompt_tool import complete_style_extraction
#         personal_template = complete_style_extraction(teach_style_custom_text)
#     #  
#     # Step 3: Merge templates or use standard
#     if standard_template and personal_template:
#         from app.prompt_tool import complete_style_merge
#         final_respond_prompt = complete_style_merge(standard_template, personal_template)
#     else:
#         final_respond_prompt = standard_template
#     #  
#     return {"final": final_respond_prompt, 
#             "selected": standard_template, 
#             "custom": personal_template, }

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

def parse_feedback_pattern(
        feedback_pattern: str = None, 
        custom_rubric: str = None, 
        model: str = 'gpt-4o-mini',
        **kwarg) -> str:
    
    app_dir = find_app_dir()
    json_path = app_dir / "static" / "data" / "pattern_info.json"
    with open(json_path, "r", encoding="utf-8") as f:
        pattern_info = json.load(f)
    
    pattern_input_lower = feedback_pattern.lower().strip()
    default_pattern_key, default_pattern = next(iter(pattern_info.items()))  # default = first one
    pattern_body, case_num = None, -1
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
        print(f"*** debug: generate pattern input_text: `{input_text}`")
        print(f"*** debug: generate pattern system_text: `{system_text}`")
        pattern_body, pattern_prob = llm_generate(
            input_text=input_text, system_text=system_text, 
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
    for kw in keywords:
        matched_kw = best_match_by_lcs(kw, keywords)
        info = keyword_info.get(matched_kw , None)
        if info is not None:
            kw_text_this = format_keyword_block(matched_kw, info)
            keyword_full_text += f"""\n\n{kw_text_this}"""
            
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
import base64

def encode_image(image_path: str) -> str:
    with open(image_path, 'rb') as image_file:
        return base64.standard_b64encode(image_file.read()).decode('utf-8')


def get_image_media_type(image_path: str) -> str:
    ext = Path(image_path).suffix.lower()
    media_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }
    return media_types.get(ext, 'image/jpeg')

    
def is_path_like(x):
    return isinstance(x, (str, Path))


def vllm_generate(
    input_text: str,
    system_text: str = None,
    input_image=None,
    max_retry: int = 3,
    img_type: str | None = None,
    project_dir: Path | None = None,
    **kwargs
):
    if project_dir is None:
        project_dir = Path(__file__).resolve().parents[1]

    image_arg = None

    if input_image:
        if isinstance(input_image, list) and input_image:
            first = input_image[0]
            if is_path_like(first):
                image_arg = project_dir / Path(first)
            else:
                image_arg = first
        elif is_path_like(input_image):
            image_arg = project_dir / Path(input_image)
        else:
            image_arg = input_image

    last_error = None

    for _ in range(max_retry):
        try:
            return llm_generate_gemini(
                system_prompt=system_text,
                user_prompt=input_text,
                image=image_arg,
                model="gemini-2.5-flash",
                max_tokens=8192,
                img_type=img_type,
            ), None
        except Exception as e:
            last_error = e
            traceback.print_exc()

    raise SystemError(
        f"failed to generate response with gemini: {last_error}"
    )

        
def llm_generate_gemini(
    system_prompt: str,
    user_prompt: str,
    image=None,
    model: str = "gemini-2.5-flash",
    max_tokens: int = 8192,
    img_type: str | None = None,
) -> str:
    from google import genai
    from google.genai import types

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not set")

    client = genai.Client(api_key=api_key)
    parts = []

    # ---- image input (at most ONE image) ----
    if image is not None:
        # 1 path-like
        if isinstance(image, (str, Path)):
            image_path = Path(image)
            if not image_path.exists():
                raise FileNotFoundError(f"Image not found: {image_path}")
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            parts.append(
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=get_image_media_type(image_path)
                )
            )

        # 2 dict payload: {"bytes": ..., "mime_type": ...}
        elif isinstance(image, dict):
            if "bytes" not in image or "mime_type" not in image:
                raise ValueError("image dict must contain 'bytes' and 'mime_type'")
            parts.append(
                types.Part.from_bytes(
                    data=image["bytes"],
                    mime_type=image["mime_type"]
                )
            )

        # 3 raw bytes / bytearray
        elif isinstance(image, (bytes, bytearray)):
            if not img_type:
                raise ValueError("img_type is required when image is raw bytes")
            parts.append(
                types.Part.from_bytes(
                    data=image,
                    mime_type=img_type
                )
            )

        else:
            raise TypeError(f"Unsupported image type: {type(image)}")

    # ---- optional user text ----
    if user_prompt:
        parts.append(types.Part.from_text(user_prompt))

    if not parts:
        raise ValueError("Both image and user_prompt are empty")

    contents = [
        types.Content(
            role="user",
            parts=parts
        )
    ]

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt if system_prompt else None,
            max_output_tokens=max_tokens,
            # response_mime_type="text/plain",
            response_mime_type="application/json",
        )
    )

    return get_gemini_output_text(response).strip()



def get_gemini_output_text(response):
    texts = []

    # new SDK method
    if hasattr(response, "candidates"):
        for cand in response.candidates or []:
            content = getattr(cand, "content", None)
            if content:
                for part in getattr(content, "parts", []) or []:
                    text = getattr(part, "text", None)
                    if text:
                        texts.append(text)

    # if given response.text
    if not texts and hasattr(response, "text"):
        return response.text or ""

    return "\n".join(texts)