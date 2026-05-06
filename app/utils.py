import base64

import json
from pathlib import Path
from typing import Union, List

import os
import html
import re



def find_app_dir(max_depth=3):
    start = Path(__file__).resolve().parent
    cur = start
    for _ in range(max_depth + 1):
        candidate = cur / "app"
        if candidate.exists():
            return candidate.resolve()
        if cur.parent == cur:
            break
        cur = cur.parent
    for depth in range(1, max_depth + 1):
        for p in start.rglob("app"):
            try:
                if len(p.relative_to(start).parts) <= depth:
                    return p.resolve()
            except ValueError:
                continue
    return start


def longest_common_substring_len(a: str, b: str) -> int:
    a, b = a.lower(), b.lower()
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    best = 0
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                best = max(best, dp[i][j])
    return best


def best_match_by_lcs(query: str, candidates: list) -> str | None:
    best_score, best_candidate = 0, None
    for c in candidates:
        score = longest_common_substring_len(query, c)
        if score > best_score:
            best_score = score
            best_candidate = c
    return best_candidate


def format_response_html(response_text: str = "Placeholder of Response.", certainty_score: str|float = 0):
    ## text
    html_text = html.escape(response_text)
    html_text = html_text.replace('\n', '<br>')
    html_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_text)
    
    ## conf
    certainty_score_default = -1
    case = 0
    if certainty_score is not None:
        if isinstance(certainty_score, float) and certainty_score>100:
            processed_certainty_score = float(certainty_score)
            processed_certainty_score = f"{processed_certainty_score:.2e}"
            case = 1
        elif isinstance(certainty_score, float):
            processed_certainty_score = float(certainty_score)
            processed_certainty_score = round(processed_certainty_score, 4)
            case = 2
        elif isinstance(certainty_score, int):
            processed_certainty_score = certainty_score
            case = 3
        else:
            processed_certainty_score = str(certainty_score)[:6]
            case = 4
        print(f">>9>>>Case{case}: {certainty_score} to {processed_certainty_score}; {type(processed_certainty_score)}")
    else:
        processed_certainty_score = -999
        
    # ppl_note = "*NOTE - PPL=1: fully certainty; - PPL→∞: increasing uncertainty."
    
    # confidence_display =f'<span style="color:#fb827a;font-weight:bold;">[PPL: {processed_certainty_score}] {ppl_note} </span>'
    # formatted_html = f"{html_text} <br> ----- <br> {confidence_display}"
    # return formatted_html
    return html_text