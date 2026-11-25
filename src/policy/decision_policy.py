"""Three-way decision policy: PHISHING / LEGITIMATE / NEEDS_REVIEW."""
LOW_DEFAULT = 0.25
HIGH_DEFAULT = 0.75


def decide(score, low=LOW_DEFAULT, high=HIGH_DEFAULT):
    if score is None:
        return "NEEDS_REVIEW"
    s = float(score)
    if s >= high:
        return "PHISHING"
    if s < low:
        return "LEGITIMATE"
    return "NEEDS_REVIEW"
