import re, os, json
from pathlib import Path

import traceback

from dotenv import load_dotenv
load_dotenv()


def get_image_media_type(image_path: str) -> str:
    ext = Path(image_path).suffix.lower()
    media_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }
    return media_types.get(ext, 'image/jpeg')


def get_gemini_output_text(response):
    texts = []
    if hasattr(response, "candidates"):
        for cand in response.candidates or []:
            content = getattr(cand, "content", None)
            if content:
                for part in getattr(content, "parts", []) or []:
                    text = getattr(part, "text", None)
                    if text:
                        texts.append(text)
    if not texts and hasattr(response, "text"):
        return response.text or ""
    return "\n".join(texts)


# ===== main =====
def llm_generate_gemini(
    user_prompt: str = None,
    system_prompt: str = None,
    image=None,
    model: str = "gemini-2.5-flash",
    max_tokens: int = 8192,
    img_type: str | None = None,
    config: dict = None
) -> dict:
    from google import genai
    from google.genai import types

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not set")

    client = genai.Client(api_key=api_key)
    parts = []
    # 
    # ===== IMAGE =====
    if image is not None:
        if isinstance(image, (str, Path)):
            image_path = Path(image)
            if not image_path.exists():
                raise FileNotFoundError(f"Image not found: {image_path}")
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            parts.append(types.Part.from_bytes(
                data=image_bytes,
                mime_type=get_image_media_type(image_path)
            ))
        elif isinstance(image, dict):
            if "bytes" not in image or "mime_type" not in image:
                raise ValueError("image dict must contain 'bytes' and 'mime_type'")
            parts.append(types.Part.from_bytes(
                data=image["bytes"],
                mime_type=image["mime_type"]
            ))
        elif isinstance(image, (bytes, bytearray)):
            if not img_type:
                raise ValueError("img_type required when image is raw bytes")
            parts.append(types.Part.from_bytes(
                data=image,
                mime_type=img_type
            ))
        else:
            raise TypeError(f"Unsupported image type: {type(image)}")
    # 
    # ===== TEXT =====
    if user_prompt:
        parts.append(types.Part.from_text(user_prompt))
    if not parts:
        raise ValueError("Both image and user_prompt are empty")
    # 
    # ===== CONFIG =====
    base_config = {
        "system_instruction": system_prompt if system_prompt else None,
        "max_output_tokens": max_tokens,
        "response_mime_type": "application/json" if (config and config.get("response_json_schema")) else "text/plain",
    }
    if config:
        base_config = {**base_config, **config}
    # 
    # ===== CALL =====
    response = client.models.generate_content(
        model=model,
        contents=parts,
        config=base_config
    )
    # 
    # ===== OUTPUT =====
    if config is not None and config.get("response_json_schema"):
        content = response
    else:
        content = get_gemini_output_text(response).strip()
    # 
    return {"content": content}


def vllm_generate_gemini(
    input_text: str,
    system_text: str = None,
    input_image=None,
    max_retry: int = 3,    img_type: str | None = None,
    project_dir: Path | None = None,
    config: dict = None,
):
    if project_dir is None:
        project_dir = Path(__file__).resolve().parents[1]

    image_arg = None
    if input_image:
        if isinstance(input_image, list) and input_image:
            first = input_image[0]
            image_arg = project_dir / Path(first) if isinstance(first, (str, Path)) else first
        elif isinstance(input_image, (str, Path)):
            image_arg = project_dir / Path(input_image)
        else:
            image_arg = input_image

    last_error = None

    for i in range(max_retry):
        print(f"[GEMINI] Try {i}:")
        try:
            return llm_generate_gemini(
                user_prompt=input_text,
                system_prompt=system_text,
                image=image_arg,
                model="gemini-2.5-flash",
                max_tokens=8192,
                img_type=img_type,
                config=config,
            )
        except Exception as e:
            last_error = e
            traceback.print_exc()

    return {"content": str(last_error)}




# =============================

# OPENAI

# def get_gpt_output_text(response):
#     texts = []
#     # -------- Responses API --------
#     if hasattr(response, "output"):
#         for item in response.output:
#             if getattr(item, "type", None) == "message" and getattr(item, "role", None) == "assistant":
#                 for part in getattr(item, "content", []) or []:
#                     if getattr(part, "type", None) == "output_text":
#                         texts.append(part.text)
#         return "\n".join(texts)
#     # -------- ChatCompletion API --------
#     if hasattr(response, "choices"):
#         choice = response.choices[0]
#         msg = getattr(choice, "message", None)
#         if msg is not None:
#             return msg.content
#         if hasattr(choice, "text"):
#             return choice.text
#     return ""


# def llm_generate_gpt(
#     user_prompt: str = None,
#     system_prompt: str = None,
#     image_path: str = None,
#     model: str = "gpt-5-nano",
#     max_tokens: int = 8192,
#     max_retry: int = 3,
#     structured: bool = False
# ):
#     last_error = None
#     result = {}
#     for i in range(max_retry):
#         print(f"[SYS] Num of Try: {i}:")
#         try:
#             client = OpenAI(api_key=next(key_iter))
#             # 
#             # ===== CASE 1: image → Responses API =====
#             if image_path and os.path.exists(image_path):
#                 input_content = []
#                 image_data = encode_image(image_path)
#                 media_type = get_image_media_type(image_path)
#                 input_content.append({
#                     "type": "input_image",
#                     "image_url": f"data:{media_type};base64,{image_data}"
#                 })
#                 # 
#                 input_blocks = []
#                 if system_prompt:
#                     input_blocks.append({"role": "system", "content": system_prompt})
#                 input_blocks.append({"role": "user", "content": input_content})
#                 # 
#                 print("!!! debug: using Responses API (image)")
#                 response = client.responses.create(
#                     model=model,
#                     input=input_blocks,
#                     max_output_tokens=max_tokens,
#                     reasoning=None,
#                     text=user_prompt if user_prompt else None
#                 )
#                 # 
#                 if not structured:
#                     content = get_gpt_output_text(response).strip()
#                 else:
#                     texts = []
#                     for item in getattr(response, "output", []) or []:
#                         if getattr(item, "type", None) == "message":
#                             for part in getattr(item, "content", []) or []:
#                                 if getattr(part, "type", None) == "output_text":
#                                     texts.append(part.text)
#                     if not texts:
#                         raise ValueError("No structured JSON returned by model")
#                     raw_text = "\n".join(texts).strip()
#                     content = parse_structured_json(raw_text)
#                 # 
#                 result = {"content": content}
#                 return result
#             # 
#             # ===== CASE 2: text only → Chat Completions =====
#             else:
#                 user_msg = {'role': 'user', 'content': str(user_prompt)}
#                 messages = ([{'role': 'system', 'content': str(system_prompt)}] if system_prompt is not None else []) + [user_msg]
#                 print("!!! debug: using Chat Completions")
#                 response = client.chat.completions.create(
#                     messages=messages,
#                     model=model,
#                     max_tokens=max_tokens if max_tokens is not None else 2048,
#                     logprobs=True,
#                     top_logprobs=1,
#                 )
#                 # 
#                 response_text = response.choices[0].message.content
#                 response_text_showing = f"{str(response_text)[:200]} ... {str(response_text)[-200:]}" if len(str(response_text)) > 450 else str(response_text)
#                 print(f"!!! debug: response_text: {response_text_showing}")
#                 # 
#                 if hasattr(response.choices[0], "logprobs") and response.choices[0].logprobs is not None:
#                     response_prob = ppl_from_response(response)
#                 else:
#                     response_prob = None
#                 # 
#                 if not structured:
#                     content = response_text
#                 else:
#                     content = parse_structured_json(response_text)
#                 # 
#                 result = {"content": content}
#                 if response_prob is not None:
#                     result["logprobs"] = response_prob
#                 return result
#         # 
#         except Exception as e:
#             last_error = str(e)
#             print(f"!!! debug: error: {last_error}")
#             continue
#     # 
#     return {"content": last_error}
    


# MAIN
# def llm_generate(
#     user_prompt: str,
#     system_prompt: str = None,
#     model: str = 'gpt-4o-mini',
#     image_path: str = None,
#     max_retry: int = 3,
#     max_tokens: int = 2048,
#     structured: bool = False,
#     have_log: bool = False,
# ) -> dict:
#     if "gpt" in model.lower():
#         from openai import OpenAI 
#         return llm_generate_gpt(
#             user_prompt=user_prompt,
#             system_prompt=system_prompt,
#             image_path=image_path,
#             model=model,
#             max_tokens=max_tokens,
#             max_retry=max_retry,
#             structured=structured
#         )

#     elif "gemini" in model.lower():
        
#     else:
#         raise ValueError(f"Unsupported model: {model}")
        
        
        