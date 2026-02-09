QUESTION_RECOGNITION = """

You are given an image containing a mathematics problem statement.

Your task is to recognize and transcribe the problem into LaTeX,
preserving the original mathematical meaning, conditions, and structure.

Transcribe ONLY the question itself:
- Include givens, definitions, constraints, and sub-questions.
- Exclude any student-written solutions, answers, or scratch work.

Prioritize mathematical meaning over visual layout.
If the question has multiple parts, preserve their labels and order.

If any content is unclear, make the most reasonable interpretation;
if ambiguity remains, use \\text{[illegible]}.

Output LaTeX only.
Do not solve, explain, or modify the problem.

"""

ASSESSMENT_RECOGNITION = """

You are given an image containing grading rules or a scoring rubric
for a mathematics problem.

Your task is to recognize and transcribe the grading criteria into LaTeX,
preserving point values, conditions, and structure as written.

Transcribe ONLY assessment-related content:
- Include scoring rules, point allocations, and conditions for credit.
- Exclude the problem statement unless it is explicitly part of the rubric.
- Exclude student answers or worked solutions.

Preserve logical relationships between conditions and points.
Do not reinterpret or simplify the grading logic.

If any content is unclear, use \\text{[illegible]}.

Output can be markdown, latex or plain text, preserving structure and relations of points.
Do not evaluate any student work.

"""
