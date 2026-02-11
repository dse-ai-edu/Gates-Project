from pydantic import BaseModel, Field
import openai

from question_image_prompt import IMAGE_POST_PROCESS_PROMPT

from app import key_iter


class ImagePostProcessOutput(BaseModel):
    text: str
    flag: int

def run_image_post_process_llm(
    user_text: str,
    model: str = 'gpt-4.1-nano', 
    max_retry: int = 3,
):
    messages = [
        {"role": "system", "content": IMAGE_POST_PROCESS_PROMPT},
        {"role": "user", "content": user_text},
    ]

    last_error = None

    for i in range(max_retry):
        try:
            client = openai.OpenAI(api_key=next(key_iter))
            response = client.responses.parse(
                input=messages,
                model=model,
                text_format=ImagePostProcessOutput,
            )

            parsed_output = response.output_parsed
            parsed_output = parsed_output.dict()

            final_text = parsed_output.get("text", "").strip()

            # ===== Sanity Checks =====
            if not final_text:
                raise ValueError("Empty output from post-process LLM.")

            lowered = final_text.lower()
            # Case 1: Clean reject
            if lowered == "[reject]":
                return {text: "[REJECT]", flag: 0}

            # Case 2: Must NOT contain extra commentary about rejection
            
            elif "[reject]" in lowered and lowered != "[REJECT]":
                return {text: "[REJECT] - soft", flag: 0}

            # Otherwise: faithfully return cleaned content
            else:
                final_output = {
                    "text": final_text,
                    "flag": 1
                }
            return final_output

        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"Post-process LLM failed after {max_retry} retries. Last error: {last_error}")
