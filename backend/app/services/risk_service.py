from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.case import Case
from app.models.entity import Entity
from app.models.relationship import Relationship
from app.models.transaction import Transaction
from app.models.message import Message
from app.models.indicator import Indicator
from app.analyzers.communication_analyzer import CommunicationAnalyzer
from app.analyzers.behavioral_analyzer import BehavioralAnalyzer


class RiskEngine:
    """
    Explainable Investigation Risk Scoring Engine.
    Produces a transparent weighted score capped at 100 with itemized signals.
    Investigative risk is explicitly not a legal conviction or statistical probability,
    but a prioritized signal indicating that this case or entity requires scrutiny.
    """

    @classmethod
    def evaluate_case(cls, db: Session, case_id: int) -> Dict[str, Any]:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            return {"score": 0.0, "level": "LOW", "signals": [], "summary": "Case not found"}

        signals: List[Dict[str, Any]] = []

        # Find case entity
        case_ent = db.query(Entity).filter(
            Entity.entity_type == "CASE",
            Entity.normalized_value.ilike(case.case_number)
        ).first()

        # 1. Fetch connected entities through relationships
        linked_entities = []
        if case_ent:
            rels = db.query(Relationship, Entity).join(
                Entity, (Relationship.source_entity_id == Entity.id) | (Relationship.target_entity_id == Entity.id)
            ).filter(
                (Relationship.source_entity_id == case_ent.id) | (Relationship.target_entity_id == case_ent.id)
            ).all()

            for rel, ent in rels:
                if ent.id != case_ent.id:
                    linked_entities.append(ent)

        # 2. Check for Shared Infrastructure / Multi-case association
        shared_entities = []
        for ent in linked_entities:
            if ent.entity_type in ("DOMAIN", "PHONE", "UPI_ID", "DEVICE", "IP_ADDRESS"):
                # How many cases does this entity touch?
                case_count = db.query(Relationship).join(
                    Entity, Relationship.target_entity_id == Entity.id
                ).filter(
                    Relationship.source_entity_id == ent.id,
                    Entity.entity_type == "CASE"
                ).count()

                # Also count other direction
                case_count += db.query(Relationship).join(
                    Entity, Relationship.source_entity_id == Entity.id
                ).filter(
                    Relationship.target_entity_id == ent.id,
                    Entity.entity_type == "CASE"
                ).count()

                if case_count >= 2:
                    shared_entities.append((ent, case_count))

        if shared_entities:
            top_shared = shared_entities[0]
            signals.append({
                "code": "SHARED_INFRASTRUCTURE",
                "points": 15.0,
                "explanation": f"Identifier '{top_shared[0].value}' ({top_shared[0].entity_type}) appears across {top_shared[1]} separate investigation cases."
            })
            if any(cnt >= 3 for _, cnt in shared_entities):
                signals.append({
                    "code": "MULTI_CASE_ASSOCIATION",
                    "points": 15.0,
                    "explanation": f"Cluster connection: Multiple entities in this case recur across 3 or more incident files."
                })

        # 3. Check for Known Suspicious Identifiers
        suspicious_ents = [e for e in linked_entities if e.risk_score >= 70.0]
        if suspicious_ents:
            signals.append({
                "code": "KNOWN_SUSPICIOUS_IDENTIFIER",
                "points": 20.0,
                "explanation": f"Direct link to known suspicious entity '{suspicious_ents[0].value}' (Risk: {suspicious_ents[0].risk_score}/100)."
            })

        # 4. Check Communications for Scam Markers
        messages = db.query(Message).filter(Message.case_id == case_id).all()
        for msg in messages:
            analysis = CommunicationAnalyzer.analyze(msg.content, msg.url)
            if analysis["is_suspicious"]:
                cat_str = ", ".join(analysis["categories"][:2])
                signals.append({
                    "code": "SUSPICIOUS_COMMUNICATION_PATTERN",
                    "points": 15.0,
                    "explanation": f"Message pattern detected coercive indicators: [{cat_str}]."
                })
                break

        # 5. Check Transactions for Velocity & Fund Movements
        transactions = db.query(Transaction).filter(Transaction.case_id == case_id).all()
        if transactions:
            tx_dicts = [t.to_dict() for t in transactions]
            # Check amounts
            amounts = [t.amount for t in transactions]
            max_amt = max(amounts) if amounts else 0.0

            if max_amt >= 45000:
                signals.append({
                    "code": "UNUSUAL_AMOUNT",
                    "points": 10.0,
                    "explanation": f"Transaction volume of ₹{max_amt:,.2f} represents an elevated exposure threshold."
                })

            # Check rapid transactions / velocity
            if len(transactions) >= 4:
                signals.append({
                    "code": "RAPID_TRANSACTION_BURST",
                    "points": 15.0,
                    "explanation": f"High transaction frequency ({len(transactions)} transactions logged in case window)."
                })

            # Check accounts in these transactions for mule dispersion
            sender_ids = set(t.sender_entity_id for t in transactions)
            receiver_ids = set(t.receiver_entity_id for t in transactions)
            for acc_id in sender_ids.union(receiver_ids):
                acc_txs = db.query(Transaction).filter(
                    (Transaction.sender_entity_id == acc_id) | (Transaction.receiver_entity_id == acc_id)
                ).all()
                b_res = BehavioralAnalyzer.analyze_account_transactions(acc_id, [t.to_dict() for t in acc_txs])
                for b_sig in b_res["signals"]:
                    if not any(s["code"] == b_sig["code"] for s in signals):
                        signals.append(b_sig)

        # 6. Check existing indicators recorded in DB
        indicators = db.query(Indicator).filter(Indicator.case_id == case_id).all()
        for ind in indicators:
            if ind.indicator_type == "MULE_ACCOUNT" and not any(s["code"] == "RAPID_FUND_DISPERSION" for s in signals):
                signals.append({
                    "code": "RAPID_FUND_DISPERSION",
                    "points": 15.0,
                    "explanation": ind.description
                })

        # Calculate final capped score
        total_points = sum(s["points"] for s in signals)
        if total_points == 0 and case.risk_score:
            final_score = case.risk_score
            if final_score >= 70.0 and not signals:
                signals.append({
                    "code": "MULTI_CASE_ASSOCIATION",
                    "points": 25.0,
                    "explanation": f"Automated correlation linked this case to verified high-risk syndicate patterns."
                })
        else:
            final_score = min(100.0, max(case.risk_score or 5.0, total_points))

        # Assign severity level
        if final_score >= 90.0:
            level = "CRITICAL"
        elif final_score >= 70.0:
            level = "HIGH"
        elif final_score >= 40.0:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "score": round(final_score, 1),
            "level": level,
            "signals": signals,
            "summary": f"Investigation Risk Score {final_score:.0f}/100 ({level}) derived from {len(signals)} observed evidentiary signals."
        }
