"""Unit tests for decision policy (threshold boundary values)."""
import sys
sys.path.insert(0, "D:/openhands/projects/v2/phishing_ai_master")

from src.policy.decision_policy import decide, LOW_DEFAULT, HIGH_DEFAULT


def test_low_default():
    assert LOW_DEFAULT == 0.25

def test_high_default():
    assert HIGH_DEFAULT == 0.75

def test_boundary_below_low():
    assert decide(0.2499) == "LEGITIMATE"

def test_boundary_at_low():
    assert decide(0.25) == "NEEDS_REVIEW"

def test_boundary_mid():
    assert decide(0.5) == "NEEDS_REVIEW"

def test_boundary_below_high():
    assert decide(0.7499) == "NEEDS_REVIEW"

def test_boundary_at_high():
    assert decide(0.75) == "PHISHING"

def test_low_score():
    assert decide(0.0) == "LEGITIMATE"

def test_high_score():
    assert decide(1.0) == "PHISHING"

def test_none():
    assert decide(None) == "NEEDS_REVIEW"

def test_custom_thresholds():
    assert decide(0.3, low=0.25, high=0.75) == "NEEDS_REVIEW"
    assert decide(0.2, low=0.25, high=0.75) == "LEGITIMATE"
    assert decide(0.8, low=0.25, high=0.75) == "PHISHING"

if __name__ == "__main__":
    test_low_default(); test_high_default()
    test_boundary_below_low(); test_boundary_at_low()
    test_boundary_mid(); test_boundary_below_high(); test_boundary_at_high()
    test_low_score(); test_high_score(); test_none()
    test_custom_thresholds()
    print("All decision policy tests passed.")
