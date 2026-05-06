from pydantic import BaseModel, Field
import openai

from app.prompts import FEEDBACK_POST_PROCESS_PROMPT

from app import key_iter

import utils as utils

class FeedbackPostProcessOutput(BaseModel):
    text: str
    flag: int


def run_feedback_post_process_llm(
    user_text: str,
    model: str = "gemini-3.1-flash-lite-preview",
    max_retry: int = 3,
):

    last_error = None

    for _ in range(max_retry):
        try:
            response = utils.llm_generate(
                user_prompt="# Input: the feedback text to process: ```{user_text}```",
                system_prompt=FEEDBACK_POST_PROCESS_PROMPT,
                model=model,
                text_format=FeedbackPostProcessOutput,
            )

            parsed_output = response.output_parsed
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
    print(f"[ERROR INPUT]: {messages}")
    raise RuntimeError(f"Feedback Post-process LLM failed after {max_retry} retries. Last error: {last_error}")
