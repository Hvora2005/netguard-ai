"""Documented severity rule used to turn a model prediction into an alert severity.

This is a simple, explicit lookup — not a learned or "AI-decided" severity —
so it can be inspected and adjusted per deployment. Severity is downgraded by
one level when the model's own confidence for that prediction is below
LOW_CONFIDENCE_THRESHOLD, since a low-confidence "critical" call is less
actionable than a high-confidence one.
"""

BENIGN_LABELS = {"benign", "normal", "0"}

SEVERITY_RULES: dict[str, str] = {
    "ddos": "critical",
    "dos": "high",
    "botnet": "critical",
    "brute force": "high",
    "bruteforce": "high",
    "web attack": "high",
    "port scan": "medium",
    "portscan": "medium",
    "malicious": "high",
}

DEFAULT_MALICIOUS_SEVERITY = "medium"
LOW_CONFIDENCE_THRESHOLD = 0.6

SEVERITY_ORDER = ["none", "low", "medium", "high", "critical"]


def resolve_severity(predicted_class: str, confidence: float | None) -> str:
    normalized = predicted_class.strip().lower()
    if normalized in BENIGN_LABELS:
        return "none"

    severity = SEVERITY_RULES.get(normalized, DEFAULT_MALICIOUS_SEVERITY)

    if confidence is not None and confidence < LOW_CONFIDENCE_THRESHOLD:
        idx = max(SEVERITY_ORDER.index(severity) - 1, 1)  # never downgrade below "low"
        severity = SEVERITY_ORDER[idx]

    return severity
