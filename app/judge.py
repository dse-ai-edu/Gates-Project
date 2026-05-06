import json

from typing import Dict, Tuple

from pydantic import BaseModel

from app.llm_utils import llm_generate

from app.text_prompts import GET_FULL_POINT_PRMPT

from app.data_structure import (
    JudgeOutput,
    FullScoreOutput,
)


# =========================
# LLM main calling
# =========================

def llm_structured_generate(
    user_prompt: str,
    system_prompt: str = None,
    model: str = "gemini-3.1-flash-lite-preview",
    max_retry: int = 3,
    max_tokens: int = 2048,
    format_obj: BaseModel = JudgeOutput,
):

    response = llm_generate(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        model=model,
        text_format=format_obj,
        max_retry=max_retry,
        max_tokens=max_tokens,
    )

    if response.obj is None:
        raise ValueError(
            "Structured output missing from LLM."
        )

    return response.obj


# =========================
# Internal: Single Judge
# =========================

def _run_judge(
    user_prompt: str,
    system_prompt: str,
    model: str = "gemini-3.1-flash-lite-preview",
    max_tokens: int = 2048,
) -> Dict:

    raw = llm_structured_generate(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        model=model,
        max_tokens=max_tokens,
        format_obj=JudgeOutput,
    )

    print(
        f"Debug: raw judge generation: "
        f"{str(raw)} with {type(raw)}"
    )

    try:

        if isinstance(raw, BaseModel):
            raw_dict = raw.model_dump()

        elif isinstance(raw, dict):
            raw_dict = raw

        elif isinstance(raw, str):
            raw_dict = json.loads(raw)

        else:
            raise TypeError(
                f"Unsupported raw type: {type(raw)}"
            )

        score = raw_dict["score"]

        score = float(score)

        score = round(score, 2)

        reasoning = raw_dict["reasoning"]

    except (
        TypeError,
        ValueError,
        json.JSONDecodeError,
        AttributeError,
        KeyError,
    ):

        score = 0.0

        reasoning = ""

    print(
        f"Debug: output judge generation: "
        f"{str(score)} with {reasoning}"
    )

    return {
        "score": score,
        "reasoning": reasoning,
    }


# =========================
# Internal: Agreement Check
# =========================

def is_consistent(
    score_a,
    score_b,
    tol: float = 0.0,
) -> bool:

    try:
        return (
            abs(float(score_a) - float(score_b))
            <= tol
        )

    except Exception:
        return False


# =========================
# Public API
# =========================

def multi_agent_judge(
    base_prompt: str,
    system_prompt: str,
    *,
    model: str = "gemini-3.1-flash-lite-preview",
    max_tokens: int = 2048,
    score_tolerance: float = 0.25,
) -> Dict[str, object]:

    dialogue_history = [
        "** History of Multi-agent Debate, Round 1 \n"
    ]

    dialogue_round_template = (
        "* [{}] `Score`: `{}`, "
        "`Reasoning`: `{}` \n"
    )

    base_prompt_showing = (
        f"{base_prompt[:300]} ... "
        f"{base_prompt[-300:]}"
        if len(base_prompt) > 600
        else base_prompt
    )

    system_prompt_showing = (
        f"{system_prompt[:300]} ... "
        f"{system_prompt[-300:]}"
        if len(system_prompt) > 600
        else system_prompt
    )

    print(
        f"GRADING: base_prompt; "
        f"{base_prompt_showing}\n"
    )

    print(
        f"GRADING: system_prompt; "
        f"{system_prompt_showing}\n"
    )

    judge_a1 = _run_judge(
        base_prompt,
        system_prompt,
        model,
        max_tokens,
    )

    judge_b1 = _run_judge(
        base_prompt,
        system_prompt,
        model,
        max_tokens,
    )

    base_prompt_shorten = (
        base_prompt.replace("\n\n", "\n")
    )

    dialogue_history.append(
        f"* Instruction to Agent: "
        f"{base_prompt_shorten} \n"
    )

    dialogue_history.append(
        dialogue_round_template.format(
            "Judge A - Round 1",
            judge_a1["score"],
            judge_a1["reasoning"],
        )
    )

    dialogue_history.append(
        dialogue_round_template.format(
            "Judge B - Round 1",
            judge_b1["score"],
            judge_b1["reasoning"],
        )
    )

    if is_consistent(
        judge_a1["score"],
        judge_b1["score"],
        score_tolerance,
    ):

        dialogue_history.append(
            dialogue_round_template.format(
                "Final Result",
                judge_a1["score"],
                judge_a1["reasoning"],
            )
        )

        return {
            "score": judge_a1["score"],
            "reasoning": judge_a1["reasoning"],
            "pass": True,
            "dialogue_history": dialogue_history,
        }

    from text_prompts import JUDGE_ROUND_2

    round2_datapackage = {
        "base_prompt": base_prompt,
        "score_a": judge_a1["score"],
        "score_b": judge_b1["score"],
        "reasoning_a": judge_a1["reasoning"],
        "reasoning_b": judge_b1["reasoning"],
    }

    round2_prompt = JUDGE_ROUND_2.format(
        **round2_datapackage
    )

    judge_a2 = _run_judge(
        round2_prompt,
        system_prompt,
        model,
        max_tokens,
    )

    judge_b2 = _run_judge(
        round2_prompt,
        system_prompt,
        model,
        max_tokens,
    )

    dialogue_history.append(
        "** History of Multi-agent Debate, "
        "Round 2: \n"
    )

    round2_prompt_shorten = (
        round2_prompt.replace("\n\n", "\n")
    )

    dialogue_history.append(
        f"** Additional Instruction to Agent: "
        f"{round2_prompt_shorten} \n"
    )

    dialogue_history.append(
        dialogue_round_template.format(
            "Judge A - Round 2",
            judge_a2["score"],
            judge_a2["reasoning"],
        )
    )

    dialogue_history.append(
        dialogue_round_template.format(
            "Judge B - Round 2",
            judge_b2["score"],
            judge_b2["reasoning"],
        )
    )

    if is_consistent(
        judge_a2["score"],
        judge_b2["score"],
        score_tolerance,
    ):

        dialogue_history.append(
            dialogue_round_template.format(
                "Final Result",
                judge_a2["score"],
                judge_a2["reasoning"],
            )
        )

        return {
            "score": judge_a2["score"],
            "reasoning": judge_a2["reasoning"],
            "pass": True,
            "dialogue_history": dialogue_history,
        }

    return {
        "score": None,
        "pass": False,
        "dialogue_history": dialogue_history,
    }


# =========================
# Full Score Extract
# =========================

def run_score_extract(
    user_prompt: str,
    model: str = "gemini-3.1-flash-lite-preview",
    max_tokens: int = 2048,
) -> Dict:

    print(
        f"Debug: BEFORE FULL SCORE EXTRACT: "
        f"{user_prompt}"
    )

    raw = llm_structured_generate(
        user_prompt=user_prompt,
        system_prompt=GET_FULL_POINT_PRMPT,
        model=model,
        max_tokens=max_tokens,
        format_obj=FullScoreOutput,
    )

    print(
        f"Debug: FULL SCORE EXTRACT TMP: "
        f"{str(raw)} with {type(raw)}"
    )

    try:

        if isinstance(raw, BaseModel):
            raw_dict = raw.model_dump()

        elif isinstance(raw, dict):
            raw_dict = raw

        elif isinstance(raw, str):
            raw_dict = json.loads(raw)

        else:
            raise TypeError(
                f"Unsupported raw type: {type(raw)}"
            )

        score = raw_dict["score"]

        score = float(score)

        score = round(score, 2)

    except (
        TypeError,
        ValueError,
        json.JSONDecodeError,
        AttributeError,
        KeyError,
    ):

        score = 0.0

    print(
        f"Debug: FULL SCORE EXTRACT FINAL: "
        f"{score}"
    )

    return {
        "score": score,
    }