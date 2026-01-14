import re, os, json
from pathlib import Path
import base64
import pandas as pd
from tqdm import tqdm
from datetime import datetime

from openai import OpenAI
from dotenv import load_dotenv
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


def llm_generate_gpt(
    system_prompt: str,
    user_prompt: str,
    image_path: str = None,
    model: str = "gpt-5-nano",
    max_tokens: int = 8192,
    text=None,
    structured: bool = False
):
    api_key = os.getenv('OPENAI_API_KEY')
    client = OpenAI(api_key=api_key)

    input_content = []
    if image_path and os.path.exists(image_path):
        image_data = encode_image(image_path)
        media_type = get_image_media_type(image_path)
        input_content.append({
            "type": "input_image",
            "image_url": f"data:{media_type};base64,{image_data}"
        })

    input_blocks = []
    if system_prompt:
        input_blocks.append({"role": "system", "content": system_prompt})
    input_blocks.append({"role": "user", "content": input_content})

    response = client.responses.create(
        model=model,
        input=input_blocks,
        max_output_tokens=max_tokens,
        reasoning=None,
        text=text if text else None
    )

    if not structured:
        return get_gpt_output_text(response).strip()

    # ===== structured output parsing =====
    texts = []
    for item in getattr(response, "output", []) or []:
        if getattr(item, "type", None) == "message":
            for part in getattr(item, "content", []) or []:
                if getattr(part, "type", None) == "output_text":
                    texts.append(part.text)

    if not texts:
        raise ValueError("No structured JSON returned by model")

    raw_text = "\n".join(texts).strip()
    return parse_structured_json(raw_text)


def get_gpt_output_text(response):
    texts = []
    # -------- New Responses API --------
    if hasattr(response, "output"):
        for item in response.output:
            if getattr(item, "type", None) == "message" and getattr(item, "role", None) == "assistant":
                for part in getattr(item, "content", []) or []:
                    if getattr(part, "type", None) == "output_text":
                        texts.append(part.text)
        return "\n".join(texts)

    # -------- Legacy ChatCompletion API --------
    if hasattr(response, "choices"):
        choice = response.choices[0]
        msg = getattr(choice, "message", None)
        if msg is not None:
            return msg.content
        if hasattr(choice, "text"):
            return choice.text
    return ""
