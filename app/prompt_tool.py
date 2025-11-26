from app.prompts import (
    COMMUNICATION_STYLE_EXTRACTION_PROMPT,
    TEACHING_METHOD_EXTRACTION_PROMPT,
    EMOTIONAL_TONE_EXTRACTION_PROMPT,
    TEACHER_IDENTITY_EXTRACTION_PROMPT,
    SUMMARIZE_PROMPT,
    MERGE_PROMPT
)

from utils import llm_generate as llm_function

### make teacher style prmopt ###
def extract_teaching_components(teacher_responses):
    responses_text = "\n\n---Response Record---\n".join([f"Response {i+1}: {response}" for i, response in enumerate(teacher_responses)])
    
    return {
        'communication_prompt': COMMUNICATION_STYLE_EXTRACTION_PROMPT.format(teacher_responses=responses_text),
        'methods_prompt': TEACHING_METHOD_EXTRACTION_PROMPT.format(teacher_responses=responses_text),
        'emotional_prompt': EMOTIONAL_TONE_EXTRACTION_PROMPT.format(teacher_responses=responses_text)
    }


def create_identity_prompt(communication_style, teaching_methods, emotional_tone):
    return TEACHER_IDENTITY_EXTRACTION_PROMPT.format(
        communication_style=communication_style,
        teaching_methods=teaching_methods,
        emotional_tone=emotional_tone
    )


def assemble_teaching_style_template(teacher_identity, communication_style, teaching_methods, emotional_tone):
    core_tone_line = [line for line in emotional_tone.split('\n') if line.startswith('Core Tone:')][0]
    interpersonal_line = [line for line in emotional_tone.split('\n') if line.startswith('Interpersonal Style:')][0]
    tone_description = core_tone_line.replace('Core Tone:', '').strip() + '. ' + interpersonal_line.replace('Interpersonal Style:', '').strip()
    template = f"""You are a {teacher_identity}. Your response should:
        {communication_style}
        {teaching_methods}
        Tone: {tone_description}"""
    return template


### Post-processing ###
def compress_style_text(input_text, maximum=275):
    if len(input_text.split()) > int(maximum):
        input_text = llm_function(SUMMARIZE_PROMPT.format(input_text), max_tokens=350, temperature=0.7)
    return input_text


def complete_style_extraction(teacher_responses):
    extraction_prompts = extract_teaching_components(teacher_responses)
    communication_style = llm_function(extraction_prompts['communication_prompt'], max_tokens=350, temperature=0.7)
    teaching_methods = llm_function(extraction_prompts['methods_prompt'], max_tokens=350, temperature=0.7)
    emotional_tone = llm_function(extraction_prompts['emotional_prompt'], max_tokens=350, temperature=0.7)
    
    identity_prompt = create_identity_prompt(communication_style, teaching_methods, emotional_tone)
    teacher_identity = llm_function(identity_prompt, max_tokens=350, temperature=0.7)
    
    final_prompt = assemble_teaching_style_template(
        teacher_identity, communication_style, teaching_methods, emotional_tone
    )
    return compress_style_text(final_prompt, maximum=275)


def complete_style_merge(standard_template, personal_template):
    input_prompts = MERGE_PROMPT.format(
        standard_template=standard_template,
        personal_template=personal_template)
    output_template = llm_function(input_prompts, max_tokens=350, temperature=0.7)
    return compress_style_text(output_template, maximum=275)


# max_tokens=350, temperature=0.7, logprobs = True