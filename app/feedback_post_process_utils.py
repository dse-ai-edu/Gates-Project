from app.text_prompts import FEEDBACK_POST_PROCESS_PROMPT

from app.llm_utils import llm_generate

from pydantic import BaseModel


def run_feedback_post_process_llm(
    user_text: str,
    model: str = "gemini-3.1-flash-lite-preview",
    max_retry: int = 3,
):

    from app.data_structure import FeedbackPostProcessOutput

    try:

        response = llm_generate(
            user_prompt=f"# Input: the feedback text to process: ```{user_text}```",
            system_prompt=FEEDBACK_POST_PROCESS_PROMPT,
            model=model,
            text_format=FeedbackPostProcessOutput,
            max_retry=max_retry,
        )

        if response.obj is None:
            raise ValueError(
                "Structured output missing from LLM."
            )

        if isinstance(response.obj, BaseModel):
            parsed_output = response.obj.model_dump()

        elif isinstance(response.obj, dict):
            parsed_output = response.obj

        else:
            raise ValueError(
                f"Unexpected structured output type: "
                f"{type(response.obj)}"
            )

        final_text = parsed_output.get("text", "")
        final_flag = parsed_output.get("flag", "")

        if not final_text:
            raise ValueError(
                "Empty output from post-process LLM."
            )

        if "0" in str(final_flag):

            return {
                "text": user_text,
                "flag": 0,
            }

        return {
            "text": final_text.strip(),
            "flag": 1,
        }

    except Exception as e:

        print(f"[ERROR]: {e}")
        print(f"[ERROR INPUT]: {user_text}")

        raise RuntimeError(
            f"Feedback Post-process LLM failed "
            f"after {max_retry} retries. "
            f"Last error: {e}"
        )