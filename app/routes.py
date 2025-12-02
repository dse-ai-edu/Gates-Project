import re
import os
import uuid
import time
import traceback

from flask import render_template, request, jsonify

import app.utils as utils
import app.prompts as prompts
from app import app, database, s3_client
from datetime import datetime, timedelta

from pymongo import DESCENDING

question_this = """
<p>Find the derivative of each of the following functions. You do not need to simplify your answers.</p>
<p>(a) f(x) = x<sup>ln(x)</sup></p>
"""
reference_this = """
<p>Find the derivative of each of the following functions. You do not need to simplify your answers.</p>
<p>(a) f(x) = x<sup>ln(x)</sup></p>
<p><strong>Solution:</strong></p>
<p>To find the derivative of f(x) = x<sup>ln(x)</sup>, we use logarithmic differentiation.</p>
<p>Take the natural logarithm of both sides:</p>
<p>ln(f(x)) = ln(x) · ln(x) = (ln(x))<sup>2</sup></p>
<p>Differentiate both sides with respect to x:</p>
<p>f'(x)/f(x) = 2ln(x) · (1/x)</p>
<p>Solve for f'(x):</p>
<p>f'(x) = f(x) · 2ln(x)/x = x<sup>ln(x)</sup> · 2ln(x)/x</p>
<p><strong>Answer: f'(x) = x<sup>ln(x)</sup> · 2ln(x)/x</strong> or equivalently <strong>f'(x) = 2x<sup>ln(x)-1</sup>ln(x)</strong></p>
"""
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
        database['comment'].find_one_and_update(
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
            'teach_style': data.get('teach_style', ''),
            'teach_example': data.get('teach_example', '')
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

def comment_generate(system_info, answer_text, question_text, reference_text, history_prompt_dict):
    """Generate personalized feedback response for student answer"""
    if history_prompt_dict:
        system_prompts_raw = history_prompt_dict
    else:
        try:
            # Extract configuration from system
            micro_feedback = system_info.get('micro_style', {})
            macro_feedback = system_info.get('macro_style', {})
            
        # Get style descriptors and templates
            style_keywords = macro_feedback.get('keywords', [])
            feedback_templates = macro_feedback.get('templates', [])
            
        # Get teaching style and personalization
            teach_style = micro_feedback.get('teach_style', 'DIRECT')
            teach_example = micro_feedback.get('examples', '')
            locked_style = macro_feedback.get('locked_style', False)
            
        # Build system prompt for feedback generation
            system_prompts_raw = utils.parse_teaching_style(
                teach_style=teach_style,
                teach_example=teach_example,
            )
        except Exception as e:
            traceback.print_exc()
            return {'success': False, 'error': str(e)}

    try:
        # Build user prompt with student answer
        system_prompt = system_prompts_raw['final']
        custom_prompt = system_prompts_raw['custom'] if system_prompts_raw.get('custom', '') else None
        user_prompt = utils.parse_teaching_text(
            question=question_text + "\n ## Reference Answer is: " + reference_text,
            answer=answer_text,
            style_keywords=style_keywords,
            feedback_templates=feedback_templates,
            )
        
       # Generate feedback using LLM
        feedback_text, feedback_prob = utils.llm_generate(
            input_text=user_prompt,
            system_text=system_prompt,
            model='gpt-4o',
            temperature=0.7, 
            max_tokens=750,
            logprobs=True
        )
        
        return {
            'success': True,
            'feedback_text': feedback_text,
            'feedback_prob': feedback_prob,
            'style_keywords': style_keywords,
            'feedback_templates': feedback_templates,
            'teach_style': teach_style,
            'teach_example': teach_example,
            'system_prompt': system_prompt,
            'selected_prompt': system_prompts_raw.get('selected', ""),
            'custom_prompt': custom_prompt
        }
        
    except Exception as e:
        traceback.print_exc()
        print(system_prompts_raw)
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
    reference_this = data.get("reference", "")
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
            history_prompt_dict = history_prompt_dict
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
                'teach_style': generate_result['teach_style'],
                'teach_example': generate_result['teach_example'],
                'final_prompt': generate_result['system_prompt'],
                'selected_prompt': generate_result['selected_prompt'],
                'custom_prompt': generate_result['custom_prompt']
            },
            'confidence': generate_result['feedback_prob'],
            'generated_at': datetime.utcnow()
        })
        
        response = {'success': True, 'tid': tid, 'aid': aid, 'attempt_id': next_attempt_id}
            
    except Exception as e:
        traceback.print_exc()
        response = {'success': False, 'error': str(e)}

    return jsonify(response)

# @app.route('/api/comment/submit', methods=['POST'])
# def comment_submit():
#     """Generate personalized feedback response for student answer (no scoring involved)"""
#     data = request.get_json()
#     tid = data.get('tid')
#     archive_tid = data.get('archive_tid', "").strip()
#     aid = data.get('aid', str(uuid.uuid4()))
#     qid = data.get('qid')
#     answer_text = data.get("student_answer", "")
#     model_name = 'gpt-4o'
    
#     if archive_tid:
#         try:
#             history_system_info = database['comment_config'].find_one({'tid': archive_tid})
#             history_system_info = history_system_info['config']
#             system_info = history_system_info[-1] if isinstance(history_system_info, list) else history_system_info
#         except Exception as e:
#             traceback.print_exc()
#             response = {'success': False, 'error': str(e)}
#     else:
#         try:
#             system_info = database['comment_config'].find_one({'tid': tid})
#             if not system_info:
#                 raise ValueError('Feedback system not found: {}'.format(tid))
            
#             if answer_text.strip():
#                 system_info = system_info['config']
#                 system_info = system_info[-1] if isinstance(system_info, list) else system_info
#                 # Extract configuration from system
#                 micro_feedback = system_info.get('micro_style', {})
#                 macro_feedback = system_info.get('macro_style', {})
                
#                 # Get style descriptors and templates
#                 style_keywords = macro_feedback.get('keywords', [])
#                 feedback_templates = macro_feedback.get('templates', [])
                
#                 # Get teaching style and personalization
#                 teach_style = micro_feedback.get('teach_style', 'DIRECT')
#                 teach_example = micro_feedback.get('examples', '')
#                 locked_style = macro_feedback.get('locked_style', False)
                
#                 # Build system prompt for feedback generation (no scoring)
#                 system_prompts = utils.parse_teaching_style(
#                     teach_style=teach_style,
#                     teach_example=teach_example,
#                 )

#                 system_prompt = system_prompts['final']
#                 custom_prompt = system_prompts['custom'] if system_prompts.get('custom', '') else None
                
#                 # Build user prompt with student answer (no scoring)
#                 user_prompt = utils.parse_teaching_text(
#                     question=question_this + "\n ## Refernce Answer is: " + reference_this,
#                     answer=answer_text,
#                     style_keywords=style_keywords,
#                     feedback_templates=feedback_templates,
#                 )
                
#                 # Generate feedback using LLM (no scoring)
#                 model_name = 'gpt-4o'
#                 feedback_text, feedback_prob = utils.llm_generate(
#                     input_text=user_prompt,
#                     system_text=system_prompt,
#                     model=model_name,
#                     temperature=0.7, 
#                     max_tokens = 750,
#                     logprobs=True
#                 )
                
#                 # Store feedback in database (no scoring)
#                 max_attempt_record = database['comment'].find_one(
#                     {'tid': tid},
#                     sort=[('attempt_id', -1)]
#                     )
#                 print(f">>>6>>> {max_attempt_record}")
#                 next_attempt_id = (max_attempt_record.get('attempt_id', -1) + 1) if max_attempt_record else 0

#                 database['comment'].insert_one({
#                     'tid': tid,
#                     'aid': aid,
#                     'question': qid,
#                     'attempt_id': next_attempt_id,
#                     'student_answer': answer_text,
#                     'generated_response': feedback_text,  # Changed from 'generated_feedback'
#                     'system_config': {
#                         'style_keywords': style_keywords,
#                         'feedback_templates': feedback_templates,
#                         'teach_style': teach_style,
#                         'teach_example': teach_example,
#                         'final_prompt': system_prompt,
#                         'selected_prompt': system_prompts['selected'],
#                         'custom_prompt': custom_prompt
#                     },
#                     'confidence': feedback_prob,
#                     'generated_at': datetime.utcnow()
#                 })
#                 print(f"insert one record with tid {tid} and atmp_id {next_attempt_id}")
#                 print(f">>>8>>>{feedback_text}")
#                 print(f">>>9>>>{feedback_prob}")
#                 response = {'success': True, 'tid': tid, 'aid': aid, 'attempt_id': next_attempt_id}
#             else:
#                 response = {'success': False, 'tid': tid, 'aid': aid}
                
#         except Exception as e:
#             traceback.print_exc()
#             response = {'success': False, 'error': str(e)}

#     print(">>>1>>>", aid, next_attempt_id)
#     return jsonify(response)

@app.route('/api/comment/load', methods=['GET'])
def comment_load():
    """Load generated feedback response by answer ID"""
    tid = request.args.get('tid')
    attempt_id = request.args.get('attempt_id')
    print(">>>1>>>", tid, attempt_id)
    try:
        print(f"want to find one record with tid {tid} and atmp_id {attempt_id}")
        result = database['comment'].find_one({'tid': tid, 'attempt_id': int(attempt_id)})
        response_text = result.get('generated_response', '')
        if response_text:
            # Return the generated response (no scoring)
            confidence = result.get('confidence', '-1')

            # Format as HTML for display
            formatted_response = utils.format_response_html(
                response_text=response_text,
                confidence=confidence,
            )
            print(f">>>3>>>{formatted_response}")
            print(f">>>4>>>{response_text}")
            print(f">>>5>>>{confidence}")

            return jsonify({'success': True, 'response': formatted_response})
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