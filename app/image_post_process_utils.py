from pydantic import BaseModel

from app.image_prompts import IMAGE_POST_PROCESS_PROMPT

from app.llm_utils import llm_generate

from app.data_structure import ImagePostProcessOutput


def run_image_post_process_llm(
    user_text: str,
    model: str = "gemini-3.1-flash-lite-preview",
    max_retry: int = 3,
):

    try:

        response = llm_generate(
            user_prompt=user_text,
            system_prompt=IMAGE_POST_PROCESS_PROMPT,
            model=model,
            text_format=ImagePostProcessOutput,
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

        final_text = parsed_output.get(
            "text",
            "",
        ).strip()

        if not final_text:
            raise ValueError(
                "Empty output from post-process LLM."
            )

        lowered = final_text.lower()

        if lowered == "[reject]":

            return {
                "text": "[REJECT]",
                "flag": 0,
            }

        elif "[reject]" in lowered and lowered != "[reject]":

            return {
                "text": "[REJECT] - soft",
                "flag": 0,
            }

        return {
            "text": final_text,
            "flag": 1,
        }

    except Exception as e:

        print(f"[ERROR INPUT]: {user_text}")

        raise RuntimeError(
            f"Image Post-process LLM failed "
            f"after {max_retry} retries. "
            f"Last error: {e}"
        )