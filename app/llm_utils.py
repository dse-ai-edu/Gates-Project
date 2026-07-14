import os
import base64

from pathlib import Path

import numpy as np

from app import key_iter
from app.data_structure import llm_output


# =========================
# GENERAL TOOLS
# =========================

def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.standard_b64encode(
            image_file.read()
        ).decode("utf-8")


def get_image_media_type(image_path: str) -> str:

    ext = Path(image_path).suffix.lower()

    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }

    return media_types.get(
        ext,
        "image/jpeg",
    )


def is_path_like(x):
    return isinstance(x, (str, Path))



# =========================
# GEMINI TOOLS
# =========================

def _prepare_gemini_parts(
    user_prompt,
    image=None,
    img_type=None,
):

    from google.genai import types

    parts = []

    if image is not None:

        if isinstance(
            image,
            (str, Path),
        ):

            image_path = Path(image)

            with open(
                image_path,
                "rb",
            ) as f:

                image_bytes = f.read()

            parts.append(
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=
                    get_image_media_type(
                        image_path
                    ),
                )
            )

        elif isinstance(image, dict):

            parts.append(
                types.Part.from_bytes(
                    data=image["bytes"],
                    mime_type=
                    image["mime_type"],
                )
            )

        elif isinstance(
            image,
            (bytes, bytearray),
        ):

            if img_type is None:

                raise ValueError(
                    "img_type is required"
                )

            parts.append(
                types.Part.from_bytes(
                    data=image,
                    mime_type=img_type,
                )
            )

        else:

            raise TypeError(
                f"Unsupported image type: "
                f"{type(image)}"
            )

    if user_prompt:

        parts.append(
            types.Part.from_text(
                text=user_prompt
            )
        )

    return parts


def _extract_gemini_text(response):

    texts = []

    if hasattr(response, "candidates"):

        for cand in (
            response.candidates or []
        ):

            content = getattr(
                cand,
                "content",
                None,
            )

            if content:

                for part in getattr(
                    content,
                    "parts",
                    [],
                ) or []:

                    text = getattr(
                        part,
                        "text",
                        None,
                    )

                    if text:

                        texts.append(text)

    if (
        not texts
        and hasattr(response, "text")
    ):

        return response.text or ""

    return "\n".join(texts)


def _llm_generate_gemini(
    system_prompt,
    user_prompt,
    image,
    model,
    max_tokens,
    max_retry,
    img_type=None,
    text_format=None,
):

    import json

    from google import genai

    api_key = os.getenv(
        "GOOGLE_API_KEY"
    )

    if not api_key:

        raise RuntimeError(
            "GOOGLE_API_KEY not set"
        )

    client = genai.Client(
        api_key=api_key
    )

    parts = _prepare_gemini_parts(
        user_prompt=user_prompt,
        image=image,
        img_type=img_type,
    )

    if system_prompt is not None:
        if not isinstance(system_prompt, str):
            system_prompt = str(system_prompt)
            

    config = {
        "system_instruction":
        system_prompt,

        "max_output_tokens":
        max_tokens,
    }

    structured = (
        text_format is not None
    )

    if structured:

        config[
            "response_mime_type"
        ] = "application/json"

        config["response_schema"] = (text_format.model_json_schema())

    for retry_i in range(max_retry):

        try:

            response = (
                client.models.generate_content(
                    model=model,
                    contents=parts,
                    config=config,
                )
            )

            if structured:

                response_text = (
                    _extract_gemini_text(
                        response
                    ).strip()
                )

                try:

                    structured_data = (
                        json.loads(
                            response_text
                        )
                    )

                except Exception as e:

                    raise RuntimeError(
                        f"Failed to parse "
                        f"Gemini JSON response: "
                        f"{response_text}"
                    ) from e

                try:

                    structured_obj = (
                        text_format
                        .model_validate(
                            structured_data
                        )
                    )

                except Exception as e:

                    raise RuntimeError(
                        f"Failed to validate "
                        f"Gemini structured "
                        f"output: "
                        f"{structured_data}"
                    ) from e

                return llm_output(
                    obj=structured_obj,
                    logprob=None,
                )

            return llm_output(
                text=
                _extract_gemini_text(
                    response
                ).strip(),

                logprob=None,
            )

        except Exception as e:

            error_msg = str(e)

            print(
                f"[GEMINI ERROR] "
                f"{error_msg}"
            )

    raise RuntimeError(error_msg)

# =========================
# MAIN ENTRY
# =========================

def llm_generate(
    user_prompt,
    system_prompt=None,
    image=None,
    model="gemini-3.1-flash-lite-preview",
    max_tokens=8192,
    max_retry=3,
    img_type=None,
    text_format=None,
    enable_logprob=False,
):

    model_lower = model.lower()

    # Requirement: EVERY LLM call -- text or image, strong or weak model -- must
    # go through Gemini. We never call OpenAI or any other provider. Any
    # non-Gemini model that slips in is redirected to the Gemini default rather
    # than routed to a different backend.
    if not ("gemini" in model_lower or "gemma" in model_lower):
        print(f"[LLM] Non-Gemini model '{model}' redirected to Gemini default.")
        model = "gemini-3.1-flash-lite-preview"

    return _llm_generate_gemini(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        image=image,
        model=model,
        max_tokens=max_tokens,
        max_retry=max_retry,
        img_type=img_type,
        text_format=text_format,
    )