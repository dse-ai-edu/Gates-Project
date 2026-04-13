### Teacher Trait Extraction for Custom Style ###
COMMUNICATION_STYLE_EXTRACTION_PROMPT = """Analyze the provided teacher response records and extract the teacher's communication style patterns.

**Focus**: How this teacher communicates with students - language choice, formality level, interaction patterns.

**Analysis Points**:
- Formal vs. casual language use
- Direct vs. indirect communication
- Questioning vs. explaining tendencies
- Use of encouragement vs. correction
- Authority vs. collaborative positioning

**Output**: Provide 2-5 bullet points describing specific communication behaviors this teacher consistently uses. 
Each bullet should be actionable and observable, and no more than 25 words.

Format:
- [Communication behavior 1]
- [Communication behavior 2]

Teacher Response Records:
{teacher_responses}"""


TEACHING_METHOD_EXTRACTION_PROMPT = """Analyze the provided teacher response records and extract the teacher's instructional methods and pedagogical approaches.

**Focus**: How this teacher structures learning, provides instruction, and guides student understanding.

**Analysis Points**:
- Step-by-step vs. holistic instruction
- Discovery-based vs. direct teaching
- Problem-solving vs. information delivery
- Scaffolding and support strategies
- Assessment and feedback methods

**Output**: Provide 2-5 bullet points describing specific instructional methods this teacher consistently uses. 
Each bullet should be actionable and observable, and no more than 25 words.

Format:
- [Teaching method 1]
- [Teaching method 2]

Teacher Response Records:
{teacher_responses}"""


EMOTIONAL_TONE_EXTRACTION_PROMPT = """Analyze the provided teacher response records and extract the teacher's emotional tone and interpersonal approach.

**Focus**: The emotional climate this teacher creates and their interpersonal style with students.

**Analysis Points**:
- Warmth vs. professional distance
- Patience vs. urgency
- Supportive vs. challenging approach
- Empathy and validation patterns
- Energy level and enthusiasm

**Output**: 
1. Core Tone: [2-5 adjectives describing the dominant emotional tone]
2. Interpersonal Style: [1-2 sentences describing how this teacher relates to students.]

Format:
Core Tone: [adjective1, adjective2]
Interpersonal Style: [Description of relationship approach and interaction style, each being no more than 25 words]

Teacher Response Records:
{teacher_responses}"""


TEACHER_IDENTITY_EXTRACTION_PROMPT = """Based on the communication style, teaching methods, and emotional tone analysis, determine the core teacher identity and philosophical approach.

**Input Analysis**:
Communication Style: {communication_style}
Teaching Methods: {teaching_methods}
Emotional Tone: {emotional_tone}

**Output**: Provide a concise description of what type of teacher this is and their main teaching philosophy.

Format:
Teacher Type: [adjective describing core approach] teacher who [main teaching philosophy/approach in 10-15 words]

Example: "patient and methodical teacher who guides students through structured problem-solving with gentle encouragement"""


### Supportive methods, shorten the prompts ###
SUMMARIZE_PROMPT = """Compress the following teaching style template to 250 words or fewer, 
while preserving the exact format and all key behavioral components.
**Requirements**:
- Maintain the original structure: "You are a [X] teacher who [Y]. Your response should:" followed by bullet points and "Tone:" section
- Keep ALL main points but make them more concise
- Preserve the essential behavioral guidance in each bullet point
- Maintain the tone description but make it more succinct
- Remove redundant words while keeping actionable specifics
- Ensure the compressed version still provides clear guidance for LLM behavior
**Input Template**:
{input_template}

**Output**: Provide the compressed version following the same format, 
ensuring it stays under 250 words while preserving all key teaching behaviors and guidance."""


MERGE_PROMPT = """Merge a standard teaching style template with a teacher's extracted personal style to create a customized version. 
Use the standard style as the foundation and integrate the personal style elements as refinements.

**Task**: 
- Keep the standard style template as the base structure and core approach
- Integrate specific behavioral patterns from the personal style as enhancements
- Maintain the original format: "You are a [X] teacher who [Y]. Your response should:" + bullet points + "Tone:" section
- Preserve all bullet points from the standard template but refine them with personal style elements
- Enhance the tone description by incorporating personal characteristics

**Merging Strategy**:
- Standard template provides the pedagogical framework
- Personal style adds individual behavioral nuances and communication patterns
- Combine complementary elements, resolve conflicts by favoring standard approach
- Ensure the merged template maintains consistency and clarity

**Standard Style Template**:
{standard_template}

**Personal Style Template**:
{personal_template}

**Output**: Provide the merged teaching style template following the exact same format, 
integrating personal style elements into the standard framework while maintaining the core pedagogical approach. 
The output, i.e., merged teacher style template, should be no more than 250 words."""


## Bridge grading result for response generation
MACRO_TRAIT_BASE = """ 
Now you should generate a feedback response to the student answer.
# Your characteristics:
You must act as a teacher who has the following traits:

{}
"""


# MACRO_TEMPLATE_BASE = """
# # Template of Output Response:
#  - 1. Your feedback response must strictly follow the template below; use ** to decorate the title of subsections (e.g., **title**).
#  - 2. If there are comments in parentheses, e.g., `improvement (suggestions on how to enhance mathematical abilities)`, just follow the name of title `improvement` without the comment content.
#  - 3. If there are colons, they indicate the hierarchical categories. 
# E.g., `A: X & A: Y`,
# which indicates level-1 title `A` with two subsections `X` and Y`. 

# The template is: {}.\n"""

MACRO_TEMPLATE_BASE = """
# Template of Output Response:
Your feedback response must strictly follow the template below; use ** to decorate the title of subsections (e.g., **title**).

The template is: {}.\n"""

## remove personalization for template
## focus on weakness, how to improve to meet the expectations --> how to improve to the weakness points
## do not leak the solution directly
## for learning purpose
## remove step 1 and step 2. Write new content for step 3.

GRADING_REFERENCE = """# Grading to Student Answer
Here is the grading result of the same question and student answer for your reference. 
## Rubric for Student Answer: {grading_rubric}. 
## Grading for Student Answer: {grading_text}.\n"""


FEEDBACK_BASE = """
# Task
Based on the given question and student answer, please generate a response to the student.
"""

FEEDBACK_INPUT_BASE = """
# Input Data
## Question: {question}. 
## Student Answer: {answer}. \n"""

FEEDBACK_OUTPUT_INSTRUCTION = """
Start your reply immediately with the feedback itself.  
Do NOT prepend headings like “Teacher Response”, “## Feedback”, or any introductory sentences.  
The first character in your answer must be the first character of the actual feedback response. \n
"""
## Feedback Promopt as Requirements
FEEDBACK_REQUIREMENT = """
** KSMT (Knowledge of Students' Mathematical Thinking) Rubric **

## Overview
The KSMT rubric for evaluating teacher responses aims to differentiate responses based on how well they address students' mathematical understanding of the key concepts underlying their solutions or strategies.

For this question, we aim to assess whether teachers understand the student's solution and recognize her proportional reasoning ability. The question specifically asks teachers to analyze Amy's understanding of equivalent ratios; therefore, responses providing accurate and specific analyses of Amy's understanding, with evidence from her work, would receive higher scores.

## Student Work Analysis

Amy's math solution and written explanation do not align perfectly; therefore, it is important to attend closely to the details in both and to acknowledge responses that recognize she is thinking multiplicatively (demonstrating an understanding of equivalent ratios). 

Amy's approach reveals a strong understanding of creating equivalent amounts to compare different situations using scaling strategies. Evidence of this comes from her math work:
- She compares the first deal (Savemore) by determining the price of 4 crayons, as the deal originally lists the price for 8 crayons
- Amy does this by multiplying the price by 0.5, demonstrating an understanding of creating equivalent ratios
- She then compares the price for 12 crayons across two deals (Savemore and BargainHut)
- Subsequently, she creates equivalent ratios by determining the prices for 24 crayons for the first (Savemore) and third (Costless) deals

The choice of 24 crayons is deliberate, as the third deal provides the price for 24 crayons. However, her written explanation — where she states, "It's only 4 crayons more" — might suggest an additive strategy, but her scaling strategies indicate that she is not thinking additively; rather, she is using imprecise language to describe what she did.

Amy's explanation highlights that, while adding 4 crayons increases the total cost to $2.40, the first deal costs $1 for 8 crayons. Her solution and written explanation provide evidence of her understanding of the covariance between total cost and the number of crayons and demonstrates her grasp of comparing ratios through scaling.

## Scoring Criteria (3-Point Scale)

### Score of 2
**Awarded if:**
- The teacher's response includes an accurate analysis of the student's understanding of the multiplicative relationship between quantities in creating equivalent ratios and uses that knowledge to compare different situations
- The response must provide specific information about how the teacher reached this conclusion or why the student's approach is correct
- The focus must be on the student's mathematical thinking, and the entire response must be correct
- **OR** The response diagnoses the student's mathematical thinking, even if the issue is not immediately apparent (e.g., recognizing that Amy's written explanation might suggest additive thinking, but her math work clearly shows multiplicative understanding)

### Score of 1
**Awarded if:**
- The teacher's response includes an accurate description or analysis of the student's understanding of creating equivalent ratios (proportions)
- The evidence is either purely procedural (focusing on what the student did or did not do) or lacks explicit statements about the student's understanding of the multiplicative relationship between quantities
- The analysis and description of the student's understanding must be specific, not generic

### Score of 0
**Awarded if:**
- The teacher's response provides a generic, incorrect, or absent description or analysis of the student's understanding of creating equivalent ratios using multiplicative strategies
- **OR** The teacher's response restates what the student said or did without analyzing the student's thinking or reasoning
- Simply stating that the student answered correctly does not demonstrate a focus on the student's understanding

## Examples by Score

| Score | Sample Response | Reason |
|-------|-----------------|--------|
| **0** | "Their answer is correct but their math work and explanation is difficult to follow." | No analysis of student thinking. |
| **0** | "Amy does not understand the concept of unit price as the price for one item." | Incorrect analysis with no evidence supporting the claim. |
| **1** | "They were able to understand that a group of 8 crayons cost 1.00 dollars and that 3 groups of 8 should have cost 3.00 but didn't." | Describes the student's multiplicative thinking by referencing what the student did. |
| **1** | "This student knew to find the cost for 4 crayons by figuring out how much 4 crayons cost per each box..." | Correct analysis but evidence is procedural (based on what student did). |
| **2** | "The student understands the multiplicative relationship between the amount of crayons. 8 crayons × 1.5 = 12. Amy has strong number sense in this thinking." | Correct analysis supported by evidence from student's work. |
| **2** | "Amy understands the importance of comparing equivalent units. They scaled deal A up to 12 crayons in order to compare with deal B..." | Teacher clearly follows student's work and understands scaling strategies. |

## Key Focus Areas
Responses focusing on Amy's understanding of:
- Equivalent ratios
- Proportion and proportional reasoning
- Multiplicative relationships
- Specific details from her mathematical work

Should receive higher scores when they demonstrate analysis of **thinking and understanding** rather than just describing **what Amy did**.
"""

JUDGE = """
You are an independent grading judge.

You will be given:
- A question
- A grading rubric
- A student's answer

Your task:
- Assign a numerical score strictly following the rubric.
- Provide a concise but clear explanation.

Rules:
- Do NOT consider other judges' opinions unless explicitly shown.
- Be objective and rubric-driven.
- If there are suggestions from human experts, consider them seriously.

Output format:
Include both the score and reasoning.
"""


FEEDBACK_POST_PROCESS_PROMPT= """
You are a feedback post-processing editor.

The input is a teacher feedback text generated by an upstream system.  
It may contain internal sections such as “Strength”, “Weakness”, or “Suggestions for improvement”.

Your task is to produce a concise student-facing feedback text.

## Editing Rules

1. Remove all section titles and structural labels.
2. Merge the content into natural language paragraphs.
3. The final text must contain **no more than 5 sentences**.
4. Preserve the original meaning and key points.

You may shorten phrasing, merge sentences, and remove repetition when necessary.

## Structure

The final text must:
- contain **no section headings**
- contains 3 - 4 sentences (shorter is allowed if necessary; longer is always prohibited)
- read as a continuous natural response
- optionally use short lists if multiple suggestions are mentioned
- remain clear and readable

## Restrictions

This task is **pure editing only**.

Do NOT:
- add new information
- invent new feedback
- infer the student answer
- evaluate the student
- explain the editing process
- produce commentary outside the final text

Only rewrite the given feedback under the constraints above.

## Output Format

Return structured output with two fields:

text: the processed feedback text;
flag: integer, binary 1 or 0;

Set:
flag = 1  (normal processing); flag = 0 (no valid input received)

The `text` field must contain only the edited feedback content.
The `text` field must contain 3 to 4 sentences in English.
Return only the structured output. No extra text.
"""


GET_FULL_POINT_PRMPT = """
You are a scoring-rule parser.

Input: a grading rubric that lists scoring items with numerical point values.  
The format may be JSON, plain text, Markdown, or LaTeX.

Your task is to compute the **maximum achievable score** implied by the rubric.

Rules:
1. Extract all numerical point values that represent scoring items.
2. Treat positive or zero values as points that can be earned.
3. Ignore all negative values (they represent penalties).
4. The full score is the **sum of all non-negative point values**.
5. If no non-negative values exist, return 0.

Important:
- Do NOT return the correct answer to the original problem.
- Ignore numbers that appear in explanations (e.g., “the correct answer is 2”) unless they are clearly part of a scoring item.

Output:
Return only a single number representing the full score. No text, no explanation.
"""


SOLUTION_REJECT_PRMPT="""
# IMPORTANT: SERVER-SIDE REJECTION RULES FOR UNPROCESSABLE INPUTS:"
- IF the content is illegible, non-mathematical, irrelevant, or cannot be reliably interpreted after reasonable effort, respond with exactly one word: [REJECT]"
- The response must be precisely: [REJECT] — including the square brackets, with no additional text, explanation, punctuation, or formatting."
- If this rule applies, it overrides all other instructions above. Do NOT attempt transcription or partial interpretation."     
"""


SHARED_NO_FORCING_FEEDBACK_SEG_PROMPT = """
# IMPORTANT HARD CONSTRAINTS: 
- No Forcing STRENGTHS section: If no strength exists in the student answer, do not include any.
- No Forcing WEAKNESSES section: If the student answer is correct, do not provide any weaknesses.  
"""


ADAPTIVE_DECIDE = """
You are an educational expert. Below are a pair of (question, student answer) and the guidance to select proper feedback pattern to him/her. You should response with one word in [conceptual, procedural, correctness] without any other comments or explanation. You are NOT asked to comment on or give feedback to the student answer.
"""


FEEDBACK_NO_FORCE = """
# IMPORTANT: if there is no meanful content in a section of given template, you may just skip this section; for example, if the response is almost perfect and your template contains the section of weakness, do not need to force saying something when there is little.\n
"""