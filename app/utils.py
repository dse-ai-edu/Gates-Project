import base64
import openai
import traceback
import numpy as np

from app import key_iter

from app.personalize.respond_prompts import *

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def verify_response(response_text):
    # leave if for now and we will implement it later based on need
    return True

def llm_generate(input_text:str, system_text:str=None, input_image:list=None, max_retry:int=3, **kwarg):
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


## Response Generation 
def parse_teaching_style(
        teach_style: str = None, 
        teach_order: str = None, 
        resource: str = None, 
        example: str = None) -> str:

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
    teach_style_custom_text = ""
    if teach_order:
        teach_style_custom_text = str(teach_order).strip()
        from personalize.prompt_tool import complete_style_extraction
        personal_template = complete_style_extraction(teach_style_custom_text)
    #  
    # Step 3: Merge templates or use standard
    if standard_template and personal_template:
        from personalize.prompt_tool import complete_style_merge
        final_respond_prompt = complete_style_merge(standard_template, personal_template)
    else:
        final_respond_prompt = standard_template
    #  
    return final_respond_prompt

def parse_teaching_text(
        question: str,
        answer: str, 
        grading: list[str, str]) -> str:
    
    grading_rubric, grading_text = grading

    # Step 1: optional, add grading information
    grading_template = ""
    if grading_rubric and grading_text:
        grading_template = GRADING_BASE.format(grading_rubric=grading_rubric, grading_text=grading_text)
    # Step 2: final user text
    final_respond_prompt = GRADING_LOAD.format(question=question, answer=answer)
    return final_respond_prompt