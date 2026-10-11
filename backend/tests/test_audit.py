from app.services.audit_service import audit_service
from app.database import get_task_session

def test_audit_event_logging():
    db = get_task_session()
    try:
        corr_id = "CORR-TEST-AUDIT-99"
        event = audit_service.log_event(
            correlation_id=corr_id,
            actor="TestAgent",
            event_type="TEST_ACTION",
            tool_name="test_tool",
            details={"account_number": "SB-1001-9821", "amount": 5000.0},
            duration_ms=14.5,
            status="SUCCESS",
            db=db
        )
        assert event.id is not None
        assert event.correlation_id == corr_id
        # Verify PII masking on details
        assert "****" in event.details

        # Retrieve through get_events
        logs = audit_service.get_events(db=db, correlation_id=corr_id)
        assert len(logs) >= 1
        assert logs[0].actor == "TestAgent"
    finally:
        db.close()
