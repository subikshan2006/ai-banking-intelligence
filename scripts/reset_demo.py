"""
Demo Reset Script
-----------------
Resets the SQLite database, reinstantiates tables, and re-seeds baseline banking data.
"""
import sys
import os

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

# Force UTF-8 encoding on standard output for Windows compatibility
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.database import engine, Base
from app.seed.seed_data import seed_database

def main():
    print("Resetting Banking AI Platform database...")
    
    # Drop all existing tables
    Base.metadata.drop_all(bind=engine)
    print("  └─ Existing tables dropped.")
    
    # Re-create all tables
    Base.metadata.create_all(bind=engine)
    print("  └─ Database schema created.")
    
    # Seed data
    print("Seeding baseline data & training Isolation Forest ML model...")
    seed_database()
    print("SUCCESS: Demo reset completed! Database is fully seeded.")

if __name__ == "__main__":
    main()
