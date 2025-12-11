
from migrations import init_db
import sys

print("Starting checks and migrations...")
try:
    init_db()
    print("Migrations completed successfully.")
except Exception as e:
    print(f"Migration FAILED: {e}")
    sys.exit(1)
