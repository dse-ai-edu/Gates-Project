import os
import json
import random
import string
import hashlib
import traceback

from datetime import datetime
from pathlib import Path

import pytz

from bson import Binary, ObjectId
from pymongo.errors import DuplicateKeyError

from flask import (
    request,
    jsonify,
    send_file,
    Response,
    abort,
)

from werkzeug.utils import secure_filename

from app import database

from flask import Blueprint
bp_image = Blueprint(
    "bp_image",
    __name__,
)


from app.config import (
    TMP_DIR,
    DEFAULT_MODEL,
)

from app.segment import process_pdf

from app.image_prompts import (
    QUESTION_RECOGNITION,
    ASSESSMENT_RECOGNITION,
    ANSWER_RECOGNITION,
    SOLUTION_REJECT_PRMPT,
)

from app.llm_utils import llm_generate

from app.image_post_process_utils import (
    run_image_post_process_llm,
)

from app.utils import find_app_dir


app_dir = find_app_dir()


# ====================
# Upload PDF
# ====================

@bp_image.route(
    "/api/preprocess/upload_pdf",
    methods=["POST"],
)
def upload_pdf():

    try:

        if "file" not in request.files:

            return jsonify({
                "success": False,
                "msg": "No file uploaded",
            })

        file = request.files["file"]

        filename = secure_filename(
            file.filename
        )

        if not filename.lower().endswith(
            ".pdf"
        ):

            return jsonify({
                "success": False,
                "msg": "Not a PDF file",
            })

        def clear_tmp():

            import shutil

            for f in TMP_DIR.iterdir():

                p = Path(TMP_DIR) / f

                if p.is_file():

                    p.unlink()

                else:

                    shutil.rmtree(p)

        clear_tmp()

        pdf_path = f"tmp/{filename}"

        file.save(pdf_path)

        return jsonify({
            "success": True,
            "pdf_path": pdf_path,
        })

    except Exception as e:

        traceback.print_exc()

        return jsonify({
            "success": False,
            "msg": str(e),
        })


# ====================
# Segment PDF
# ====================

@bp_image.route(
    "/api/preprocess/segment",
    methods=["POST"],
)
def segment_pdf():

    try:

        data = request.json

        pdf_path = data.get("pdf_path")

        if (
            not pdf_path
            or not os.path.exists(pdf_path)
        ):

            return jsonify({
                "success": False,
                "msg": "PDF not found",
            })

        image_paths = process_pdf(
            pdf_path=pdf_path
        )

        print(
            f"[INFO] Generated "
            f"{len(image_paths)} crops"
        )

        return jsonify({
            "success": True,
            "images": image_paths,
        })

    except Exception as e:

        traceback.print_exc()

        return jsonify({
            "success": False,
            "msg": str(e),
        })


# ====================
# Download Segments
# ====================

@bp_image.route(
    "/api/preprocess/segment_download",
    methods=["POST"],
)
def download_all():

    try:

        zip_path = TMP_DIR / "figures.zip"

        if not zip_path.exists():

            return jsonify({
                "success": False,
            })

        tz = pytz.timezone("US/Central")

        now = datetime.now(tz)

        time_str = now.strftime(
            "%y%m%d_%H%M%S"
        )

        rand_str = "".join(
            random.choices(
                string.ascii_lowercase,
                k=6,
            )
        )

        download_name = (
            f"{time_str}_{rand_str}.zip"
        )

        return send_file(
            zip_path,
            as_attachment=True,
            download_name=download_name,
        )

    except Exception as e:

        traceback.print_exc()

        return jsonify({
            "success": False,
            "msg": str(e),
        })


# ====================
# Image Convert
# ====================

@bp_image.route(
    "/api/image/convert",
    methods=["POST"],
)
def api_image_convert():

    api_output = {
        "success": False,
        "error": "",
        "asset_id": "",
        "sha256": "",
        "text": "",
        "status": 0,
    }

    try:

        if "file" not in request.files:

            return jsonify({
                "success": False,
                "error": "No file uploaded",
            }), 400

        file = request.files["file"]

        input_type = (
            request.form
            .get("type", "")
            .lower()
        )

        allow_reject = (
            request.form
            .get("allow_reject", "no")
            .strip()
            .lower()
        )

        allow_reject = (
            True
            if (
                "yes" in allow_reject
                or "1" in allow_reject
            )
            else False
        )

        if file.filename == "":

            api_output["error"] = (
                "Empty filename"
            )

            return jsonify(api_output), 400

        filename = secure_filename(
            file.filename
        )

        ext = filename.rsplit(
            ".",
            1,
        )[-1].lower()

        if ext not in (
            "png",
            "jpg",
            "jpeg",
            "pdf",
        ):

            api_output["error"] = (
                "Unsupported file type"
            )

            return jsonify(api_output), 400

        file_bytes = file.read()

        content_type = file.mimetype

        sha256 = hashlib.sha256(
            file_bytes
        ).hexdigest()

        asset_doc = database["assets"].find_one({
            "sha256": sha256,
        })

        if asset_doc:

            asset_id = asset_doc["_id"]

            if not asset_doc.get("data"):

                database["assets"].update_one(
                    {"_id": asset_id},
                    {
                        "$set": {
                            "data": Binary(file_bytes),
                            "content_type": content_type,
                            "ext": ext,
                            "updated_at": datetime.utcnow(),
                        }
                    }
                )

                asset_doc = (
                    database["assets"]
                    .find_one({"_id": asset_id})
                )

        else:

            asset_doc = {
                "filename": filename,
                "sha256": sha256,
                "ext": ext,
                "content_type": content_type,
                "data": Binary(file_bytes),
                "created_at": datetime.utcnow(),
            }

            try:

                result = (
                    database["assets"]
                    .insert_one(asset_doc)
                )

                asset_id = result.inserted_id

            except DuplicateKeyError:

                asset_doc = (
                    database["assets"]
                    .find_one({"sha256": sha256})
                )

                asset_id = asset_doc["_id"]

        asset_doc = database["assets"].find_one({
            "_id": asset_id,
        })

        if ext == "pdf":

            tmp_dir = os.path.join(
                app_dir,
                "tmp",
            )

            os.makedirs(
                tmp_dir,
                exist_ok=True,
            )

            saved_name = (
                f"{asset_id}_{sha256[:8]}.pdf"
            )

            saved_path = os.path.join(
                tmp_dir,
                saved_name,
            )

            if not os.path.exists(saved_path):

                with open(saved_path, "wb") as f:

                    f.write(asset_doc["data"])

            try:

                # Only the FIRST page is needed for recognition. Render just
                # page 1 instead of process_pdf(), which renders AND
                # LLM-segments EVERY page -- the main reason PDF conversion was
                # slow enough to risk timeouts.
                from pdf2image import convert_from_path

                first_pages = convert_from_path(
                    saved_path,
                    dpi=200,
                    first_page=1,
                    last_page=1,
                )

                if not first_pages:

                    api_output["error"] = (
                        "Empty PDF after processing"
                    )

                    return jsonify(
                        api_output
                    ), 500

                first_page_path = os.path.join(
                    tmp_dir,
                    f"{asset_id}_{sha256[:8]}_p1.png",
                )

                first_pages[0].save(
                    first_page_path,
                    "PNG",
                )

                input_image = first_page_path

            except Exception:

                traceback.print_exc()

                api_output["error"] = (
                    "Failed to process PDF"
                )

                return jsonify(
                    api_output
                ), 500

        else:

            input_image = {
                "bytes": asset_doc["data"],
                "mime_type": (
                    asset_doc.get(
                        "content_type"
                    )
                    or content_type
                ),
            }

        api_output["asset_id"] = str(asset_id)

        api_output["sha256"] = sha256

        text_format = None

        if input_type == "question":

            print(
                "USING PROMPT: "
                "QUESTION_RECOGNITION"
            )

            system_prompt = (
                QUESTION_RECOGNITION
            )

        elif input_type == "assessment":

            from app.data_structure import (
                RubricOutput,
            )

            print(
                "USING PROMPT: "
                "ASSESSMENT_RECOGNITION"
            )

            system_prompt = (
                ASSESSMENT_RECOGNITION
            )

            text_format = RubricOutput

        elif input_type == "answer":

            print(
                "USING PROMPT: "
                "ANSWER_RECOGNITION"
            )

            system_prompt = (
                ANSWER_RECOGNITION
            )

        else:

            print(
                "USING PROMPT: "
                "QUESTION_RECOGNITION"
            )

            system_prompt = (
                QUESTION_RECOGNITION
            )

        if (
            allow_reject
            and input_type == "answer"
        ):

            system_prompt += (
                SOLUTION_REJECT_PRMPT
            )

        output = llm_generate(
            user_prompt="",
            system_prompt=system_prompt,
            image=input_image,
            img_type=content_type,
            text_format=text_format,
        )

        if input_type == "assessment":

            from app.data_structure import (
                RubricOutput,
            )

            rubric_obj = output.obj

            rubric_list = list(
                rubric_obj.rubrics
            )

            rubric_dict = {
                f"rubric {idx+1}": {
                    "points": rbrc.points,
                    "content": rbrc.content,
                }
                for idx, rbrc
                in enumerate(rubric_list)
            }

            full_score = sum(
                max(item["points"], 0)
                for item
                in rubric_dict.values()
            )

            rubric_dict["Full Score"] = (
                round(full_score, 2)
            )

            processed_text = json.dumps(
                rubric_dict,
                indent=2,
                ensure_ascii=False,
            )

            api_output["text"] = (
                processed_text
            )

        else:

            output_text = (
                output.text.strip()
                if output.text
                else ""
            )

            processed_text = ""

            if (
                allow_reject
                and input_type == "answer"
            ):

                print(
                    "[INFO] running in "
                    "reject-able image "
                    "recognition model."
                )

                processed_output = (
                    run_image_post_process_llm(
                        user_text=output_text,
                        model=DEFAULT_MODEL,
                    )
                )

                if int(
                    processed_output.get(
                        "flag",
                        0,
                    )
                ) == 0:

                    api_output["success"] = (
                        False
                    )

                    api_output["error"] = (
                        "Image Cannot Be Processed"
                    )

                    api_output["status"] = 2

                    return jsonify(
                        api_output
                    ), 400

                else:

                    processed_text = (
                        processed_output
                        .get("text", "")
                        .strip()
                    )

            safe_text = (
                processed_text.strip()
                or output_text.strip()
            )

            safe_text = safe_text.replace(
                "\x08",
                "\\",
            )

            api_output["text"] = safe_text

        api_output["success"] = True

        api_output["status"] = 1

        print(
            f"IMAGE TEXT: "
            f"{api_output['text']}"
        )

        return jsonify(api_output)

    except Exception as e:

        traceback.print_exc()

        return jsonify({
            "success": False,
            "error": "Failed to process the image. Please try again.",
        }), 500


# ====================
# Asset
# ====================

@bp_image.route("/asset/<asset_id>")
def get_asset(asset_id):

    asset = database["assets"].find_one(
        {"_id": ObjectId(asset_id)},
        {
            "data": 1,
            "content_type": 1,
        },
    )

    if not asset:
        abort(404)

    return Response(
        asset["data"],
        mimetype=asset.get(
            "content_type",
            "application/octet-stream",
        ),
        headers={
            "Cache-Control":
            "public, max-age=31536000"
        },
    )