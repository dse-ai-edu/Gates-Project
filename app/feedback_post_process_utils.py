import os

from pydantic import BaseModel, Field

from app.config import Config
from app.prompts import FEEDBACK_POST_PROCESS_PROMPT

class FeedbackPostProcessOutput(BaseModel):
    text: str
    flag: int


def run_feedback_post_process_llm(
    user_text: str,
    model: str = Config.GEMINI_MODEL_LOW,
    max_retry: int = 3,
):
    from google import genai
    from google.genai import types

    api_key = os.getenv("GOOGLE_API_KEY")
    user_prompt = f"# Input: the feedback text to process: ```{user_text}```"

    config = {
        "system_instruction": FEEDBACK_POST_PROCESS_PROMPT,
        "response_mime_type": "application/json",
        "response_json_schema": FeedbackPostProcessOutput.model_json_schema(),
    }

    last_error = None

    for i in range(max_retry):
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model,
                contents=[types.Part.from_text(text=user_prompt)],
                config=config,
            )

            parsed_output = FeedbackPostProcessOutput.model_validate_json(response.text)
            parsed_output = parsed_output.dict()

            final_text = parsed_output.get("text", "")
            final_flag = parsed_output.get("flag", "")

            # ===== Sanity Checks =====
            if not final_text:
                raise ValueError("Empty output from post-process LLM.")

            if "0" in str(final_flag):
                return {"text": user_text, "flag": 0}
            else:
                final_output = {"text": final_text.strip(), "flag": 1}
            return final_output

        except Exception as e:
            last_error = e
            continue

    print(f"[ERROR]: {last_error}")
    print(f"[ERROR INPUT]: {user_prompt}")
    raise RuntimeError(f"Feedback Post-process LLM failed after {max_retry} retries. Last error: {last_error}")
