import json

from typing import Dict, Tuple

from pydantic import BaseModel

import openai
from app import key_iter
# =========================

class JudgeOutput(BaseModel):
    score: float
    reasoning: str

class FullScoreOutput(BaseModel):
    score: float

# LLM main calling
def llm_structured_generate(
    input_text: str, 
    system_text: str = None, 
    model: str = 'gpt-4o-mini', 
    max_retry: int = 3, 
    max_tokens: int = 2048,
    format_obj: BaseModel = JudgeOutput
    ) -> str:
    
    user_msg = {'role':'user','content': str(input_text)}
    if system_text is not None:
        system_msg = {'role':'system','content':str(system_text)}
        messages = [system_msg, user_msg]
    else:
        messages = [user_msg]  
        
    for _ in range(max_retry):
        print(f"[SYS] Num of Try: {_}:")
        try:
            client = openai.OpenAI(api_key=next(key_iter))
            response = client.responses.parse(
                input=messages, 
                model=model, 
                text_format=format_obj
                )
            parsed_output = response.output_parsed
            return parsed_output
        except Exception as e:
            error_msg = str(e)
            print(f"!!! debug: response_prob error: {error_msg}")
            continue
    return error_msg


# =========================
# Internal: Single Judge
# =========================

def _run_judge(
    user_prompt: str,
    system_prompt: str,
    model: str = "gpt-4o-mini",
    max_tokens: int = 2048,
) -> Dict:
    """
    Run a single judge agent.
    Must return {"score": number, "reasoning": str}
    """
    raw = llm_structured_generate(
        input_text=user_prompt,
        system_text=system_prompt,
        model=model,
        max_tokens=max_tokens,
        format_obj=JudgeOutput,
    )

    print(f"Debug: raw judge generation: {str(raw)} with {type(raw)}")
    try:
        if isinstance(raw, str):
            raw = json.loads(raw)

        score = raw.score
        score = float(score)
        score = round(score, 2)
        reasoning = raw.reasoning

    except (TypeError, ValueError, json.JSONDecodeError, AttributeError):
        score = 0.0
        reasoning = ""

    print(f"Debug: output judge generation: {str(score)} with {reasoning}")
    return {"score": score, "reasoning": reasoning}

# =========================
# Internal: Agreement Check
# =========================

def is_consistent(score_a, score_b, tol: float = 0.0) -> bool:
    """
    Check whether two scores are consistent.
    tol = 0.0 means strict equality.
    """
    try:
        return abs(float(score_a) - float(score_b)) <= tol
    except Exception:
        return False


# =========================
# Internal: Round-2 Context
# =========================

def _build_round2_prompt(
    base_prompt: str,
    judge_a: Dict,
    judge_b: Dict,
) -> str:
    """
    Build the second-round prompt with prior judgments as context.
    """
    return f"""
{base_prompt}

Two independent judges previously evaluated the answer.

Judge A:
Score: {judge_a["score"]}
Reasoning: {judge_a["reasoning"]}

Judge B:
Score: {judge_b["score"]}
Reasoning: {judge_b["reasoning"]}

Please independently reassess the student's answer.
Follow the grading rubric strictly.
"""


# =========================
# Public API
# =========================

def multi_agent_judge(
    base_prompt: str,
    system_prompt: str,
    *,
    model: str = "gpt-4o-mini",
    max_tokens: int = 2048,
    score_tolerance: float = 0.25,
) -> Dict[str, object]:
    """
    Run a two-round, two-agent judging process.

    Returns:
    {
        "text": <score or None>,
        "pass": <True if consensus reached, else False>
    }
    """

    # -------- Round 1 --------
    base_prompt_showing = f"{base_prompt[:300]} ... {base_prompt[-300:]}" if len(base_prompt) > 600 else base_prompt
    system_prompt_showing = f"{system_prompt[:300]} ... {system_prompt[-300:]}" if len(system_prompt) > 600 else system_prompt
    print(f"GRADING: base_prompt; {base_prompt_showing}\n")
    print(f"GRADING: system_prompt; {system_prompt_showing}\n")
    judge_a1 = _run_judge(base_prompt, system_prompt, model, max_tokens)
    judge_b1 = _run_judge(base_prompt, system_prompt, model, max_tokens)

    if is_consistent(judge_a1["score"], judge_b1["score"], score_tolerance):
        return {
            "score": judge_a1["score"],
            "reasoning": judge_a1["reasoning"],
            "pass": True
        }

    # -------- Round 2 --------
    round2_prompt = _build_round2_prompt(
        base_prompt,
        judge_a1,
        judge_b1
    )

    judge_a2 = _run_judge(round2_prompt, system_prompt, model, max_tokens)
    judge_b2 = _run_judge(round2_prompt, system_prompt, model, max_tokens)

    if is_consistent(judge_a2["score"], judge_b2["score"], score_tolerance):
        return {
            "score": judge_a2["score"],
            "reasoning": judge_a1["reasoning"],
            "pass": True
        }

    # -------- No consensus --------
    return {
        "score": None,
        "pass": False
    }



def run_score_extract(
    user_prompt: str,
    model: str = "gpt-4o-mini",
    max_tokens: int = 2048,
) -> Dict:
    """
    Run a single judge agent.
    Must return {"score": number, "reasoning": str}
    """
    raw = llm_structured_generate(
        input_text=user_prompt,
        system_text="""You are an assistant. Extract the full score from the grading rubric. The rubric may be plain text, Markdown, or LaTeX. Full score = the maximum non-negative numerical score mentioned. Ignore all negative scores. If no non-negative score exists, return 0. Output only a single number.""",
        model=model,
        max_tokens=max_tokens,
        format_obj=FullScoreOutput,
    )
    
    print(f"Debug: SCORE EXTRACT generation: {str(raw)} with {type(raw)}")
    try:
        if isinstance(raw, str):
            raw = json.loads(raw)
        score = raw.score
        score = float(score)
        score = round(score, 2)
    except (TypeError, ValueError, json.JSONDecodeError, AttributeError):
        score = 0.0
    return {"score": score}