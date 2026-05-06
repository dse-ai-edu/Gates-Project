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
# GPT TOOLS
# =========================

def ppl_from_response(
    response,
    min_logprob=-100,
):

    logps = []

    for item in response.choices[0].logprobs.content:

        lp = item.logprob

        if lp is None:
            continue

        if lp < min_logprob:
            continue

        logps.append(lp)

    if not logps:
        return None

    return float(
        np.exp(-np.mean(logps))
    )


def _llm_generate_gpt(
    system_prompt,
    user_prompt,
    model,
    max_tokens,
    max_retry,
    text_format=None,
    enable_logprob=False,
):

    import openai

    user_msg = {
        "role": "user",
        "content": str(user_prompt),
    }

    if system_prompt is not None:

        messages = [
            {
                "role": "system",
                "content": str(system_prompt),
            },
            user_msg,
        ]

    else:

        messages = [user_msg]

    structured = (
        text_format is not None
    )

    for retry_i in range(max_retry):

        try:

            client = openai.OpenAI(
                api_key=next(key_iter)
            )

            kwargs = {
                "messages": messages,
                "model": model,
                "max_tokens": max_tokens,
            }

            if structured:

                kwargs["response_format"] = (
                    text_format
                )

            elif enable_logprob:

                kwargs["logprobs"] = True
                kwargs["top_logprobs"] = 1

            response = (
                client.chat.completions.create(
                    **kwargs
                )
            )

            response_text = (
                response
                .choices[0]
                .message
                .content
            )

            if structured:

                try:

                    structured_obj = (
                        response
                        .choices[0]
                        .message
                        .parsed
                    )

                except Exception:

                    structured_obj = (
                        response_text
                    )

                return llm_output(
                    obj=structured_obj,
                    logprob=None,
                )

            if (
                enable_logprob
                and hasattr(
                    response.choices[0],
                    "logprobs",
                )
                and response.choices[0]
                .logprobs is not None
            ):

                response_prob = (
                    ppl_from_response(
                        response
                    )
                )

            else:

                response_prob = None

            return llm_output(
                text=response_text,
                logprob=response_prob,
            )

        except Exception as e:

            error_msg = str(e)

            print(
                f"[GPT ERROR] "
                f"{error_msg}"
            )

    raise RuntimeError(error_msg)


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

                try:

                    structured_obj = (
                        response.parsed
                    )

                except Exception:

                    structured_obj = (
                        response
                    )

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

    if "gpt" in model_lower:

        return _llm_generate_gpt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            max_tokens=max_tokens,
            max_retry=max_retry,
            text_format=text_format,
            enable_logprob=
            enable_logprob,
        )

    elif (
        "gemini" in model_lower
        or "gemma" in model_lower
    ):

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

    else:

        raise ValueError(
            f"Unknown model: {model}"
        )