import base64
from pathlib import Path

from app import key_iter

import numpy as np

import traceback

# GENERAL TOOLS
def encode_image(image_path: str) -> str:
    with open(image_path, 'rb') as image_file:
        return base64.standard_b64encode(image_file.read()).decode('utf-8')

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

    
def is_path_like(x):
    return isinstance(x, (str, Path))


# GPT LLM TOOLS
def ppl_from_response(response, min_logprob=-100):
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
    return float(np.exp(-np.mean(logps)))


def llm_generate_gpt(
    user_prompt: str, 
    system_prompt: str = None, 
    model: str = 'gpt-5.4-nano', 
    max_retry: int = 3, 
    max_tokens: int = 2048,
    text_format = None,
    have_log: bool = False, 
    # **kwarg
    ) -> str:
    import openai
    
    user_msg = {'role':'user','content': str(user_prompt)}
    if system_prompt is not None:
        system_msg = {'role':'system','content':str(system_prompt)}
        messages = [system_msg, user_msg]
    else:
        messages = [user_msg]  
        
    for _ in range(max_retry):
        print(f"[SYS] Num of Try: {_}:")
        try:
            client = openai.OpenAI(api_key=next(key_iter))
            if have_log: 
                print(f"!!! debug: before response generation A: ")
                response = client.chat.completions.create(
                    messages=messages, 
                    model=model,
                    max_tokens=max_tokens if max_tokens is not None else 2048,
                    top_logprobs=1,
                    logprobs=True,
                    # **kwarg
                    )
                
                response_showing = f"{str(response)[:200]} ... {str(response)[-200:]}" if len(str(response)) > 450 else str(response)
                
                print(f"!!! debug: after response generation A, {response_showing}")
                
            else:
                print(f"!!! debug: before response generation B: ")
                response = client.chat.completions.create(messages=messages, model=model, max_tokens=max_tokens)
                response_showing = f"{str(response)[:200]} ... {str(response)[-200:]}" if len(str(response)) > 450 else str(response)
                print(f"!!! debug: after response generation B, {response_showing}")
                
            response_text = response.choices[0].message.content
            response_text_showing = f"{str(response_text)[:200]} ... {str(response_text)[-200:]}" if len(str(response_text)) > 450 else str(response_text)
            print(f"!!! debug: response_text: {response_text_showing}")
            if hasattr(response.choices[0], "logprobs") and response.choices[0].logprobs is not None:
                print(f"--- LOGPROB: ")
                # with open("tmp0202.json", "w") as g:
                #     response_dict = response.model_dump()
                #     json.dump(response_dict, g, ensure_ascii=False, indent=2)
                print(f"--- TEXT: {response_text}")
                print(f"--- Len of log content: {len(response.choices[0].logprobs.content)}")
                response_prob = ppl_from_response(response)
            else:
                response_prob = None
            print(f"!!! debug: response_prob: {response_prob}")
            return response_text, response_prob
        except Exception as e:
            error_msg = str(e)
            print(f"!!! debug: response_prob error: {error_msg}")
            continue
    return error_msg, None


# GEMINI LLM TOOLS
def llm_generate_gemini(
    system_prompt: str,
    user_prompt: str,
    image=None,
    model: str = "gemini-2.5-flash",
    max_tokens: int = 8192,
    max_retry: int = 3,
    img_type: str | None = None,
    config: dict = None
) -> str:
    from google import genai
    from google.genai import types

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not set")

    client = genai.Client(api_key=api_key)
    parts = []

    # ---- image input (at most ONE image) ----
    if image is not None:
        # 1 path-like
        if isinstance(image, (str, Path)):
            image_path = Path(image)
            if not image_path.exists():
                raise FileNotFoundError(f"Image not found: {image_path}")
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            parts.append(
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=get_image_media_type(image_path)
                )
            )

        # 2 dict payload: {"bytes": ..., "mime_type": ...}
        elif isinstance(image, dict):
            if "bytes" not in image or "mime_type" not in image:
                raise ValueError("image dict must contain 'bytes' and 'mime_type'")
            parts.append(
                types.Part.from_bytes(
                    data=image["bytes"],
                    mime_type=image["mime_type"]
                )
            )

        # 3 raw bytes / bytearray
        elif isinstance(image, (bytes, bytearray)):
            if not img_type:
                raise ValueError("img_type is required when image is raw bytes")
            parts.append(
                types.Part.from_bytes(
                    data=image,
                    mime_type=img_type
                )
            )

        else:
            raise TypeError(f"Unsupported image type: {type(image)}")

    # ---- optional user text ----
    if user_prompt:
        parts.append(types.Part.from_text(user_prompt))

    if not parts:
        raise ValueError("Both image and user_prompt are empty")

    base_config = {
            "system_instruction": system_prompt if system_prompt else None,
            "max_output_tokens": max_tokens,
            # "response_mime_type"="text/plain",
            "response_mime_type": "application/json",
        }
    
    if config:
        base_config = {**base_config, **config}
    
    for _ in range(max_retry):
        print(f"[SYS] Num of Try: {_}:")
        try:
            response = client.models.generate_content(
                model=model,
                contents=parts,
                config = base_config
            )

            if config is not None and config.get("response_json_schema", ""):
                return response
            else:
                return get_gemini_output_text(response).strip()
            
        except Exception as e:
            error_msg = str(e)
            print(f"!!! debug: response_prob error: {error_msg}")
            continue



def get_gemini_output_text(response):
    texts = []

    # new SDK method
    if hasattr(response, "candidates"):
        for cand in response.candidates or []:
            content = getattr(cand, "content", None)
            if content:
                for part in getattr(content, "parts", []) or []:
                    text = getattr(part, "text", None)
                    if text:
                        texts.append(text)

    # if given response.text
    if not texts and hasattr(response, "text"):
        return response.text or ""

    return "\n".join(texts)
    

# MAIN CALLING: with IMAGE

def vllm_generate(
    user_prompt: str,
    system_prompt: str = None,
    input_image=None,
    max_retry: int = 3,
    img_type: str | None = None,
    project_dir: Path | None = None,
    config: dict = None,
    **kwargs
):
    if project_dir is None:
        project_dir = Path(__file__).resolve().parents[1]

    image_arg = None

    if input_image:
        if isinstance(input_image, list) and input_image:
            first = input_image[0]
            if is_path_like(first):
                image_arg = project_dir / Path(first)
            else:
                image_arg = first
        elif is_path_like(input_image):
            image_arg = project_dir / Path(input_image)
        else:
            image_arg = input_image

    last_error = None

    for _ in range(max_retry):
        try:
            return llm_generate_gemini(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                image=image_arg,
                model="gemini-2.5-flash",
                max_tokens=8192,
                img_type=img_type,
                config=config,
            ), None
        except Exception as e:
            last_error = e
            traceback.print_exc()

    raise SystemError(
        f"failed to generate response with gemini: {last_error}"
    )


# MAIN CALLING: without IMAGE
def llm_generate(
    system_prompt: str,
    user_prompt: str,
    image=None,
    model: str = "gemini-2.5-flash",
    max_tokens: int = 8192,
    max_retry: int = 3,
    img_type: str | None = None,
    config: dict = None
):

        
    if "gpt" in model.lower():

    elif "gemini" in model.lower() or "gemma" in model.lower():

    else:
        raise ValueError("Unknown model for LLM segmentation")

