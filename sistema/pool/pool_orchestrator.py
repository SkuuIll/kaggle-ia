"""Multi-account pool orchestrator. Selects accounts, evaluates rolling quotas, and plans zero-downtime handovers."""
import json, time
from pathlib import Path

BASE = Path(__file__).resolve().parent

def evaluate_candidate_accounts(profiles, base_dir=BASE, exclude=None):
    candidates = []
    base_dir = Path(base_dir)
    for key, p in profiles.items():
        if exclude and key == exclude:
            continue
        if not p.get('enabled', True):
            continue
        cred = base_dir / f"kaggle({p.get('account', 1)}).json"
        if not cred.exists():
            continue
        candidates.append(key)
    return candidates

def rank_pool_accounts(candidates, profiles, quota_data=None, usage_history=None):
    if not candidates:
        return []
    scored = []
    now = time.time()
    for key in candidates:
        p = profiles.get(key, {})
        acc = p.get('account', 1)
        quota_score = 30.0 * 3600  # default: assume full 30h if unmeasured
        if quota_data and str(acc) in quota_data:
            q = quota_data[str(acc)]
            avail = q.get('available_seconds')
            if avail is not None:
                quota_score = float(avail)
        # Factor in last used timestamp: prefer account that has rested longest
        last_used = (usage_history or {}).get(key, 0)
        rest_time = now - last_used
        # Score combines available quota with rest time
        scored.append((quota_score, rest_time, key))
    # Sort descending: highest available quota first, then longest rest
    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [item[2] for item in scored]

def should_prewarm_next(session_elapsed_seconds, max_session_minutes=120, prewarm_lead_seconds=480, quota_remaining_seconds=None):
    max_seconds = max_session_minutes * 60
    # Pre-warm if session is within the lead window (e.g. 8 minutes before session timeout)
    if session_elapsed_seconds >= (max_seconds - prewarm_lead_seconds):
        return True, 'session_limit_approaching'
    # Pre-warm if remaining quota for this account is critical (less than lead window)
    if quota_remaining_seconds is not None and quota_remaining_seconds <= prewarm_lead_seconds:
        return True, 'quota_exhaustion_approaching'
    return False, 'steady'
