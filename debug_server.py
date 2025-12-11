import sys
import traceback

print("PYTHONPATH:", sys.path)

try:
    print("Attempting to import offer_letter_generator...")
    import offer_letter_generator
    print("Successfully imported offer_letter_generator.")
except Exception:
    print("Failed to import offer_letter_generator:")
    traceback.print_exc()

try:
    print("Attempting to import hr_decision_emails...")
    import hr_decision_emails
    print("Successfully imported hr_decision_emails.")
except Exception:
    print("Failed to import hr_decision_emails:")
    traceback.print_exc()

try:
    print("Attempting to import email_sender...")
    import email_sender
    print("Successfully imported email_sender.")
except Exception:
    print("Failed to import email_sender:")
    traceback.print_exc()

try:
    print("Attempting to import main...")
    # Prevent main from running if it doesn't have if __name__ == "__main__": (it does, but safe to be sure)
    import main
    print("Successfully imported main.")
except Exception:
    print("Failed to import main:")
    traceback.print_exc()

print("Debug check complete.")
