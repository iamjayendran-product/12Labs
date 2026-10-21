"""RICE scoring. Reach is computed from evidence, never typed in.

Reach = sum over distinct accounts in an item's evidence of
clamp(account_arr / median_arr, arr_weight_min, arr_weight_max).
Accounts with no CRM ARR (voice-of-customer or support only) get the minimum weight."""
from statistics import median
from typing import Dict, List, Optional

from pmos.loaders import Company
from pmos.schema import ReachConfig


def account_arr(company: Company) -> Dict[str, int]:
    return {r.account: r.arr_usd for r in company.crm}


def median_arr(arr_by_account: Dict[str, int]) -> float:
    return float(median(arr_by_account.values()))


def reach(evidence: List[Dict], arr_by_account: Dict[str, int], median: float, cfg: ReachConfig) -> Dict:
    breakdown = []
    for account in sorted({e["account"] for e in evidence}):
        arr: Optional[int] = arr_by_account.get(account)
        weight = cfg.arr_weight_min if arr is None else max(
            cfg.arr_weight_min, min(cfg.arr_weight_max, arr / median)
        )
        breakdown.append({"account": account, "arr": arr, "weight": weight})
    return {
        "score": round(sum(b["weight"] for b in breakdown), 2),
        "accounts": len(breakdown),
        "total_arr": sum(b["arr"] or 0 for b in breakdown),
        "breakdown": breakdown,
    }


def rice_score(reach_: float, impact: float, confidence: float, effort_pw: float) -> float:
    if effort_pw <= 0:
        raise ValueError("effort_pw must be > 0")
    return round(reach_ * impact * confidence / effort_pw, 2)


def score_items(items: List[Dict], arr_by_account: Dict[str, int], cfg: ReachConfig) -> List[Dict]:
    """Attach `rice` to each snapshot item (using its `effective` I/C/E); best score first."""
    med = median_arr(arr_by_account)
    scored = []
    for item in items:
        r = reach(item["evidence"], arr_by_account, med, cfg)
        e = item["effective"]
        score = rice_score(r["score"], e["impact"], e["confidence"], e["effort_pw"])
        scored.append({**item, "rice": {"reach": r, "score": score}})
    return sorted(scored, key=lambda i: (-i["rice"]["score"], i["id"]))
