import os
import json
import hashlib
from datetime import datetime, timedelta
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib

from app.database import engine, Base, SessionLocal
from app.models.customer import Customer
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.loan import LoanApplication
from app.models.fraud import FraudAlert
from app.models.approval import ApprovalRequest
from app.models.policy import PolicyDocument
from app.models.notification import Notification
from app.models.audit import AuditEvent
from app.models.user import User
from app.services.security import hash_password

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "services", "models")
POLICIES_DIR = os.path.join(os.path.dirname(__file__), "policies")

def compute_payload_hash(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def calculate_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    if annual_rate == 0 or tenure_months == 0:
        return round(principal / max(1, tenure_months), 2)
    r = (annual_rate / 100.0) / 12.0
    emi = principal * r * ((1 + r) ** tenure_months) / (((1 + r) ** tenure_months) - 1)
    return round(emi, 2)

def train_and_save_isolation_forest(transactions: list[dict]):
    """Fit IsolationForest reproducibly on transaction features with fixed seed."""
    os.makedirs(MODEL_DIR, exist_ok=True)
    model_path = os.path.join(MODEL_DIR, "isolation_forest.joblib")
    
    # Feature extraction: [normalized_amount, hour_of_day, day_of_week, tx_frequency]
    features = []
    for tx in transactions:
        dt = tx["timestamp"]
        norm_amt = float(tx["amount"]) / 10000.0
        hour = float(dt.hour)
        dow = float(dt.weekday())
        # synthetic frequency indicator
        freq = 1.0 if not tx.get("is_flagged", False) else 5.0
        features.append([norm_amt, hour, dow, freq])

    X = np.array(features)
    # contamination = 0.05
    iso_forest = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    iso_forest.fit(X)
    joblib.dump(iso_forest, model_path)
    return iso_forest

def seed_users(db):
    """Seed demo users idempotently (independent of the main data seed skip)."""
    users_seed = [
        ("USR1001", "manager", "Branch Manager (Demo)", "manager", "Manager@123"),
        ("USR1002", "risk_analyst", "Risk Analyst (Demo)", "risk_analyst", "Risk@123"),
        ("USR1003", "compliance_officer", "Compliance Officer (Demo)", "compliance_officer", "Compliance@123"),
    ]
    for uid, username, display_name, role, password in users_seed:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            continue
        db.add(User(id=uid, username=username, display_name=display_name, role=role, password_hash=hash_password(password)))
    db.flush()

def seed_database(force_reset: bool = False):
    """Seed synthetic banking data idempotently."""
    if force_reset:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Demo users are always ensured (independent seed, idempotent by username).
        seed_users(db)
        db.commit()

        # Check if already seeded
        existing_customers = db.query(Customer).count()
        if existing_customers >= 15 and not force_reset:
            print("Database already contains >= 15 customers. Skipping seed.")
            return

        print("Seeding synthetic banking intelligence database...")
        now = datetime.utcnow()

        # 1. Seed 15 Customers
        customers_data = [
            ("CUST1001", "Aarav Sharma", "aarav.sharma@example.com", "+91-98201-11221", "VERIFIED", "LOW", 125000.0, 15000.0, "Tech Mahindra", "Mumbai"),
            ("CUST1002", "Priya Patel", "priya.patel@example.com", "+91-98201-22332", "VERIFIED", "LOW", 95000.0, 8000.0, "Infosys", "Bengaluru"),
            ("CUST1003", "Rohan Mehta", "rohan.mehta@example.com", "+91-98201-33443", "VERIFIED", "HIGH", 70000.0, 32000.0, "Fintech Ventures", "Delhi"),
            ("CUST1004", "Ananya Iyer", "ananya.iyer@example.com", "+91-98201-44554", "PENDING", "MEDIUM", 60000.0, 5000.0, "Tata Consultancy", "Chennai"),
            ("CUST1005", "Vikram Verma", "vikram.verma@example.com", "+91-98201-55665", "VERIFIED", "MEDIUM", 110000.0, 28000.0, "HDFC Life", "Pune"),
            ("CUST1006", "Sneha Reddy", "sneha.reddy@example.com", "+91-98201-66776", "VERIFIED", "LOW", 140000.0, 12000.0, "Dr Reddy Labs", "Hyderabad"),
            ("CUST1007", "Kabir Sen", "kabir.sen@example.com", "+91-98201-77887", "VERIFIED", "HIGH", 45000.0, 24000.0, "Freelance Agency", "Kolkata"),
            ("CUST1008", "Neha Deshmukh", "neha.deshmukh@example.com", "+91-98201-88998", "VERIFIED", "LOW", 85000.0, 9000.0, "L&T Infotech", "Mumbai"),
            ("CUST1009", "Arjun Nair", "arjun.nair@example.com", "+91-98201-99009", "REJECTED", "HIGH", 35000.0, 18000.0, "Self Employed", "Kochi"),
            ("CUST1010", "Pooja Joshi", "pooja.joshi@example.com", "+91-98202-00110", "VERIFIED", "LOW", 180000.0, 22000.0, "Amazon India", "Bengaluru"),
            ("CUST1011", "Aditya Kapoor", "aditya.kapoor@example.com", "+91-98202-11223", "VERIFIED", "MEDIUM", 90000.0, 14000.0, "Airtel", "Gurugram"),
            ("CUST1012", "Divya Menon", "divya.menon@example.com", "+91-98202-22334", "VERIFIED", "LOW", 130000.0, 10000.0, "Wipro", "Bengaluru"),
            ("CUST1013", "Siddharth Rao", "siddharth.rao@example.com", "+91-98202-33445", "PENDING", "MEDIUM", 55000.0, 12000.0, "Retail Traders", "Ahmedabad"),
            ("CUST1014", "Meera Pillai", "meera.pillai@example.com", "+91-98202-44556", "VERIFIED", "LOW", 160000.0, 18000.0, "Reliance Retail", "Mumbai"),
            ("CUST1015", "Kunal Bhatia", "kunal.bhatia@example.com", "+91-98202-55667", "VERIFIED", "LOW", 105000.0, 11000.0, "Maruti Suzuki", "Delhi"),
        ]

        for cid, name, email, phone, kyc, risk, inc, debt, emp, city in customers_data:
            cust = Customer(
                id=cid, name=name, email=email, phone=phone,
                kyc_status=kyc, risk_rating=risk, monthly_income=inc,
                existing_monthly_debt=debt, employer=emp, city=city,
                created_at=now - timedelta(days=90)
            )
            db.merge(cust)

        # 2. Seed 25 Accounts
        accounts_data = [
            ("ACC2001", "CUST1001", "SB-1001-9821", "SAVINGS", 824500.00, "ACTIVE"),
            ("ACC2002", "CUST1001", "FD-1001-4412", "FIXED_DEPOSIT", 500000.00, "ACTIVE"),
            ("ACC2003", "CUST1002", "SB-1002-3142", "SAVINGS", 312400.00, "ACTIVE"),
            ("ACC2004", "CUST1003", "SB-1003-8871", "SAVINGS", 48600.00, "ACTIVE"),
            ("ACC2005", "CUST1003", "CA-1003-9910", "CHECKING", 12500.00, "ACTIVE"),
            ("ACC2006", "CUST1004", "SB-1004-1234", "SAVINGS", 74200.00, "ACTIVE"),
            ("ACC2007", "CUST1005", "SB-1005-5561", "SAVINGS", 418900.00, "ACTIVE"),
            ("ACC2008", "CUST1006", "SB-1006-7782", "SAVINGS", 632100.00, "ACTIVE"),
            ("ACC2009", "CUST1007", "SB-1007-9911", "SAVINGS", 15400.00, "ACTIVE"),
            ("ACC2010", "CUST1008", "SB-1008-2231", "SAVINGS", 245000.00, "ACTIVE"),
            ("ACC2011", "CUST1009", "SB-1009-4419", "SAVINGS", 8900.00, "FROZEN"),
            ("ACC2012", "CUST1010", "SB-1010-6622", "SAVINGS", 1120000.00, "ACTIVE"),
            ("ACC2013", "CUST1010", "FD-1010-8833", "FIXED_DEPOSIT", 1000000.00, "ACTIVE"),
            ("ACC2014", "CUST1011", "SB-1011-1144", "SAVINGS", 215000.00, "ACTIVE"),
            ("ACC2015", "CUST1012", "SB-1012-3355", "SAVINGS", 380000.00, "ACTIVE"),
            ("ACC2016", "CUST1013", "SB-1013-5566", "SAVINGS", 62000.00, "ACTIVE"),
            ("ACC2017", "CUST1014", "SB-1014-7788", "SAVINGS", 540000.00, "ACTIVE"),
            ("ACC2018", "CUST1015", "SB-1015-9900", "SAVINGS", 290000.00, "ACTIVE"),
            ("ACC2019", "CUST1002", "FD-1002-8821", "FIXED_DEPOSIT", 200000.00, "ACTIVE"),
            ("ACC2020", "CUST1005", "CA-1005-7734", "CHECKING", 85000.00, "ACTIVE"),
            ("ACC2021", "CUST1006", "CA-1006-2219", "CHECKING", 150000.00, "ACTIVE"),
            ("ACC2022", "CUST1008", "FD-1008-9941", "FIXED_DEPOSIT", 300000.00, "ACTIVE"),
            ("ACC2023", "CUST1011", "CA-1011-4451", "CHECKING", 45000.00, "ACTIVE"),
            ("ACC2024", "CUST1012", "FD-1012-6671", "FIXED_DEPOSIT", 250000.00, "ACTIVE"),
            ("ACC2025", "CUST1014", "CA-1014-8891", "CHECKING", 120000.00, "DORMANT"),
        ]

        for aid, cid, num, atype, bal, status in accounts_data:
            acc = Account(
                id=aid, customer_id=cid, account_number=num,
                account_type=atype, balance=bal, currency="INR",
                status=status, created_at=now - timedelta(days=80)
            )
            db.merge(acc)

        # 3. Seed 130+ Transactions with specific suspicious scenarios
        raw_tx_records = []
        tx_counter = 4001

        # Base categories and merchants
        categories = [
            ("Salary", "Corporate Payroll Hub", "CREDIT"),
            ("Groceries", "Nature's Basket", "DEBIT"),
            ("Utility", "Tata Power Distribution", "DEBIT"),
            ("Dining", "Copper Chimney", "DEBIT"),
            ("Shopping", "Amazon India", "DEBIT"),
            ("Travel", "MakeMyTrip India", "DEBIT"),
            ("Transfer", "UPI Payment", "DEBIT"),
        ]

        # Generate realistic transaction history for each customer
        tx_dict = {}
        for cid, _, _, _, _, _, inc, _, _, city in customers_data:
            aid = f"ACC{2000 + int(cid.replace('CUST10', ''))}"
            # Monthly salary credit
            tx_id = f"TXN{tx_counter}"
            tx_dict[tx_id] = {
                "id": tx_id, "account_id": aid, "customer_id": cid,
                "amount": inc, "txn_type": "CREDIT", "category": "Salary",
                "merchant_name": "Corporate Payroll", "location": f"{city}, IN",
                "status": "COMPLETED", "timestamp": now - timedelta(days=28),
                "is_flagged": False, "description": "Monthly Salary Credit"
            }
            tx_counter += 1

            # Regular routine transactions
            amounts = [1250.0, 3400.0, 850.0, 4200.0, 2100.0, 680.0, 5500.0]
            for i, amt in enumerate(amounts):
                cat, mer, ttype = categories[(i % (len(categories) - 1)) + 1]
                t_id = f"TXN{tx_counter}"
                tx_dict[t_id] = {
                    "id": t_id, "account_id": aid, "customer_id": cid,
                    "amount": amt, "txn_type": ttype, "category": cat,
                    "merchant_name": mer, "location": f"{city}, IN",
                    "status": "COMPLETED", "timestamp": now - timedelta(days=25 - i * 3, hours=i * 2),
                    "is_flagged": False, "description": f"Routine {cat} purchase"
                }
                tx_counter += 1

        # Specific Key Test Scenarios (Overwrite specific IDs cleanly):
        # Scenario A: TXN4008 - Huge Transfer Spike for CUST1001 (Amount: 450000.0)
        tx_dict["TXN4008"] = {
            "id": "TXN4008",
            "account_id": "ACC2001",
            "customer_id": "CUST1001",
            "amount": 450000.0,
            "txn_type": "DEBIT",
            "category": "Transfer",
            "merchant_name": "Offshore Remittance Gateway",
            "location": "Limassol, CY",
            "status": "COMPLETED",
            "timestamp": now - timedelta(days=2, hours=3),
            "is_flagged": True,
            "description": "Unusually high value outward transfer spike"
        }

        # Scenario B: Velocity Burst for CUST1003 (TXN4015, TXN4016, TXN4017, TXN4018)
        burst_base_time = now - timedelta(hours=14)
        for idx, t_id in enumerate(["TXN4015", "TXN4016", "TXN4017", "TXN4018"]):
            tx_dict[t_id] = {
                "id": t_id,
                "account_id": "ACC2004",
                "customer_id": "CUST1003",
                "amount": 18500.0,
                "txn_type": "DEBIT",
                "category": "Shopping",
                "merchant_name": "QuickPay Wallet",
                "location": "Delhi, IN",
                "status": "COMPLETED",
                "timestamp": burst_base_time + timedelta(minutes=idx * 2),
                "is_flagged": True,
                "description": f"High velocity burst transaction #{idx+1}"
            }

        # Scenario C: Duplicate Charge Anomaly for CUST1005 (TXN4022, TXN4023)
        dup_time = now - timedelta(days=1, hours=5)
        for idx, t_id in enumerate(["TXN4022", "TXN4023"]):
            tx_dict[t_id] = {
                "id": t_id,
                "account_id": "ACC2007",
                "customer_id": "CUST1005",
                "amount": 12999.0,
                "txn_type": "DEBIT",
                "category": "Shopping",
                "merchant_name": "Croma Electronics",
                "location": "Pune, IN",
                "status": "COMPLETED",
                "timestamp": dup_time + timedelta(seconds=idx * 45),
                "is_flagged": True if idx == 1 else False,
                "description": "Duplicate payment charge within 45 seconds"
            }

        # Scenario D: Repeated Failed Payments for CUST1007 (TXN4030, TXN4031, TXN4032)
        fail_time = now - timedelta(hours=8)
        for idx, t_id in enumerate(["TXN4030", "TXN4031", "TXN4032"]):
            tx_dict[t_id] = {
                "id": t_id,
                "account_id": "ACC2009",
                "customer_id": "CUST1007",
                "amount": 50000.0,
                "txn_type": "DEBIT",
                "category": "Transfer",
                "merchant_name": "CryptoExchange Portal",
                "location": "Kolkata, IN",
                "status": "FAILED",
                "timestamp": fail_time + timedelta(minutes=idx * 4),
                "is_flagged": True,
                "description": "Repeated failed debit exceeding account liquidity"
            }

        raw_tx_records = list(tx_dict.values())

        # Save all transactions
        for tx in raw_tx_records:
            t_obj = Transaction(
                id=tx["id"], account_id=tx["account_id"], customer_id=tx["customer_id"],
                amount=tx["amount"], txn_type=tx["txn_type"], category=tx["category"],
                merchant_name=tx["merchant_name"], location=tx["location"],
                status=tx["status"], timestamp=tx["timestamp"],
                is_flagged=tx["is_flagged"], description=tx["description"]
            )
            db.merge(t_obj)

        # 4. Train Isolation Forest and save to disk
        train_and_save_isolation_forest(raw_tx_records)

        # 5. Seed Initial Fraud Alerts for known suspicious scenarios
        alerts_seed = [
            (
                "ALERT5001", "TXN4008", "CUST1001", 88, "HIGH",
                json.dumps(["High amount vs historical baseline (>3x median)", "Unusual foreign merchant location"]),
                0.28, 1,
                json.dumps({"historical_median": 3400.0, "observed_amount": 450000.0, "merchant": "Offshore Remittance Gateway"}),
                "Review Recommended - Verify transfer legitimacy with customer", "OPEN"
            ),
            (
                "ALERT5002", "TXN4018", "CUST1003", 82, "HIGH",
                json.dumps(["Velocity spike: 4 successive transactions within 8 minutes"]),
                0.22, 1,
                json.dumps({"velocity_window_mins": 8, "transaction_count": 4, "total_value": 74000.0}),
                "Review Recommended - Step-up customer authentication", "OPEN"
            ),
            (
                "ALERT5003", "TXN4023", "CUST1005", 74, "MEDIUM",
                json.dumps(["Duplicate charge: identical amount within 45 seconds"]),
                0.15, 0,
                json.dumps({"amount": 12999.0, "merchant": "Croma Electronics", "delta_seconds": 45}),
                "Review Recommended - Verify possible POS double charge", "UNDER_REVIEW"
            ),
            (
                "ALERT5004", "TXN4032", "CUST1007", 92, "HIGH",
                json.dumps(["Repeated failed debit payments: 3 failures in 10 minutes"]),
                0.35, 1,
                json.dumps({"failed_count": 3, "requested_amount": 50000.0, "available_balance": 15400.0}),
                "Block & Escalate - Temporary account freeze recommended", "OPEN"
            ),
        ]

        for aid, tid, cid, r_score, r_lvl, rules, a_score, is_ml, evid, rec, stat in alerts_seed:
            fa = FraudAlert(
                id=aid, transaction_id=tid, customer_id=cid,
                risk_score=r_score, risk_level=r_lvl, triggered_rules=rules,
                anomaly_score=a_score, is_ml_anomaly=is_ml, evidence=evid,
                recommended_action=rec, status=stat, created_at=now - timedelta(hours=6)
            )
            db.merge(fa)

        # 6. Seed 8 Loan Applications
        loans_seed = [
            ("LOAN3001", "CUST1001", 500000.0, 36, "Home Improvement", 10.5, 16254.0, 25.0, "ELIGIBLE", "PENDING_REVIEW", "Strong debt service capacity. Clean repayment profile."),
            ("LOAN3002", "CUST1002", 300000.0, 24, "Personal", 11.0, 13985.0, 23.1, "ELIGIBLE", "APPROVED", "Approved under Retail Auto-Decisioning tier."),
            ("LOAN3003", "CUST1003", 800000.0, 48, "Business Expansion", 12.5, 21278.0, 76.1, "HIGH_RISK_DTI", "REJECTED", "Projected DTI exceeds policy threshold of 50%."),
            ("LOAN3004", "CUST1004", 400000.0, 36, "Education", 10.5, 13003.0, 30.0, "REQUIRES_MANUAL_REVIEW", "PENDING_REVIEW", "Pending KYC completion verification."),
            ("LOAN3005", "CUST1005", 250000.0, 18, "Vehicle Purchase", 10.0, 15007.0, 39.1, "ELIGIBLE", "PENDING_REVIEW", "DTI within acceptable 40% band."),
            ("LOAN3006", "CUST1006", 1200000.0, 60, "Home Purchase", 9.5, 25211.0, 26.6, "ELIGIBLE", "APPROVED", "High income profile; excellent liquidity."),
            ("LOAN3007", "CUST1007", 600000.0, 36, "Debt Consolidation", 13.0, 20218.0, 98.2, "INELIGIBLE", "REJECTED", "Severe credit over-leverage."),
            ("LOAN3008", "CUST1010", 750000.0, 36, "Personal", 10.5, 24381.0, 25.8, "ELIGIBLE", "PENDING_REVIEW", "Eligible prime candidate."),
        ]

        for lid, cid, req_amt, tenure, purp, rate, emi, dti, a_res, app_stat, notes in loans_seed:
            l_obj = LoanApplication(
                id=lid, customer_id=cid, requested_amount=req_amt,
                tenure_months=tenure, purpose=purp, interest_rate=rate,
                estimated_emi=emi, dti_ratio=dti, assessment_result=a_res,
                approval_status=app_stat, assessment_notes=notes,
                created_at=now - timedelta(days=12)
            )
            db.merge(l_obj)

        # 7. Seed 5 Policy Documents from JSON files
        if os.path.exists(POLICIES_DIR):
            for filename in os.listdir(POLICIES_DIR):
                if filename.endswith(".json"):
                    filepath = os.path.join(POLICIES_DIR, filename)
                    with open(filepath, "r", encoding="utf-8") as f:
                        p_data = json.load(f)
                        p_doc = PolicyDocument(
                            id=p_data["id"],
                            title=p_data["title"],
                            category=p_data["category"],
                            version=p_data["version"],
                            effective_date=p_data.get("effective_date", "2026-01-01"),
                            content=p_data["content"],
                            passages=json.dumps(p_data.get("passages", []))
                        )
                        db.merge(p_doc)

        # 8. Seed Initial Approval Requests with SHA256 Payload Hash & Idempotency Key
        appr1_payload = {"account_id": "ACC2009", "customer_id": "CUST1007", "reason": "Repeated unauthorized failed debit burst"}
        appr2_payload = {"account_id": "ACC2001", "amount": 450000.0, "beneficiary": "Offshore Remittance Gateway"}
        appr3_payload = {"loan_id": "LOAN3003", "override_dti": 76.1, "exception_reason": "High business turnover"}

        approvals_seed = [
            (
                "APPR7001", "REQ-APPR-001", "FraudAgent", "FREEZE_ACCOUNT",
                appr1_payload, "IDEM-FREEZE-ACC2009-01", "HIGH",
                "Customer CUST1007 experienced 3 rapid failed debits; risk of brute force account takeover.",
                "PENDING", None, None, None, None
            ),
            (
                "APPR7002", "REQ-APPR-002", "CustomerAgent", "HIGH_VALUE_TRANSFER",
                appr2_payload, "IDEM-XFER-ACC2001-450K", "HIGH",
                "Simulated high value transfer of ₹450,000 exceeds standard single-transaction threshold.",
                "APPROVED", "compliance_manager", "Verified transfer intent with account holder via registered channel.",
                now - timedelta(hours=2), json.dumps({"status": "SIMULATED_SUCCESS", "reference": "SIM-REF-99214"})
            ),
            (
                "APPR7003", "REQ-APPR-003", "CreditAgent", "OVERRIDE_LOAN",
                appr3_payload, "IDEM-LOAN-OVERRIDE-3003", "CRITICAL",
                "Requesting DTI policy exception for business loan expansion.",
                "REJECTED", "risk_committee_lead", "DTI ratio 76.1% severely breaches prudential lending cap.",
                now - timedelta(days=1), json.dumps({"status": "REJECTED_BY_POLICY"})
            )
        ]

        for aid, req_id, ag_name, act_type, payload, idem_key, r_lvl, reason, stat, dec_by, dec_reason, dec_at, exec_res in approvals_seed:
            p_hash = compute_payload_hash(payload)
            appr_obj = ApprovalRequest(
                id=aid, request_id=req_id, agent_name=ag_name, action_type=act_type,
                payload=json.dumps(payload), payload_hash=p_hash, idempotency_key=idem_key,
                risk_level=r_lvl, reason=reason, status=stat, decision_by=dec_by,
                decision_reason=dec_reason, decision_at=dec_at, execution_result=exec_res,
                created_at=now - timedelta(hours=10)
            )
            db.merge(appr_obj)

        # 9. Seed Notifications
        notifs_seed = [
            ("NOTIF8001", "High Severity Fraud Alert", "Unusually large transfer of ₹450,000 detected on ACC2001.", "ALERT", False, "/fraud"),
            ("NOTIF8002", "Pending Approval Required", "Account freeze recommendation submitted for ACC2009.", "WARNING", False, "/approvals"),
            ("NOTIF8003", "Loan Evaluation Completed", "Loan application LOAN3001 evaluated with 25.0% DTI ratio.", "INFO", True, "/loans"),
            ("NOTIF8004", "System Simulation Active", "Synthetic transaction generator running in simulation mode.", "INFO", True, "/dashboard"),
        ]
        for nid, title, msg, ntype, is_read, link in notifs_seed:
            notif = Notification(id=nid, title=title, message=msg, type=ntype, is_read=is_read, link_url=link, created_at=now - timedelta(hours=4))
            db.merge(notif)

        # 10. Seed Initial Audit Events
        audits_seed = [
            ("TRC-INIT-001", "System", "SYSTEM_INITIALIZED", "", json.dumps({"version": "v1.0", "status": "Ready"}), 12.4, "SUCCESS"),
            ("TRC-INIT-002", "FraudAgent", "ANOMALY_MODEL_LOADED", "load_model", json.dumps({"model": "IsolationForest-v1.0", "contamination": 0.05}), 45.2, "SUCCESS"),
            ("TRC-INIT-003", "SupervisorAgent", "POLICY_INDEXED", "index_policies", json.dumps({"total_policies": 5, "passages": 10}), 18.7, "SUCCESS"),
        ]
        for trc, actor, ev_type, tool, details, dur, stat in audits_seed:
            aud = AuditEvent(
                correlation_id=trc, actor=actor, event_type=ev_type,
                tool_name=tool, details=details, duration_ms=dur, status=stat,
                timestamp=now - timedelta(hours=12)
            )
            db.add(aud)

        db.commit()
        print("Database seeded successfully with all synthetic entities and isolation forest model!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database(force_reset=True)
