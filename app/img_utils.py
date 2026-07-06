import re, os, json
from pathlib import Path
import base64

from dotenv import load_dotenv

from app.config import Config
#=========================
load_dotenv()

#=========================
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


def parse_structured_json(text: str):
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError(f"No JSON object found in: {text}")

    json_str = match.group(0)
    try:
        return json.loads(json_str)
    except Exception as e:
        raise ValueError(f"Failed to parse JSON: {json_str}") from e


def llm_generate_gemini(
    system_prompt: str,
    user_prompt: str,
    image_path: str = None,
    model: str = Config.GEMINI_MODEL_VISION,
    max_tokens: int = 8192,
    response_schema: dict = None,
):
    from google import genai
    from google.genai import types

    api_key = os.getenv("GOOGLE_API_KEY")

    parts = []
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        parts.append(
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=get_image_media_type(image_path)
            )
        )

    if user_prompt:
        parts.append(types.Part.from_text(text=user_prompt))

    config = {
        "system_instruction": system_prompt if system_prompt else None,
        "max_output_tokens": max_tokens,
        "response_mime_type": "application/json",
    }
    if response_schema is not None:
        config["response_json_schema"] = response_schema

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=parts,
        config=config,
    )

    if response_schema is not None:
        return parse_structured_json(get_gemini_output_text(response))
    return get_gemini_output_text(response).strip()


def get_gemini_output_text(response):
    texts = []
    # -------- new SDK method --------
    if hasattr(response, "candidates"):
        for cand in response.candidates or []:
            content = getattr(cand, "content", None)
            if content:
                for part in getattr(content, "parts", []) or []:
                    text = getattr(part, "text", None)
                    if text:
                        texts.append(text)
        if texts:
            return "\n".join(texts)

    # -------- if given response.text --------
    if hasattr(response, "text"):
        return response.text or ""
    return ""
