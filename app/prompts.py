SCI_GRADE = """
# Task
Use rubric to assign a score for the student's answer to the question.

{resource}

{question}

{rubric}

{example}

# Output format
Score: <SCORE>
Reasoning: <REASONING>

## Output Rules
1. Repalce "<SCORE>" with your score assignment for the student response. 
2. Replace "<REASONING>" with your reasoning for score assignment.
3. **You MUST strictly obey this output format.**

# Prediction
Text: {answer}
Label: 
""" 


VIP_GRADE = """
# Task
In this task, you perform the task of assessing teachers’ knowledge of mathematics teaching by grading teacher's response to a math teaching question.

{question}

{resource}

{rubric}

{example}

# Output format
<SCORE>
Reasoning: <REASONING>

## Output Rules
1. Repalce "<SCORE>" with ONLY ONE INTEGER from 0, 1, or 2.
2. Replace "<REASONING>" with your reasoning for score assignment.
3. **You MUST strictly obey this output format.**

# Prediction
Text: {answer}
Label:
"""