import json
import os

from typing import Dict, Tuple

from pydantic import BaseModel

from app.config import Config
from app.prompts import GET_FULL_POINT_PRMPT
# =========================

# Assumed total/full score when a rubric does not explicitly state one.
DEFAULT_FULL_SCORE = 5.0

class JudgeOutput(BaseModel):
    score: float
    reasoning: str

class FullScoreOutput(BaseModel):
    score: float

# LLM main calling
def llm_structured_generate(
    input_text: str,
    system_text: str = None,
    model: str = Config.GEMINI_MODEL_LOW,
    max_retry: int = 3,
    max_tokens: int = 2048,
    format_obj: BaseModel = JudgeOutput
    ) -> str:
    from google import genai
    from google.genai import types

    api_key = os.getenv("GOOGLE_API_KEY")

    config = {
        "system_instruction": str(system_text) if system_text is not None else None,
        "max_output_tokens": max_tokens,
        "response_mime_type": "application/json",
        "response_json_schema": format_obj.model_json_schema(),
    }

    for _ in range(max_retry):
        print(f"[SYS] Num of Try: {_}:")
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model,
                contents=[types.Part.from_text(str(input_text))],
                config=config,
                )
            parsed_output = format_obj.model_validate_json(response.text)
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
    model: str = Config.GEMINI_MODEL_LOW,
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
    model: str = Config.GEMINI_MODEL_LOW,
    max_tokens: int = 2048,
    score_tolerance: float = 0.25,
) -> Dict[str, object]:
    dialogue_history = ["** History of Multi-agent Debate, Round 1 \n"]
    dialogue_round_template = "* [{}] `Score`: `{}`, `Reasoning`: `{}` \n"
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

    base_prompt_shorten = base_prompt.replace("\n\n", "\n")
    dialogue_history.append(f"""* Instruction to Agent: {base_prompt_shorten} \n""")
    dialogue_history.append(dialogue_round_template.format("Judge A - Round 1", judge_a1['score'], judge_a1['reasoning']))
    dialogue_history.append(dialogue_round_template.format("Judge B - Round 1", judge_b1['score'], judge_b1['reasoning']))
    
    if is_consistent(judge_a1["score"], judge_b1["score"], score_tolerance):
        dialogue_history.append(dialogue_round_template.format("Final Result", judge_a1['score'], judge_a1['reasoning']))
        return {
            "score": judge_a1["score"],
            "reasoning": judge_a1["reasoning"],
            "pass": True, 
            "dialogue_history": dialogue_history
        }

    # -------- Round 2 --------
    round2_prompt = _build_round2_prompt(
        base_prompt,
        judge_a1,
        judge_b1
    )

    
    judge_a2 = _run_judge(round2_prompt, system_prompt, model, max_tokens)
    judge_b2 = _run_judge(round2_prompt, system_prompt, model, max_tokens)
    
    dialogue_history.append(f"** History of Multi-agent Debate, Round 2: \n")
    round2_prompt_shorten = round2_prompt.replace("\n\n", "\n")
    dialogue_history.append(f"""** Additional Instruction to Agent: {round2_prompt_shorten} \n""")

    dialogue_history.append(dialogue_round_template.format("Judge A - Round 2", judge_a2['score'], judge_a2['reasoning']))
    dialogue_history.append(dialogue_round_template.format("Judge B - Round 2", judge_b2['score'], judge_b2['reasoning']))
    
    if is_consistent(judge_a2["score"], judge_b2["score"], score_tolerance):
        dialogue_history.append(dialogue_round_template.format("Final Result", judge_a2['score'], judge_a2['reasoning']))
        return {
            "score": judge_a2["score"],
            "reasoning": judge_a1["reasoning"],
            "pass": True,
            "dialogue_history": dialogue_history
        }

    # -------- No consensus --------
    return {
        "score": None,
        "pass": False,
        "dialogue_history": dialogue_history
    }



def run_score_extract(
    user_prompt: str,
    model: str = Config.GEMINI_MODEL_LOW,
    max_tokens: int = 2048,
) -> Dict:
    """
    Run a single judge agent.
    Must return {"score": number, "reasoning": str}
    """
    print(f"Debug: BEFORE FULL SCORE EXTRACT: {user_prompt}")
    raw = llm_structured_generate(
        input_text=user_prompt,
        system_text=GET_FULL_POINT_PRMPT,
        model=model,
        max_tokens=max_tokens,
        format_obj=FullScoreOutput,
    )
    print(f"Debug: FULL SCORE EXTRACT TMP: {str(raw)} with {type(raw)}")
    try:
        if isinstance(raw, str):
            raw = json.loads(raw)
        score = raw.score
        score = float(score)
        score = round(score, 2)
    except (TypeError, ValueError, json.JSONDecodeError, AttributeError):
        score = 0.0
    print(f"Debug: FULL SCORE EXTRACT FINAL: {score}")
    return {"score": score}