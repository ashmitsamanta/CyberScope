import pytest
from datetime import datetime, timezone, timedelta
from app.utils.normalization import (
    normalize_phone, normalize_domain, normalize_url, normalize_upi, EntityExtractor
)
from app.analyzers.communication_analyzer import CommunicationAnalyzer
from app.analyzers.behavioral_analyzer import BehavioralAnalyzer
from app.analyzers.graph_analyzer import GraphAnalyzer
from app.analyzers.transaction_analyzer import TransactionAnalyzer


def test_phone_normalization():
    assert normalize_phone("+91 90000 00001") == "+919000000001"
    assert normalize_phone("9000000001") == "+919000000001"
    assert normalize_phone("09000000001") == "+919000000001"
    assert normalize_phone("+919000000001") == "+919000000001"


def test_domain_and_url_normalization():
    assert normalize_domain("HTTP://Example.com") == "example.com"
    assert normalize_domain("example.com/") == "example.com"
    assert normalize_domain("https://www.example.com/login") == "example.com"
    assert normalize_url("http://example.com/test/") == "http://example.com/test"


def test_upi_normalization():
    assert normalize_upi("CentralMule99@OKAXIS") == "centralmule99@okaxis"
    assert normalize_upi("  test@upi  ") == "test@upi"


def test_entity_extractor():
    text = "Verify your account at https://secure-kyc-update.com and transfer ₹48,500 to centralmule99@okaxis or call 9000000001."
    res = EntityExtractor.extract_all(text)
    assert "secure-kyc-update.com" in res["domains"]
    assert "centralmule99@okaxis" in res["upi_ids"]
    assert 48500.0 in res["amounts"]
    assert "+919000000001" in res["phones"]


def test_communication_analyzer():
    content = "URGENT: Your SBI bank account will be blocked within 2 hours. Update KYC now at https://fake-bank-auth.xyz or share OTP."
    analysis = CommunicationAnalyzer.analyze(content, url="https://fake-bank-auth.xyz")
    assert analysis["is_suspicious"] is True
    assert analysis["suspicion_score"] >= 50.0
    assert "URGENCY" in analysis["categories"]
    assert "ACCOUNT_THREAT" in analysis["categories"]
    assert "VERIFICATION_SCAM" in analysis["categories"]


def test_behavioral_analyzer_fan_out():
    now = datetime.now(timezone.utc)
    account_id = 100
    txs = [
        {"id": 1, "timestamp": (now - timedelta(minutes=5)).isoformat(), "sender_entity_id": account_id, "receiver_entity_id": 201, "amount": 1000.0},
        {"id": 2, "timestamp": (now - timedelta(minutes=4)).isoformat(), "sender_entity_id": account_id, "receiver_entity_id": 202, "amount": 1000.0},
        {"id": 3, "timestamp": (now - timedelta(minutes=2)).isoformat(), "sender_entity_id": account_id, "receiver_entity_id": 203, "amount": 1000.0},
        {"id": 4, "timestamp": (now - timedelta(minutes=1)).isoformat(), "sender_entity_id": account_id, "receiver_entity_id": 204, "amount": 1000.0},
    ]
    res = BehavioralAnalyzer.analyze_account_transactions(account_id, txs, reference_time=now)
    assert "FAN_OUT" in res["patterns_detected"]
    assert "BURST_VELOCITY" in res["patterns_detected"]


def test_graph_analyzer_circular_flow():
    analyzer = GraphAnalyzer()
    entities = [
        {"id": 1, "value": "A", "normalized_value": "a", "entity_type": "BANK_ACCOUNT", "risk_score": 50},
        {"id": 2, "value": "B", "normalized_value": "b", "entity_type": "BANK_ACCOUNT", "risk_score": 50},
        {"id": 3, "value": "C", "normalized_value": "c", "entity_type": "BANK_ACCOUNT", "risk_score": 50},
    ]
    relationships = [
        {"id": 1, "source_entity_id": 1, "target_entity_id": 2, "relationship_type": "TRANSFERRED_TO"},
        {"id": 2, "source_entity_id": 2, "target_entity_id": 3, "relationship_type": "TRANSFERRED_TO"},
        {"id": 3, "source_entity_id": 3, "target_entity_id": 1, "relationship_type": "TRANSFERRED_TO"},
    ]
    analyzer.build_from_records(entities, relationships)
    cycles = analyzer.detect_circular_flows()
    assert len(cycles) >= 1
    assert cycles[0]["length"] == 3


def test_transaction_analyzer():
    tx = {"amount": 48500.0, "channel": "UPI"}
    sender = {"value": "victim", "risk_score": 10.0}
    receiver = {"value": "mule", "risk_score": 85.0}
    res = TransactionAnalyzer.evaluate_transaction(tx, sender, receiver)
    assert res["is_flagged"] is True
    assert res["risk_score"] >= 40.0
    codes = [s["code"] for s in res["signals"]]
    assert "HIGH_RISK_BENEFICIARY" in codes
    assert "POTENTIAL_STRUCTURING" in codes
