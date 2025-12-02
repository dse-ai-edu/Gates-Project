import base64
import openai
import traceback
import numpy as np

import os
import html
import re

from app import key_iter

from app.prompts import *

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def verify_response(response_text):
    # leave if for now and we will implement it later based on need
    return True

def vllm_generate(input_text:str, system_text:str=None, input_image:list=None, max_retry:int=3, **kwarg):
    if input_image:
        image_list = [encode_image('./app/'+x) for x in input_image]
        messages = [{
            'role':'user',
            'content':[{"type": "image_url", "image_url": 
                        {"url": "data:image/png;base64,{}".format(x),},} for x in image_list] \
                            + [{"type": "text","text":input_text},]
        }]
    else:
        messages = [{'role':'user','content':input_text},]
    
    if system_text is not None:
        messages = [{'role':'system','content':system_text},] + messages
    
    for _ in range(max_retry):
        try:
            client = openai.OpenAI(api_key=next(key_iter))
            response = client.chat.completions.create(
                messages=messages, **kwarg
            )
            response_text = response.choices[0].message.content
            if response.choices[0].logprobs:
                response_prob = response.choices[0].logprobs.content[0].logprob
                response_prob = np.round(np.exp(response_prob)*100, 2)
            else:
                response_prob = None
            return response_text, response_prob
        except:
            traceback.print_exc()
    
    raise SystemError('failed to generate response with llm.')


def llm_generate(input_text: str, system_text:str=None,  max_retry:int=3, **kwarg) -> str:
    
    messages = [{'role':'user','content':input_text},]
    
    if system_text is not None:
        messages = [{'role':'system','content':system_text},] + messages
    
    for _ in range(max_retry):
        try:
            client = openai.OpenAI(api_key=next(key_iter))
            response = client.chat.completions.create(
                messages=messages, 
                **kwarg
            )
            response_text = response.choices[0].message.content
            if response.choices[0].logprobs:
                response_prob = response.choices[0].logprobs.content[0].logprob
                response_prob = np.round(np.exp(response_prob)*100, 2)
            else:
                response_prob = None
            return response_text, response_prob
        except:
            traceback.print_exc()


## Response Generation 
def parse_teaching_style(
        teach_style: str = None, 
        teach_example: str = None, 
        resource: str = None, 
        example: str = None,
        **kwarg) -> str:

    # Step 1: Process teach_style
    standard_template = str(PLAIN)
    teach_style_upper = teach_style.upper()

    match teach_style_upper:
        case "AUTHORITATIVE":
            standard_template = str(AUTHORITATIVE)
        case "SOCRATIC":
            standard_template = str(SOCRATIC)
        case "NURTURING":
            standard_template = str(NURTURING)
        case "CONSTRUCTIVE":
            standard_template = str(CONSTRUCTIVE)
        case "DIRECT":
            standard_template = str(DIRECT)
        case "PLAIN":
            standard_template = str(PLAIN)
    #  
    # Step 2: Generate personal template
    personal_template = ""
    if teach_example:
        teach_style_custom_text = str(teach_example).strip()
        from app.prompt_tool import complete_style_extraction
        personal_template = complete_style_extraction(teach_style_custom_text)
    #  
    # Step 3: Merge templates or use standard
    if standard_template and personal_template:
        from app.prompt_tool import complete_style_merge
        final_respond_prompt = complete_style_merge(standard_template, personal_template)
    else:
        final_respond_prompt = standard_template
    #  
    return {"final": final_respond_prompt, 
            "selected": standard_template, 
            "custom": personal_template, }

def parse_teaching_text(
        question: str,
        answer: str,
        style_keywords: str,
        feedback_templates: str = "",
        # grading: list[str, str]
        ) -> str:
    
    # Step 1: optional, add grading information
    # grading_rubric, grading_text = grading
    grading_prompt = ""
    # if grading_rubric and grading_text:
    #     grading_prompt = GRADING_REFERENCE.format(grading_rubric=grading_rubric, grading_text=grading_text)
    
    # Step 2: add macro-view-style
    macro_trait_prompt = MACRO_TRAIT_BASE.format(style_keywords)

    if not feedback_templates:
        feedback_templates = "- Stength, - Weakness, - Improvement."
    macro_template_prompt = MACRO_TEMPLATE_BASE.format(feedback_templates)
    
    # Step 3: final user text
    final_respond_prompt = macro_trait_prompt
    final_respond_prompt += FEEDBACK_BASE
    # final_respond_prompt += "Below are requirements for your feedback response: {} \n".format(FEEDBACK_REQUIREMENT)
    final_respond_prompt += FEEDBACK_INPUT_BASE.format(question=question, answer=answer)
    if grading_prompt: final_respond_prompt += grading_prompt
    final_respond_prompt += macro_template_prompt
    final_respond_prompt += FEEDBACK_OUTPUT_INSTRUCTION
    final_respond_prompt += "## Teacher (you) Response [NO MORE THAN *500* WORDS]: "
    return final_respond_prompt


def format_response_html(response_text: str = "Placeholder of Response.", confidence: str|float = 0):
    ## text
    html_text = html.escape(response_text)
    html_text = html_text.replace('\n', '<br>')
    html_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_text)
    
    ## conf
    processed_confidence = 0.0
    if confidence is not None:
        confidence_str = str(confidence)[:20]
        pattern = r'^(\d+|\d+\.\d+)$'
        match = re.match(pattern, confidence_str.strip())
        if match:
            number_str = match.group(1)
            processed_confidence = float(number_str)
            processed_confidence = round(processed_confidence, 4)
    
    confidence_display = f'<span style="color:#666;font-size:0.85em;">[conf: {processed_confidence:.4f}]</span>'
    formatted_html = f"{html_text} <br> ----- <br> {confidence_display}"
    return formatted_html