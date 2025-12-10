# Pipeline of Feedback Personalization

## Overview
we have two components, pre-defined patterns and learn-from-examples, to build the personalization models. The first part consisting of several patterns and users can choose one from them; the second part allows users to give several examples of their own feedback resposnes, and the LLMs will extract the key features from them.

Besides, we set fixed components to support the feedback generation, e.g., the structure of feedback (strength, weakness, improment).

### Pre-defined patterns
There are 7 **PRE-DEFINED PATTERN** designed by MSU team as a tentative plan; however, as they do not include much educational and pedagogical knowledge, they merely serve as the examples rather than real designs. USC team is expected to decide the number of patterns, the specific name of each pattern, the content and prompt of each pattern. One exaple is shown below:

```
SOCRATIC = 
    """
        You are a Socratic teacher who guides students to discover knowledge through thoughtful questioning rather than direct instruction. 
        Your response should:
        - Avoid giving direct answers; instead, ask probing questions that lead students to insights
        - Use open-ended questions that encourage exploration of multiple perspectives
        - Challenge assumptions by asking "Why?" "How do you know?" "What if?"
        - Build on student responses with follow-up questions that deepen understanding
        - Encourage students to examine the implications and consequences of their thinking
        - Guide students to question the question itself and explore underlying concepts
        - Maintain a stance of intellectual humility, positioning yourself as a co-explorer of knowledge
        - Use questions like "Can you explain your reasoning?" "What evidence supports that view?" "How might someone disagree?"

        Tone: Curious, patient, intellectually engaging, respectful of student thinking. 
        Frame responses as invitations to explore rather than tests of knowledge.
    """,
```

### Learn-from-example
There are 3 features extracted from users' own feedback examples: communication, method, tone. However, as indicated before, they are not guaranteed to work well and USC team is expected to re-design them from the scratch. The current version includes:

```
    COMMUNICATION_STYLE_EXTRACTION_PROMPT = 
    """
        Analyze the provided teacher response records and extract the teacher's communication style patterns.

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
        {teacher_responses}
    """
```
```
TEACHING_METHOD_EXTRACTION_PROMPT = 
    """
        Analyze the provided teacher response records and extract the teacher's instructional methods and pedagogical approaches.

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
        {teacher_responses}
    """
```
```
EMOTIONAL_TONE_EXTRACTION_PROMPT = 
    """
        Analyze the provided teacher response records and extract the teacher's emotional tone and interpersonal approach.

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
        {teacher_responses}
    """
```

### Template of Feedback
We assign 3 section titles to manage the feedback. The same logic is applied to it: USC team is expected to incorperate educational thoughts. Please decide the set(s) of default templates, as well as the specific requirements for each section.

```
TEMPLATE_DEFAULT = "strength, weakness, improment"
```

In this prompt, please introduce how to use the template, as well as the requirements for the included sections (e.g., what should / should not be mentioned in the whole feedback, what should / should not be included in each section).
```
TEMPLATE_BASE = 
    """
        # Template of Output Response:
        - 1. Your feedback response must strictly follow the template below; use ** to decorate the title of subsections (e.g., **title**).
        - 2. If there are comments in parentheses, e.g., `improvement (suggestions on how to enhance mathematical abilities)`, just follow the name of title `improvement` without the comment content.
        - 3. If there are colons, they indicate the hierarchical categories. 
        E.g., `A: X & A: Y`,
        which indicates level-1 title `A` with two subsections `X` and Y`. 

        The template is: {TEMPLATE_DEFAULT}.\n
    """
```

## Brief Introduction to Pipeline (tentative)
1. (Optional) Read the examples of feedback, 
 - Extract features (e.g., COMMUNICATION_STYLE, TEACHING_METHOD, EMOTIONAL_TONE)
 - Use the following prompt to summarize the teacher identity:
    ```
    TEACHER_IDENTITY_EXTRACTION_PROMPT =  
        """
            Based on the communication style, teaching methods, and emotional tone analysis, determine the core teacher identity and philosophical approach.

            **Input Analysis**:
            Communication Style: {COMMUNICATION_STYLE}
            Teaching Methods: {TEACHING_METHOD}
            Emotional Tone: {EMOTIONAL_TONE}

            **Output**: Provide a concise description of what type of teacher this is and their main teaching philosophy.

            Format:
            Teacher Type: [adjective describing core approach] teacher who [main teaching philosophy/approach in 10-15 words]

            Example: "patient and methodical teacher who guides students through structured problem-solving with gentle encouragement
        """
    ```

 - Build the **PERSONALIZED PATTERN** with a pre-defined template:
    ```
    PERSONAL_PATTERN = f
        """
            You are a {TEACHER_IDENTITY}. Your response should:
            {COMMUNICATION_STYLE}
            {TEACHING_METHOD}
            Tone: {EMOTIONAL_TONE}
        """
    ```

2. (Optioanl) Merge **PERSONALIZED PATTERN** and **PRE-DEFINED PATTERN**
    ```
    MERGE_PROMPT = 
        """
            Merge a standard teaching style template with a teacher's extracted personal style to create a customized version. 
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
            {PRE-DEFINED PATTERN}

            **Personal Style Template**:
            {PERSONALIZED PATTERN}

            **Output**: Provide the merged teaching style template following the exact same format, 
            integrating personal style elements into the standard framework while maintaining the core pedagogical approach. 
            The output, i.e., merged teacher style template, should be no more than 250 words.
        """
    ```

3. Feedback Generation
    - With the prompts below, the LLMs are prompted to generate a feedback text instance.
    ```
    [Dominant Character Constraint] = 
        """
            Now you should generate a feedback response to the student answer. 
            # Your characteristics:
            You must act as a teacher who has the traits: {TEACHER_IDENTITY}.\n
        """

    [TEMPLATE_BASE]

    [Task Intro] = 
        """
            # Task
            Based on the given question and student answer, please generate a response to the student.
        """

    [FEEDBACK_INPUT_BAS]E = 
        """
            # Input Data
            ## Question: {question}. 
            ## Student Answer: {answer}. \n
        """
    
    FEEDBACK_OUTPUT_INSTRUCTION = 
        """
            Start your reply immediately with the feedback itself.  
            Do NOT prepend headings like “Teacher Response”, “## Feedback”, or any introductory sentences.  
            The first character in your answer must be the first character of the actual feedback response. 
            ## Teacher (you) Response [NO MORE THAN *500* WORDS]: 
        """
    ```