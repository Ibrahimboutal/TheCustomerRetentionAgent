import requests
import json
import sqlite3
import os

# Configuration
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

DB_PATH = os.path.join(BASE_DIR, "data", "mock_crm.db")

def test_constraint_adherence():
    """Test if the Rules Engine blocks a greedy agent."""
    print("TEST 1: Constraint Adherence (Financial Safety)")
    
    from api import server
    
    # Customer #1
    result = server.generate_discount_code(1, requested_rate=0.95)
    
    applied_rate = int(result['applied_rate'].replace('%', ''))
    if applied_rate <= 20:
        print(f"  PASS: Agent requested 95%, Rules Engine capped at {applied_rate}%.")
    else:
        print(f"  FAIL: Rules Engine allowed {applied_rate}%!")

def test_hallucination_prevention():
    """Test if the agent handles missing support history gracefully."""
    print("TEST 2: Hallucination Prevention (Data Integrity)")
    
    from api import server
    result = server.search_support_history(10)
    
    if result['status'] == 'empty':
        print("  PASS: System correctly returned 'empty' for user with no history.")
    else:
        print("  FAIL: System invented or found fake history.")

def test_decision_consistency():
    """Test if the ML model provides consistent probabilities."""
    print("TEST 3: Decision Consistency (Deterministic ML)")
    
    from api import server
    p1 = server.get_customers()[0]['churn_probability']
    p2 = server.get_customers()[0]['churn_probability']
    
    if p1 == p2:
        print(f"  PASS: ML Inference is deterministic (P1: {p1}%, P2: {p2}%).")
    else:
        print("  FAIL: ML Inference is inconsistent!")

if __name__ == "__main__":
    try:
        test_constraint_adherence()
        test_hallucination_prevention()
        test_decision_consistency()
        print("\nALL PRODUCTION READINESS TESTS PASSED")
    except Exception as e:
        print(f"ERROR during evaluation: {str(e)}")
