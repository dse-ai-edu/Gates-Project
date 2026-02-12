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

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TMP_DIR = BASE_DIR / "tmp"

TMP_DIR.mkdir(parents=True, exist_ok=True)

app_dir = utils.find_app_dir()
KEYWORD_PATH = app_dir / "static" / "data"/ "keyword_info.json"
#   ==================== MAIN ==================== #

#   ==================== Sample Data for Demo ==================== #


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


def comment_generate(system_info, answer_text, question_text, reference_text, history_prompt_dict, predefined_flag = ""):
    try:
        style_keywords = system_info.get('style_keywords', [])
        feedback_templates = system_info.get('feedback_templates', [])
        feedback_pattern = system_info.get('feedback_pattern', "")
        custom_rubric = system_info.get('custom_rubric', "")
        locked_style = system_info.get('locked_style', False)
        
        print(f"debug: before parse_feedback_pattern")
        pattern_dict = utils.parse_feedback_pattern(
            feedback_pattern=feedback_pattern,
            custom_rubric=custom_rubric,
            )
        
        pattern_key = pattern_dict.get("pattern_key", None)
        pattern_body = pattern_dict.get("pattern_body", None)
        print(f"debug: selected feedback_pattern: `{pattern_key}`; `{str(pattern_body)[:200]}`")
        
        
        if reference_text is not None and len(reference_text.strip()) > 0:
            question_text = question_text + "\n ## Reference Answer(s): " + reference_text
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
            }
        
    except Exception as e:
        traceback.print_exc()
        print(system_info)
        return {'success': False, 'error': str(e)}
    
    
@app.route('/api/comment/submit', methods=['POST'])
def comment_submit():
    """Generate personalized feedback response for student answer (no scoring involved)"""
    data = request.get_json()
    tid = data.get('tid')
    archive_tid = data.get('archive_tid', "").strip()
    aid = data.get('aid', str(uuid.uuid4()))
    qid = data.get('qid')
    answer_text = data.get("student_answer", "")
    question_this = data.get("question", "")
    predefined_flag = data.get("predefined_flag", "")
    
    history_prompt_dict = None
    
    try:
       # Determine which system_info to use
        if archive_tid:
            history_record = database['comment_config'].find_one({'tid': archive_tid})
            if not history_record:
                raise ValueError(f'Archive system not found: {archive_tid}')
            history_system_info = history_record['config']
            system_info = history_system_info[-1] if isinstance(history_system_info, list) else history_system_info

            try:
                history_prompt_record = database['comment'].find_one({'tid': archive_tid}, sort=[('_id', -1)])
                history_prompt_dict = history_prompt_record['system_config']
            except:
                history_prompt_dict = None
        else:
            current_record = database['comment_config'].find_one({'tid': tid})
            if not current_record:
                raise ValueError(f'Feedback system not found: {tid}')
            current_system_info = current_record['config']
            system_info = current_system_info[-1] if isinstance(current_system_info, list) else current_system_info
        
        if not answer_text.strip():
            return jsonify({'success': False, 'error': 'Student answer cannot be empty'})
        
       # Generate feedback
        generate_result = comment_generate(
            system_info=system_info,
            answer_text=answer_text,
            question_text=question_this,
            reference_text=reference_this,
            history_prompt_dict = history_prompt_dict,
            predefined_flag = predefined_flag
        )
        
        if not generate_result['success']:
            return jsonify(generate_result)
        
       # Store feedback in database
        max_attempt_record = database['comment'].find_one(
            {'tid': tid},
            sort=[('attempt_id', -1)]
        )
        
        next_attempt_id = (max_attempt_record.get('attempt_id', -1) + 1) if max_attempt_record else 0

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
        
        response = {'success': True, 'tid': tid, 'aid': aid, 'attempt_id': next_attempt_id}
            
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
            certainty_score = result.get('feedback_prob', '-1')

            # Format as HTML for display
            formatted_response = utils.format_response_html(
                response_text=response_text,
                certainty_score=certainty_score,
            )

            
            return_data = {'success': True,
                            'response': formatted_response,
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
