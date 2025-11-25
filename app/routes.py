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
def home():
    return render_template('welcome.html')

@app.route('/create')
def create():
    return render_template('create.html')

@app.route('/select')
def select():
    return render_template('select.html')

# ==================== API Route (returns JSON) ==================== #

@app.route('/api/task/create', methods=['POST'])
def task_create():
    data = request.get_json()
    tid = data.get('tid')
    name = data.get('name')
    desc = data.get('desc')
    try:
        if not database['task'].find_one({'tid':tid}):
            database['task'].insert_one({'tid':tid, 'name':name, 'desc':desc})
        else:
            database['task'].find_one_and_update({'tid':tid}, {'$set':{'name':name, 'desc':desc}})    
        response = {'success':True}
    except:
        traceback.print_exc()
        response = {'success':False}
    return jsonify(response)


@app.route('/api/task/load', methods=['POST'])
def task_load():
    # This function is wrong.
    data = request.get_json()
    section = data.get('section')
    try:
        task_info = database['task'].find_one({'tid':data.get('tid')},)
        if task_info:
            if section == 'profile':
                response = {'name':task_info['name'],'desc':task_info['desc']}
            else:
                response = {'info':task_info[section]}
    except:
        traceback.print_exc()
    return jsonify(response)


@app.route('/api/task/show', methods=['POST'])
def task_show():
    data = request.get_json()
    user = data.get('user')
    try:
        task_list = database['task'].find({'tid':{'$exists':True}}, 
                                          {'tid':1,'name':1,'desc':1,'_id':0}).to_list()
        response = {'task_list':task_list}
    except:
        traceback.print_exc()
        response = {}
    return jsonify(response)



@app.route('/api/section/save', methods=['POST'])
def section_save():
    data = request.get_json()
    try:
        database['task'].find_one_and_update({'tid':data.get('tid')}, {'$set':data})
        response = {'success':True}
    except:
        traceback.print_exc()
        response = {'success':False}
    return jsonify(response)


@app.route('/api/section/load', methods=['POST'])
def section_load():
    data = request.get_json()
    section = data.get('section')
    response = {}
    try:
        task_info = database['task'].find_one({'tid':data.get('tid')},)
        if task_info:
            if section == 'profile':
                response = {'name':task_info.get('name',''),'desc':task_info.get('desc','')}
            else:
                response = {'info':task_info.get(section,dict())}
    except:
        traceback.print_exc()
    return jsonify(response)


@app.route('/api/answer/submit', methods=['POST'])
def answer_grade():
    data = request.get_json()
    tid = data.get('tid')
    aid = data.get('aid')
    answer_text = data.get('answer_text')
    answer_file = data.get('answer_file')
    try:
        task_info = database['task'].find_one({'tid':tid})
        if not task_info:
            raise ValueError('Fail to fetch task id: {}'.format(tid))
        
        if answer_text is not None and answer_file is None:
            # question and rubric is necessery
            question = task_info['question']['text']
            rubric = task_info['rubric']['text']
            if 'resource' in task_info:
                resource = task_info['resource']['text']
            else:
                resource = ''
            if 'example' in task_info:
                example = task_info['example']['text']
            else:
                example = ''
            answer = answer_text

            if tid in ['82acf738-ef7c-431a-89ac-a21cdc51d3be','d0de9e1b-bfff-4d1f-b889-c2bda1c8f5ca']:
                model_name = 'gpt-4o-2024-08-06'
                input_text = prompts.VIP_GRADE.format(
                    question=question, rubric=rubric, answer=answer,
                    resource=resource, example=example
                ).strip()
            else:
                model_name = 'gpt-4o'
                input_text = prompts.SCI_GRADE.format(
                    question=question, rubric=rubric, answer=answer,
                    resource=resource, example=example
                ).strip()
            
            response_text, response_prob = utils.llm_generate(
                input_text=input_text, model=model_name, 
                temperature=0, logprobs = True
            )

            score_text = response_text[0]
            response_text = '\n'.join(response_text.split('\n')[1:])
            score_reason = re.split(r'^[Rr]eason(ing)?:?',response_text)[-1].strip()
            
            output_text = "<strong>Score</strong>: {}<br><strong>Feedback</strong>: {}".format(score_text, score_reason)
            if response_prob:
                output_text = output_text + '<br><strong>Confidence</strong>: {}'.format(response_prob)

            # record the result into database
            database['feedback'].insert_one({'tid':tid, 'aid':aid, 'answer':input_text, 'grade':output_text})
        
        elif answer_text is None and answer_file is not None:
            raise NotImplementedError()
        else:
            raise ValueError('Duplicate or missing inputs in file and text.')
    except:
        traceback.print_exc()
    return jsonify()



@app.route('/api/feedback/load', methods=['GET'])
def feedback_load():
    aid = request.args.get('aid')
    result = database['feedback'].find_one({'aid': aid})
    if result:
        return jsonify({'grade': result['grade']})
    return jsonify({'grade': None})


@app.route('/api/optimize/load', methods=['POST'])
def optimize_load():
    data = request.get_json()
    optid = data.get('optid')
    result = database['optimize'].find_one({'optid': optid})
    if result:
        return jsonify({'output': result['output'], 'input':result['input']})
    return jsonify({'output': None})


@app.route('/api/bucket/upload', methods=['POST'])
def bucket_upload():
    file = request.files['file']
    # @Luke you may start to implement here


### Add Feedback Generation Functions
@app.route('/api/response/submit', methods=['POST'])
def answer_respond():
    data = request.get_json()
    tid = data.get('tid')
    aid = data.get('aid')
    answer_text = data.get('answer_text')
    answer_file = data.get('answer_file')
    try:
        task_info = database['task'].find_one({'tid': tid})
        if not task_info:
            raise ValueError('Fail to fetch task id: {}'.format(tid)) 
        
        if answer_text is not None and answer_file is None:
            question = task_info['question']['text']

            grading_rubric = task_info['rubric']['text'] # grading rubric
            grading_text = data.get('grade', None)

            teach_style = task_info['teach_style']['text']
            teach_order = task_info['teach_order']['text']

            if 'resource' in task_info:
                resource = task_info['resource']['text']
            else:
                resource = ''
            if 'example' in task_info:
                example = task_info['example']['text']
            else:
                example = ''

            answer = answer_text
            input_system_text = utils.parse_teaching_style(
                teach_style=teach_style,
                teach_order=teach_order,
                resource=resource,
                example=example
            )
            input_user_text = utils.parse_teaching_text(
                question=question,
                answer=answer,
                grading=[grading_rubric, grading_text]
            )
            
            model_name = 'gpt-4o'
            llm_text, llm_prob = utils.llm_generate(
                input_text=input_user_text,
                system_text=input_system_text,
                model=model_name,
                temperature=0,
                logprobs=True
            )
            feedback_text = llm_text[0]
            feedback_text = '\n'.join(feedback_text.split('\n')[1:])
            output_text = "<strong>Feedback</strong>: {}<br>".format(feedback_text)
            if llm_prob:
                output_text = output_text + '<br><strong>Confidence</strong>: {}'.format(llm_prob)
            database['feedback'].update_one(
                {'tid': tid, 'aid': aid},
                {'$set': {
                    'response': feedback_text,
                    'response_prob': llm_prob
                }}
            )
        elif answer_text is None and answer_file is not None:
            raise NotImplementedError()
        else:
            raise ValueError('Duplicate or missing inputs in file and text.')
    except:
        traceback.print_exc()
    return jsonify()


@app.route('/api/response/load', methods=['GET'])
def response_load():
    aid = request.args.get('aid')
    result = database['feedback'].find_one({'aid': aid})
    if result:
        return jsonify({'response': result['response']})
    return jsonify({'response': None})