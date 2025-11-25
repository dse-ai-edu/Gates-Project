import re
import os
import uuid
import time
import traceback

from flask import render_template, request, jsonify

import uuid
import app.utils as utils
import app.prompts as prompts
from app import app, database, s3_client
from datetime import datetime, timedelta

from pymongo import DESCENDING

# ==================== Page Route (returns HTML) ==================== #

@app.route('/')
@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/step1')
def step1():
    return render_template('step1.html')

@app.route('/step2')
def step2():
    return render_template('step2.html')

@app.route('/step_final')
def step_final():
    return render_template('step_final.html')


# ==================== API Route (returns JSON) ==================== #

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
                'token': str(uuid.uuid4())  # Generate demo token
            }
        else:
            response = {'success': False, 'message': 'Invalid credentials'}
    except:
        traceback.print_exc()
        response = {'success': False, 'message': 'Authentication error'}
    return jsonify(response)

# @app.route('/api/task/create', methods=['POST'])
# def task_create():
#     """Create or update feedback system configuration"""
#     data = request.get_json()
#     tid = data.get('tid')
#     name = data.get('name')
#     desc = data.get('desc')
#     try:
#         if not database['feedback_system'].find_one({'tid': tid}):
#             database['feedback_system'].insert_one({
#                 'tid': tid, 
#                 'name': name, 
#                 'desc': desc,
#                 'created_at': datetime.utcnow(),
#                 'updated_at': datetime.utcnow()
#             })
#         else:
#             database['feedback_system'].find_one_and_update(
#                 {'tid': tid}, 
#                 {'$set': {
#                     'name': name, 
#                     'desc': desc,
#                     'updated_at': datetime.utcnow()
#                 }}
#             )    
#         response = {'success': True}
#     except:
#         traceback.print_exc()
#         response = {'success': False}
#     return jsonify(response)

# @app.route('/api/task/show', methods=['POST'])
# def task_show():
#     """Show available feedback systems"""
#     data = request.get_json()
#     user = data.get('user')
#     try:
#         task_list = database['feedback_system'].find(
#             {'tid': {'$exists': True}}, 
#             {'tid': 1, 'name': 1, 'desc': 1, '_id': 0}
#         ).to_list()
#         response = {'task_list': task_list}
#     except:
#         traceback.print_exc()
#         response = {}
#     return jsonify(response)

# @app.route('/api/section/save', methods=['POST'])
# def section_save():
#     """Save configuration data from step1 and step2"""
#     data = request.get_json()
#     try:
#         database['feedback_system'].find_one_and_update(
#             {'tid': data.get('tid')}, 
#             {'$set': {**data, 'updated_at': datetime.utcnow()}},
#             upsert=True
#         )
#         response = {'success': True}
#     except:
#         traceback.print_exc()
#         response = {'success': False}
#     return jsonify(response)

# @app.route('/api/section/load', methods=['POST'])
# def section_load():
#     """Load configuration data for step1 and step2"""
#     data = request.get_json()
#     section = data.get('section')
#     response = {}
#     try:
#         system_info = database['feedback_system'].find_one({'tid': data.get('tid')})
#         if system_info:
#             if section in ['base_style', 'macro_feedback']:
#                 response = {'info': system_info.get(section, {})}
#             else:
#                 response = {'info': {}}
#     except:
#         traceback.print_exc()
#     return jsonify(response)

@app.route('/api/configuration/final', methods=['POST'])
def configuration_final():
    """Save final configuration and mark system as complete"""
    data = request.get_json()
    tid = data.get('tid')
    try:
        database['feedback_system'].find_one_and_update(
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

@app.route('/api/response/submit', methods=['POST'])
def answer_respond():
    """Generate personalized feedback response for student answer (no scoring involved)"""
    data = request.get_json()
    tid = data.get('tid')
    aid = data.get('aid', str(uuid.uuid4()))
    qid = data.get('qid')
    answer_text = data.get("student_answer", "")

    try:
        system_info = database['feedback_system'].find_one({'tid': tid})
        if not system_info:
            raise ValueError('Feedback system not found: {}'.format(tid))
        
        if answer_text.strip():
            # Extract configuration from system
            micro_feedback = system_info.get('micro_feedback', {})
            macro_feedback = system_info.get('macro_feedback', {})
            
            # Get style descriptors and templates
            style_keywords = macro_feedback.get('keywords', [])
            feedback_templates = macro_feedback.get('templates', [])
            
            # Get teaching style and personalization
            teach_style = micro_feedback.get('teach_style', 'DIRECT')
            teach_example = micro_feedback.get('examples', '')
            locked_style = macro_feedback.get('locked_style', False)
            
            # Build system prompt for feedback generation (no scoring)
            system_prompts = utils.parse_teaching_style(
                style_keywords=style_keywords,
                feedback_templates=feedback_templates,
                teach_style=teach_style,
                teach_example=teach_example,
            )

            system_prompt = system_prompts['final']
            custom_prompt = system_prompts['custom'] if system_prompts.get('custom', '') else None
            
            # Build user prompt with student answer (no scoring)
            user_prompt = utils.build_feedback_user_prompt(
                student_answer=answer_text,
                feedback_structure=feedback_templates
            )
            
            # Generate feedback using LLM (no scoring)
            model_name = 'gpt-4o'
            feedback_text, feedback_prob = utils.llm_generate(
                input_text=user_prompt,
                system_text=system_prompt,
                model=model_name,
                temperature=0.3,  # Slightly higher temperature for more natural feedback
                logprobs=True
            )
            
            # Store feedback in database (no scoring)
            database['responder'].insert_one({
                'tid': tid,
                'aid': aid,
                'question': qid,
                'student_answer': answer_text,
                'generated_response': feedback_text,  # Changed from 'generated_feedback'
                'system_config': {
                    'style_keywords': style_keywords,
                    'feedback_templates': feedback_templates,
                    'teach_style': teach_style,
                    'teach_example': teach_example,
                    'final_prompt': system_prompt,
                    'selected_prompt': system_prompts['selected'],
                    'custome_prompt': custom_prompt
                },
                'confidence': feedback_prob,
                'generated_at': datetime.utcnow()
            })
            
            response = {'success': True, 'aid': aid}
        else:
            response = {'success': False, 'aid': aid}
            
    except Exception as e:
        traceback.print_exc()
        response = {'success': False, 'error': str(e)}
    
    return jsonify(response)

@app.route('/api/response/load', methods=['GET'])
def response_load():
    """Load generated feedback response by answer ID"""
    aid = request.args.get('aid')
    try:
        result = database['feedback'].find_one({'aid': aid})
        if result:
            # Return the generated response (no scoring)
            response_text = result.get('generated_response', '')
            confidence = result.get('confidence')
            
            # Format as HTML for display
            formatted_response = utils.format_response_html(
                response_text=response_text,
                confidence=confidence,
                system_config=result.get('system_config', {})
            )
            
            return jsonify({'response': formatted_response})
        return jsonify({'response': None})
    except:
        traceback.print_exc()
        return jsonify({'response': None})

# Remove the feedback/generate endpoint as we're using response/submit instead
# Keep answer/submit for legacy compatibility but redirect to response/submit
@app.route('/api/answer/submit', methods=['POST'])
def answer_submit():
    """Legacy endpoint - redirect to response/submit"""
    data = request.get_json()
    try:
        # Redirect to the actual response generation
        with app.test_client() as client:
            response = client.post('/api/response/submit', 
                                 json=data,
                                 content_type='application/json')
            result = response.get_json()
            
        return jsonify(result)
        
    except:
        traceback.print_exc()
        return jsonify({'success': False})

# Update feedback/load to also support the new response format
@app.route('/api/feedback/load', methods=['GET'])
def feedback_load():
    """Load generated feedback by answer ID (legacy compatibility)"""
    aid = request.args.get('aid')
    try:
        result = database['feedback'].find_one({'aid': aid})
        if result:
            # Check for both old and new response field names
            response_text = (result.get('generated_response') or 
                           result.get('generated_feedback') or 
                           result.get('grade', ''))
            
            confidence = result.get('confidence')
            
            # Format as HTML for display
            formatted_response = utils.format_response_html(
                response_text=response_text,
                confidence=confidence,
                system_config=result.get('system_config', {})
            )
            
            return jsonify({'grade': formatted_response})  # Keep 'grade' key for legacy compatibility
        return jsonify({'grade': None})
    except:
        traceback.print_exc()
        return jsonify({'grade': None})

@app.route('/api/response/load', methods=['GET'])
def response_load():
    aid = request.args.get('aid')
    result = database['feedback'].find_one({'aid': aid})
    if result:
        return jsonify({'response': result.get('response', '')})
    return jsonify({'response': None})

# ==================== Legacy API Routes (for backward compatibility) ==================== #

@app.route('/api/optimize/load', methods=['POST'])
def optimize_load():
    """Legacy optimization endpoint - return empty for now"""
    data = request.get_json()
    optid = data.get('optid')
    # Return empty result as optimization is not part of feedback generation
    return jsonify({'output': None})

@app.route('/api/bucket/upload', methods=['POST'])
def bucket_upload():
    """File upload endpoint - placeholder for future implementation"""
    file = request.files['file']
    # TODO: Implement file upload for feedback resources
    return jsonify({'success': False, 'message': 'File upload not implemented yet'})

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