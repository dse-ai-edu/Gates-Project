import re
import os
import json
import uuid
import shutil
import time
import traceback
from datetime import datetime
import random
import string
import pytz

from flask import render_template, request, jsonify, send_file
from flask import send_from_directory
from werkzeug.utils import secure_filename

import app.utils as utils
import app.prompts as prompts
from app.gates_segment import process_pdf
from app import app, database
# from app import s3_client
from datetime import datetime, timedelta

from pymongo import DESCENDING

from app.question_image_prompt import QUESTION_RECOGNITION, ASSESSMENT_RECOGNITION
from app.image_prompts_latest import RECOGNITION
from app.prompts import JUDGE

from app.judge import multi_agent_judge, run_score_extract, is_consistent

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TMP_DIR = BASE_DIR / "tmp"

TMP_DIR.mkdir(parents=True, exist_ok=True)

app_dir = utils.find_app_dir()
KEYWORD_PATH = app_dir / "static" / "data"/ "keyword_info.json"
#   ==================== MAIN ==================== #

#   ==================== Sample Data for Demo ==================== #

# question_this = """
# <p>Find the derivative of each of the following functions. You do not need to simplify your answers.</p>
# <p>(a) f(x) = x<sup>ln(x)</sup></p>
# """
# reference_this = """
# <p>Find the derivative of each of the following functions. You do not need to simplify your answers.</p>
# <p>(a) f(x) = x<sup>ln(x)</sup></p>
# <p><strong>Solution:</strong></p>
# <p>To find the derivative of f(x) = x<sup>ln(x)</sup>, we use logarithmic differentiation.</p>
# <p>Take the natural logarithm of both sides:</p>
# <p>ln(f(x)) = ln(x) · ln(x) = (ln(x))<sup>2</sup></p>
# <p>Differentiate both sides with respect to x:</p>
# <p>f'(x)/f(x) = 2ln(x) · (1/x)</p>
# <p>Solve for f'(x):</p>
# <p>f'(x) = f(x) · 2ln(x)/x = x<sup>ln(x)</sup> · 2ln(x)/x</p>
# <p><strong>Answer: f'(x) = x<sup>ln(x)</sup> · 2ln(x)/x</strong> or equivalently <strong>f'(x) = 2x<sup>ln(x)-1</sup>ln(x)</strong></p>
# """


def load_keywords_by_subgroup(keyword_path = KEYWORD_PATH):
    with open(keyword_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    grouped = {}
    for kw, info in raw.items():
        subgroup = info.get("subgroup")
        if subgroup is None:
            continue
        grouped.setdefault(subgroup, []).append({
            "key": kw,
            "name": info.get("name", kw),
            "group_idx": info.get("group_idx", 0),
            "short": info.get("short", "")
        })
    for subgroup, items in grouped.items():
        items.sort(key=lambda x: x["group_idx"])
    return grouped


GROUPED_KEYWORDS = load_keywords_by_subgroup()
# ==================== Page Route (returns HTML) ==================== #

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/page_1')
def page_1():
    return render_template('page_1.html',
                            subgroup1_keywords=GROUPED_KEYWORDS.get(1, []),
                            subgroup2_keywords=GROUPED_KEYWORDS.get(2, []),
                            subgroup3_keywords=GROUPED_KEYWORDS.get(3, []),
                            subgroup4_keywords=GROUPED_KEYWORDS.get(4, [])
                           )

@app.route('/page_2')
def step2():
    return render_template('page_2.html')

@app.route('/page_final')
def page_final():
    return render_template('page_final.html')

# @app.route("/segment")
# def segment_page():
#     return render_template("segment.html")

# @app.route('/tmp/<path:filename>')
# def serve_tmp(filename):
#     return send_from_directory(TMP_DIR, filename)


# @app.route('/<path:filepath>')
# def serve_uploaded_files(filepath): 
#     full_path = os.path.join(os.getcwd(), filepath)

#     if not os.path.isfile(full_path):
#         return "Not Found", 404

#     directory = os.path.dirname(full_path)
#     filename = os.path.basename(full_path)

#     return send_from_directory(directory, filename)


# ==================== API Route (System Setting) ==================== #

@app.route('/api/login', methods=['POST'])
def api_login():
    """Simple login API for the 4-page system"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    try:
        # Simple demo authentication - in production, use proper authentication
        if username and password:  # Accept any non-empty credentials for demo
            response = {
                'success': True,
                'user': username,
                'token': str(uuid.uuid4())  # Generate demo token // tid
            }
        else:
            response = {'success': False, 'message': 'Invalid credentials'}
    except:
        traceback.print_exc()
        response = {'success': False, 'message': 'Authentication error'}
    return jsonify(response)


@app.route('/api/configuration/final', methods=['POST'])
def configuration_final():
    """Save final configuration and mark system as complete"""
    data = request.get_json()
    tid = data.get('tid')
    try:
        database['comment_status'].find_one_and_update(
            {'tid': tid},
            {'$set': {
                'completed': True,
                'completed_at': datetime.utcnow(),
                'final_config': data.get('finalConfiguration', {})
            }}
        )
        response = {'success': True}
    except:
        traceback.print_exc()
        response = {'success': False}
    return jsonify(response)


# ==================== API Route (QA demo) ==================== #
@app.route('/api/demo/calculus', methods=['POST'])
def catch_demo_answer():
    data = request.get_json()
    q_index = data.get('question_index') if data else None

    if q_index is None:
        return jsonify({'success': False, 'error': 'Missing question_index'}), 400

    with open("app/static/data/calculus_qa_example.json", "r") as f:
        demo_data = json.load(f)

    q_index_str = f"q{int(q_index) + 1}"
    demo_data_this = demo_data.get(q_index_str)

    if not demo_data_this:
        return jsonify({
            'success': False,
            'answer_code_list': [],
            answer_img_list: [],
            'error': f'Question {q_index_str} not found'
        })

    answer_code_list = [
        demo_data_this[f"a{a_idx}"]["answer_code"]
        for a_idx in range(1, 6)
    ]
    
    answer_img_list = [
        demo_data_this[f"a{a_idx}"]["image"]
        for a_idx in range(1, 6)
    ]

    response = {
        'success': True,
        'answer_code_list': answer_code_list,
        'answer_img_list': answer_img_list,
        'question_code': demo_data_this["content"]
    }
    return jsonify(response)

    

# ==================== API Route (Style Setting) ==================== #
@app.route('/api/comment/update_style', methods=['POST'])
def update_style_config():
    data = request.get_json()
    tid = data.get('tid')
    try:
        if not tid:
            raise ValueError('Missing required field: tid')
        
        config_data = {
            'style_keywords': data.get('style_keywords', []),
            'feedback_templates': data.get('feedback_templates', []),
            'feedback_pattern': data.get('feedback_pattern', ''),
            'custom_rubric': data.get('custom_rubric', '')
        }
        
        existing_record = database['comment_config'].find_one({'tid': tid})
        
        if existing_record:
            # Tid exists - append new config to existing config list
            current_config_list = existing_record.get('config', [])
            current_config_list.append(config_data)
            database['comment_config'].find_one_and_update(
                {'tid': tid},
                {'$set': {
                    'config': current_config_list,
                    'updated_at': datetime.utcnow()
                }}
                )
        else:
            # Tid doesn't exist - create new record with config as list containing one dict
            new_record = {
                'tid': tid,
                'config': [config_data],
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            database['comment_config'].insert_one(new_record)

        response = {'success': True}
        
    except Exception as e:
        print(f"Error in update_style_config: {str(e)}")
        traceback.print_exc()
        response = {'success': False, 'error': str(e)}
    return jsonify(response)

@app.route('/api/comment/retrieve_style', methods=['POST'])
def retrieve_style_config():
    data = request.get_json()
    tid = data.get('tid')
    try:
        if not tid:
            raise ValueError('Missing required field: tid')
        
       # Find the record with matching tid
        existing_record = database['comment_config'].find_one({'tid': tid})
        
        if existing_record:
           # Extract the config list
            config_list = existing_record.get('config', [])
            
            if config_list and len(config_list) > 0:
               # Get the last config element
                last_config = config_list[-1]
                response = {
                    'success': True,
                    'config': last_config,
                    'message': f'Retrieved {len(config_list)} configurations'
                }
            else:
                response = {
                    'success': False,
                    'error': 'No configurations found for this tid'
                }
        else:
            response = {
                'success': False,
                'error': f'No record found for tid: {tid}'
            }
        
    except Exception as e:
        print(f"Error in retrieve_style_config: {str(e)}")
        traceback.print_exc()
        response = {'success': False, 'error': str(e)}
    
    return jsonify(response)


# def comment_generate(system_info, answer_text, question_text, reference_text, history_prompt_dict, predefined_flag = ""):
#     """Generate personalized feedback response for student answer"""
#     if predefined_flag:
#         import predefined_conf
#         predefined_data = predefined_conf.predefined_data
#         system_prompts_raw = {
#             "final": predefined_data[predefined_flag]["final"], 
#             "selected": predefined_data[predefined_flag]["selected"], 
#             "custom": predefined_data[predefined_flag]["custom"], }
#     elif history_prompt_dict:
#         system_prompts_raw = history_prompt_dict
#     else:
#         try:
#             # Extract configuration from system
#             micro_feedback = system_info.get('micro_style', {})
#             macro_feedback = system_info.get('macro_style', {})
            
#         # Get style descriptors and templates
#             style_keywords = macro_feedback.get('keywords', [])
#             feedback_templates = macro_feedback.get('templates', [])
            
#         # Get teaching style and personalization
#             teach_style = micro_feedback.get('teach_style', '')
#             teach_example = micro_feedback.get('examples', '')
#             locked_style = macro_feedback.get('locked_style', False)
            
#         # Build system prompt for feedback generation
#             system_prompts_raw = utils.parse_teaching_style(
#                 teach_style=teach_style,
#                 teach_example=teach_example,
#                 )
#         except Exception as e:
#             traceback.print_exc()
#             return {'success': False, 'error': str(e)}

#     try:
#         # Build user prompt with student answer
#         system_prompt = system_prompts_raw['final']
#         custom_prompt = system_prompts_raw['custom'] if system_prompts_raw.get('custom', '') else None
#         user_prompt = utils.parse_teaching_text(
#             question=question_text + "\n ## Reference Answer is: " + reference_text,
#             answer=answer_text,
#             style_keywords=style_keywords,
#             feedback_templates=feedback_templates,
#             )
        
#        # Generate feedback using LLM
#         feedback_text, feedback_prob = utils.llm_generate(
#             input_text=user_prompt,
#             system_text=system_prompt,
#             model='gpt-4o',
#             temperature=0.7, 
#             max_tokens=750,
#             logprobs=True
#         )
        
#         return {
#             'success': True,
#             'feedback_text': feedback_text,
#             'feedback_prob': feedback_prob,
#             'style_keywords': style_keywords,
#             'feedback_templates': feedback_templates,
#             'teach_style': teach_style,
#             'teach_example': teach_example,
#             'system_prompt': system_prompt,
#             'selected_prompt': system_prompts_raw.get('selected', ""),
#             'custom_prompt': custom_prompt
#         }
        
#     except Exception as e:
#         traceback.print_exc()
#         print(system_prompts_raw)
#         return {'success': False, 'error': str(e)}


def comment_generate(system_info, answer_text, question_text, reference_text, history_prompt_dict, predefined_flag = ""):
    try:
        style_keywords = system_info.get('style_keywords', [])
        feedback_templates = system_info.get('feedback_templates', [])
        feedback_pattern = system_info.get('feedback_pattern', "")
        custom_rubric = system_info.get('custom_rubric', "")
        locked_style = system_info.get('locked_style', False)
        
        print(f"debug: before judgement")
        judge_input_text = f"# Question:\n{question_text}\n\n# Assessment Rubric:\n{reference_text}\n\n# Student Answer:\n{answer_text}\n\n"
        grading_result = multi_agent_judge(
            base_prompt=judge_input_text,
            system_prompt=JUDGE, 
            )
        
        if grading_result["pass"] == False:
            return {
                "success": True, 
                'feedback_text': "We can not  Process this answer, please check the question and involve human experts in grading work.",
                'feedback_prob': None,
                'style_keywords': style_keywords,
                'feedback_templates': feedback_templates,
                'feedback_pattern': feedback_pattern,
                'custom_rubric': custom_rubric,
                "grade_success": True,
                "grade": None,
                }
            
        print(f"debug: before grading extraction")
        full_score = run_score_extract(
                            user_prompt = f"# Grading Rubric:\n```\n{reference_text}\n```"
                            )
        
        if is_consistent(full_score, grading_result['score'], 0.25):
            return {
                'success': True,
                'feedback_text': "Congratulations! The answer fully meets the problem requirements and demonstrates a correct understanding of the task.",
                'feedback_prob': None,
                'style_keywords': style_keywords,
                'feedback_templates': feedback_templates,
                'feedback_pattern': feedback_pattern,
                'custom_rubric': custom_rubric,
                "grade_success": True, 
                "grade": grading_result['score'],
                }
            
            
        print(f"debug: before parse_feedback_pattern")
        pattern_dict = utils.parse_feedback_pattern(
            feedback_pattern=feedback_pattern,
            custom_rubric=custom_rubric,
            )
        
        pattern_key = pattern_dict.get("pattern_key", None)
        pattern_body = pattern_dict.get("pattern_body", None)
        print(f"debug: selected feedback_pattern: `{pattern_key}`; `{str(pattern_body)[:200]}`")
        
        
        if reference_text is not None and len(reference_text.strip()) > 0:
            question_text = question_text + "\n ## Rubric: " + reference_text
            
        if grading_result.get("reasoning", None):
            question_text += f"\n ## Socre of this Answer: {grading_result.get('score', 'N/A')}\n"
            question_text += f"## Reasons for Grading: {grading_result.get('reasoning', '')}" 
            
        answer_text = answer_text.strip()
        
        user_prompt = utils.parse_teaching_text(
            question=question_text,
            answer=answer_text,
            style_keywords=style_keywords,
            feedback_templates=feedback_templates,
            )
        
        print(f"debug: before utils.llm_generate")
        # Generate feedback using LLM
        feedback_text, feedback_prob = utils.llm_generate(
            input_text=user_prompt,
            system_text=pattern_body,
            model='gpt-4o-mini',
            max_tokens=2048,
            have_log=True
            )
        
        return {
                'success': True,
                'feedback_text': feedback_text,
                'feedback_prob': feedback_prob,
                'style_keywords': style_keywords,
                'feedback_templates': feedback_templates,
                'feedback_pattern': feedback_pattern,
                'custom_rubric': custom_rubric,
                'pattern_body': pattern_body,
                "grade_success": True, 
                "grade": grading_result['score'],
            }
        
    except Exception as e:
        traceback.print_exc()
        print(system_info)
        return {'success': False, 'error': str(e)}
    
@app.route('/api/comment/submit', methods=['POST'])
def comment_submit():
    """Generate personalized feedback response for student answer (no scoring involved)"""

    # ===============================
    # 1. Read from FormData (NOT JSON)
    # ===============================
    tid = request.form.get('tid')
    archive_tid = request.form.get('archive_tid', "").strip()
    aid = request.form.get('aid', str(uuid.uuid4()))
    qid = request.form.get('qid')

    question_this = request.form.get("question", "")
    assessment_this = request.form.get("assessment", "")
    answer_text = request.form.get("answer", "")
    predefined_flag = request.form.get("predefined_flag", "")

    history_prompt_dict = None

    try:
        # ===============================
        # 2. Load system configuration
        # ===============================
        if archive_tid:
            history_record = database['comment_config'].find_one({'tid': archive_tid})
            if not history_record:
                raise ValueError(f'Archive system not found: {archive_tid}')

            history_system_info = history_record['config']
            system_info = (
                history_system_info[-1]
                if isinstance(history_system_info, list)
                else history_system_info
            )

            try:
                history_prompt_record = database['comment'].find_one(
                    {'tid': archive_tid},
                    sort=[('_id', -1)]
                )
                history_prompt_dict = history_prompt_record['system_config']
            except Exception:
                history_prompt_dict = None

        else:
            current_record = database['comment_config'].find_one({'tid': tid})
            if not current_record:
                raise ValueError(f'Feedback system not found: {tid}')

            current_system_info = current_record['config']
            system_info = (
                current_system_info[-1]
                if isinstance(current_system_info, list)
                else current_system_info
            )

        # ===============================
        # 3. Validation
        # ===============================
        if not answer_text.strip():
            return jsonify({
                'success': False,
                'error': 'Student answer cannot be empty'
            })

        # ===============================
        # 4. Generate feedback
        # ===============================
        generate_result = comment_generate(
            system_info=system_info,
            answer_text=answer_text,
            question_text=question_this,
            reference_text=assessment_this,   # ← assessment = reference
            history_prompt_dict=history_prompt_dict,
            predefined_flag=predefined_flag
        )

        if not generate_result['success']:
            return jsonify(generate_result)

        # ===============================
        # 5. Store feedback in database
        # ===============================
        max_attempt_record = database['comment'].find_one(
            {'tid': tid},
            sort=[('attempt_id', -1)]
        )

        next_attempt_id = (
            max_attempt_record.get('attempt_id', -1) + 1
            if max_attempt_record else 0
        )

        database['comment'].insert_one({
            'tid': tid,
            'aid': aid,
            'question': qid,
            'attempt_id': next_attempt_id,
            'student_answer': answer_text,
            'generated_response': generate_result['feedback_text'],
            'system_config': {
                'style_keywords': generate_result['style_keywords'],
                'feedback_templates': generate_result['feedback_templates'],
                'feedback_pattern': generate_result['feedback_pattern'],
                'custom_rubric': generate_result['custom_rubric'],
                'pattern_body': generate_result['pattern_body'],
            },
            'feedback_prob': generate_result['feedback_prob'],
            'generated_at': datetime.utcnow()
        })

        response = {
            'success': True,
            'tid': tid,
            'aid': aid,
            'attempt_id': next_attempt_id
        }

    except Exception as e:
        traceback.print_exc()
        response = {'success': False, 'error': str(e)}

    return jsonify(response)



@app.route('/api/comment/load', methods=['GET'])
def comment_load():
    """Load generated feedback response by answer ID"""
    tid = request.args.get('tid')
    attempt_id = request.args.get('attempt_id')
    print(">>>1>>>", tid, attempt_id)
    with open(KEYWORD_PATH, "r", encoding="utf-8") as f:
        keyword_info = json.load(f)
        
    try:
        print(f"want to find one record with tid {tid} and atmp_id {attempt_id}")
        result = database['comment'].find_one({'tid': tid, 'attempt_id': int(attempt_id)})
        response_text = result.get('generated_response', '')
        
        system_config = result.get('system_config', dict())
        
        style_keywords = system_config.get('style_keywords', [])
        style_keywords = style_keywords.split(",") if isinstance(style_keywords, str) else style_keywords
        style_keywords_print = [keyword_info.get(kw.strip(), {}).get('name', "") for kw in style_keywords]
        style_keywords_text = "; ".join(s.strip() for s in style_keywords_print if s.strip())
        
        feedback_templates = system_config.get('feedback_templates', [])
        
        feedback_pattern = system_config.get('feedback_pattern', '')
        pattern_custom_flag = feedback_pattern=="" or "custom" in feedback_pattern.lower()
        style_pattern_text = "Custom" if pattern_custom_flag else feedback_pattern
        
        custom_rubric = system_config.get('custom_rubric', '')
        
        pattern_body = system_config.get('pattern_body', '')

        if response_text:
            # Return the generated response (no scoring)
            certainty_score = result.get('feedback_prob', '-1')

            # Format as HTML for display
            formatted_response = utils.format_response_html(
                response_text=response_text,
                certainty_score=certainty_score,
            )
            # print(f">>>3>>>{formatted_response}")
            # print(f">>>4>>>{response_text}")
            # print(f">>>5>>>{certainty_score}")
            
            return_data = {'success': True,
                            'response': formatted_response,
                            # 'response_text': response_text,
                            'keyword_text': str(style_keywords_text),
                            'template_text': str(feedback_templates),
                            'pattern_text': str(style_pattern_text),
                            'custom_rubric': str(custom_rubric),
                            'pattern_body': str(pattern_body)
                        }

            return jsonify(return_data)
        return jsonify({'success': False, 'response': None})
    except:
        traceback.print_exc()
        return jsonify({'success': False, 'response': None})

# ==================== Utility API Routes ==================== #

@app.route('/api/session/create', methods=['POST'])
def session_create():
    """Create a new session for the feedback system"""
    try:
        session_id = str(uuid.uuid4())
        # Could store session info in database if needed
        response = {'success': True, 'session_id': session_id}
    except:
        traceback.print_exc()
        response = {'success': False}
    return jsonify(response)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'feedback-generation-system'
    })
    
# ==================== segment ==================== #

def clear_tmp():
    import shutil
    for f in TMP_DIR.iterdir():
        path = os.path.join(TMP_DIR, f)
        if p.is_file():
            p.unlink()
        else:
            shutil.rmtree(p)

@app.route("/api/preprocess/upload_pdf", methods=["POST"])
def upload_pdf():
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "msg": "No file uploaded"})

        file = request.files["file"]
        filename = secure_filename(file.filename)

        if not filename.lower().endswith(".pdf"):
            return jsonify({"success": False, "msg": "Not a PDF file"})

        clear_tmp()

        pdf_path = f"tmp/{filename}"
        file.save(pdf_path)

        return jsonify({"success": True, "pdf_path": pdf_path})
    except:
        traceback.print_exc()
        return jsonify({"success": False, "msg": "Upload failed"})


@app.route("/api/preprocess/segment", methods=["POST"])
def segment_pdf():
    try:
        data = request.json
        pdf_path = data.get("pdf_path")

        if not pdf_path or not os.path.exists(pdf_path):
            return jsonify({"success": False, "msg": "PDF not found"})

        image_paths = process_pdf(pdf_path=pdf_path)
        print(f"[INFO] Generated ``{len(image_paths)}`` crops")
        return jsonify({
            "success": True,
            "images": image_paths
        })
    except:
        traceback.print_exc()
        return jsonify({"success": False})


@app.route("/api/preprocess/segment_download", methods=["POST"])
def download_all():
    try:
        zip_path = TMP_DIR / "figures.zip"   

        if not zip_path.exists():
            return jsonify({"success": False})

        # Central Time (US)
        tz = pytz.timezone("US/Central")
        now = datetime.now(tz)
        time_str = now.strftime("%y%m%d_%H%M%S")

        rand_str = "".join(random.choices(string.ascii_lowercase, k=6))
        download_name = f"{time_str}_{rand_str}.zip"

        return send_file(
            zip_path,               
            as_attachment=True,
            download_name=download_name
        )

    except Exception:
        traceback.print_exc()
        return jsonify({"success": False})



@app.route('/api/image/convert', methods=['POST'])
def api_image_convert():
    """
    Image / PDF recognition endpoint.
    Accepts: multipart/form-data with field `file`
    Returns: { success: true, text: "..." }
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400

        file = request.files['file']
        
        input_type = request.form.get('type', '').lower()
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Empty filename'}), 400

        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[-1].lower()

        if ext not in ('png', 'jpg', 'jpeg', 'pdf'):
            return jsonify({'success': False, 'error': 'Unsupported file type'}), 400

        # -------------------------------------------------
        # Save file under app/tmp (must be inside ./app/)
        # -------------------------------------------------
        tmp_dir = os.path.join(app_dir, 'tmp')
        os.makedirs(tmp_dir, exist_ok=True)

        uid = uuid.uuid4().hex
        saved_name = f'{uid}.{ext}'
        saved_path = os.path.join(tmp_dir, saved_name)

        file.save(saved_path)

        # -------------------------------------------------
        # Prepare image list for vllm_generate
        # vllm_generate expects paths relative to ./app/
        # -------------------------------------------------
        input_images = []

        if ext == 'pdf':
            try:
                image_paths = process_pdf(pdf_path=saved_path)
                if not image_paths:
                    return jsonify({'success': False, 'error': 'Empty PDF after processing'}), 500
                # only first page
                input_images = [image_paths[0]]
            except Exception:
                traceback.print_exc()
                return jsonify({'success': False, 'error': 'Failed to process PDF'}), 500
        else:
            rel_path = os.path.relpath(saved_path, app_dir)
            input_images = [rel_path]


        # -------------------------------------------------
        # Call vLLM for OCR
        # -------------------------------------------------

        if input_type == 'question':
            system_prompt = QUESTION_RECOGNITION
        elif input_type == 'assessment':
            system_prompt = ASSESSMENT_RECOGNITION
        elif input_type == 'answer':
            system_prompt = RECOGNITION
        else:
            system_prompt = QUESTION_RECOGNITION
            
        text, _ = utils.vllm_generate(
            input_text="",
            system_text=system_prompt,
            input_image=input_images,
            temperature=0.0
        )

        return jsonify({
            'success': True,
            'text': text.strip()
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
