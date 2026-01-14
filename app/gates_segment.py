from img_utils import llm_generate_gpt, llm_generate_gemini
import json

SYSTEM_PROMPT = """You are a document layout analyzer.

Given a scanned exam page image, your task is to decide how to vertically split the page into multiple rectangular sub-images.

Rules:
- Only horizontal cuts are allowed.
- Output vertical ranges as percentages of page height.
- Overlap between adjacent ranges is allowed and encouraged if student answers may spill over.
- Ensure no content is missing; redundancy is acceptable.
- Always cover the full page from 0 to 100. 
- Vertical percentages are measured from top to bottom: 0 means the top edge of the page, 100 means the bottom edge.
- Allow one page to be a single segment (0, 100) if appropriate.
- If the page is blank or print-only (e.g., cheat sheet, cover page), return a single segment (0, 100).

Output format:
A Python list of tuples:
[(y_start, y_end), ...]

Constraints:
- 0 <= y_start < y_end <= 100
- Tuples must be sorted by y_start
- No explanation, no text, no markdown.
- Output ONLY the list.
"""

from pdf2image import convert_from_path
from pathlib import Path

# =========================

def pdf_to_images(pdf_path: str, out_dir: str, dpi: int = 300):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    pages = convert_from_path(pdf_path, dpi=dpi)
    image_paths = []

    for i, page in enumerate(pages):
        img_path = out_dir / f"page_{i:03d}.png"
        page.save(img_path, "PNG")
        image_paths.append(str(img_path))

    return image_paths

# =========================

def validate_splits(splits):
    if not isinstance(splits, list):
        raise ValueError("Splits must be a list")

    prev_start = -1
    for item in splits:
        if (
            not isinstance(item, (list, tuple)) or
            len(item) != 2
        ):
            raise ValueError(f"Invalid split item: {item}")

        y0, y1 = item
        if not (0 <= y0 < y1 <= 100):
            raise ValueError(f"Invalid range: {item}")

        if y0 < prev_start:
            raise ValueError("Splits must be sorted")

        prev_start = y0

    if splits[0][0] != 0 or splits[-1][1] != 100:
        raise ValueError("Splits must cover full page (0–100)")

# =========================

import ast

def get_vertical_splits_from_llm(
    image_path: str,
    model: str = "gpt-5-nano",
):
    with open("schema.json", "r") as f:
        schema = json.load(f)
        text = {
        "format": {
            "type": "json_schema",
            "schema": schema, 
            "strict": True,
            "name": "vertical_splits"
        }}
        
    if "gpt" in model.lower():
        raw = llm_generate_gpt(
            system_prompt=SYSTEM_PROMPT,
            user_prompt="",
            image_path=image_path,
            model=model,
            text=text,
            structured=True  
        )
    elif "gemini" in model.lower() or "gemma" in model.lower():
        raw = llm_generate_gemini(
            system_prompt=SYSTEM_PROMPT,
            user_prompt="",
            image_path=image_path,
            model=model
        )
    else:
        raise ValueError("Unknown model for LLM segmentation")

    # structured output: raw is dict
    if not isinstance(raw, dict) or "splits" not in raw:
        raise ValueError(f"Invalid structured output: {raw}")

    splits = raw["splits"]
    validate_splits(splits)
    return splits

# ========================

from PIL import Image

def crop_image_by_percentages(
    image_path: str,
    splits,
    out_dir: str,
    prefix: str
):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    img = Image.open(image_path)
    width, height = img.size

    out_paths = []

    for idx, (y0, y1) in enumerate(splits):
        top = int(height * y0 / 100.0)
        bottom = int(height * y1 / 100.0)

        crop = img.crop((0, top, width, bottom))
        out_path = out_dir / f"{prefix}_part_{idx:02d}.png"
        crop.save(out_path)
        out_paths.append(str(out_path))

    return out_paths

# =========================

def process_single_page(
    image_path: str,
    output_dir: str,
    model: str = "gpt-5-nano",
    ):
    splits = get_vertical_splits_from_llm(
        image_path=image_path,
        model=model,
    )

    page_name = Path(image_path).stem
    crop_paths = crop_image_by_percentages(
        image_path=image_path,
        splits=splits,
        out_dir=output_dir,
        prefix=page_name
    )

    return crop_paths, splits


# =========================

def process_pdf(
    pdf_path: str,
    work_dir: str,
    model: str = "gpt-5-nano",
):
    pages_dir = Path(work_dir) / f"{model}_pages"
    crops_dir = Path(work_dir) / f"{model}_crops"

    page_images = pdf_to_images(pdf_path, pages_dir)

    all_outputs = []

    splits_jsonl = Path(work_dir) / "splits.jsonl"

    for page_idx, img_path in enumerate(page_images, start=1):  # 1-based
        crop_paths, splits = process_single_page(
            image_path=img_path,
            output_dir=crops_dir,
            model=model,
        )

        all_outputs.extend(crop_paths)
        
        record = {
            "page": page_idx,
            "split": splits
        }
        with open(splits_jsonl, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return all_outputs

# =========================

import argparse
from pathlib import Path


def main(args):
    pdf_root = Path(args.pdf_dir)
    if not pdf_root.exists():
        raise FileNotFoundError(f"PDF directory not found: {pdf_root}")

    crops_root = pdf_root / f"{args.model}_crops"
    crops_root.mkdir(exist_ok=True)

    pdf_files = sorted(
            pdf_root.glob("*.pdf"),
            key=lambda p: p.stat().st_size
        )
    if not pdf_files:
        print(f"[WARN] No PDF files found in {pdf_root}")
        return

    for pdf_path in pdf_files:
        pdf_name = pdf_path.stem 
        print(f"[INFO] Processing PDF: {pdf_name}")

        pdf_crop_dir = crops_root / pdf_name
        pdf_crop_dir.mkdir(parents=True, exist_ok=True)

        work_dir = pdf_crop_dir / "_work"
        work_dir.mkdir(exist_ok=True)

        try:
            process_pdf(
                pdf_path=str(pdf_path),
                work_dir=str(work_dir),
                model=args.model,
            )

            # move crops
            generated_crops = (work_dir / f"{args.model}_crops").glob("*.png")
            for img_path in generated_crops:
                target = pdf_crop_dir / img_path.name
                img_path.replace(target)

            # move splits.jsonl if any
            splits_jsonl = work_dir / "splits.jsonl"
            if splits_jsonl.exists():
                splits_jsonl.replace(pdf_crop_dir / "splits.jsonl")

        except Exception as e:
            print(f"[ERROR] Failed to process {pdf_name}: {e}")


        import shutil
        if not args.keep_work and work_dir.exists():
            shutil.rmtree(work_dir)

    print("[INFO] All PDFs processed.")

