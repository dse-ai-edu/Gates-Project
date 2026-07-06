import os

from pydantic import BaseModel, Field

from app.config import Config
from app.question_image_prompt import IMAGE_POST_PROCESS_PROMPT

class ImagePostProcessOutput(BaseModel):
    text: str
    flag: int


def run_image_post_process_llm(
    user_text: str,
    model: str = Config.GEMINI_MODEL_LOW,
    max_retry: int = 3,
):
    from google import genai
    from google.genai import types

    api_key = os.getenv("GOOGLE_API_KEY")

    config = {
        "system_instruction": IMAGE_POST_PROCESS_PROMPT,
        "response_mime_type": "application/json",
        "response_json_schema": ImagePostProcessOutput.model_json_schema(),
    }

    last_error = None

    for i in range(max_retry):
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model,
                contents=[types.Part.from_text(text=user_text)],
                config=config,
            )

            parsed_output = ImagePostProcessOutput.model_validate_json(response.text)
            parsed_output = parsed_output.dict()

            final_text = parsed_output.get("text", "").strip()

            # ===== Sanity Checks =====
            if not final_text:
                raise ValueError("Empty output from post-process LLM.")

            lowered = final_text.lower()
            # Case 1: Clean reject
            if lowered == "[reject]":
                return {"text": "[REJECT]", "flag": 0}

            # Case 2: Must NOT contain extra commentary about rejection
            elif "[reject]" in lowered and lowered != "[REJECT]":
                return {"text": "[REJECT] - soft", "flag": 0}

            # Otherwise: faithfully return cleaned content
            else:
                final_output = {"text": final_text, "flag": 1}
            return final_output

        except Exception as e:
            last_error = e
            continue

    print(f"[ERROR INPUT]: {user_text}")
    raise RuntimeError(f"Image Post-process LLM failed after {max_retry} retries. Last error: {last_error}")
