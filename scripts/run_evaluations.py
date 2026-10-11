"""
Benchmark Evaluation Runner Script
----------------------------------
Runs automated benchmark suite evaluating agent task completion, latency, and compliance.
"""
import sys
import os
import asyncio

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

# Force UTF-8 encoding on standard output for Windows compatibility
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.database import SessionLocal
from app.services.evaluation_service import evaluation_service

async def main_async():
    print("Starting Banking AI Platform Benchmark Evaluation Suite...")
    db = SessionLocal()
    try:
        res = await evaluation_service.run_suite(db)
        
        print("\n" + "="*60)
        print("EVALUATION RESULTS SUMMARY")
        print("="*60)
        print(f"Run ID                 : {res.evaluation_id}")
        print(f"Total Test Scenarios   : {res.total_cases}")
        print(f"Passed Scenarios       : {res.passed_cases}")
        print(f"Accuracy Rate          : {res.accuracy_rate:.1f}%")
        print(f"Execution Mode         : {res.mode}")
        print("="*60)
        
        print("\nSCENARIO BREAKDOWN:")
        for case in res.results:
            status = case.status
            print(f" [{status:<6}] {case.case_id} | Scenario: {case.prompt[:45]}... ({case.execution_time_ms} ms)")
            print(f"           Details: {case.details}")
        
        print("\nSUCCESS: Benchmark evaluation completed cleanly!")
    finally:
        db.close()

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
