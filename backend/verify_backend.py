import httpx
import json
import sys
import os

# Use localhost directly
BASE_URL = "http://localhost:8000"
EMAIL = "catalinohara@gmail.com"
PASSWORD = "Password123!"

def log(msg):
    print(f"[TEST] {msg}")

def fail(msg):
    print(f"[FAIL] {msg}")
    sys.exit(1)

def run_verification():
    # Use a client (sync) for simplicity in this script, or we can use async.
    # httpx.Client is synchronous.
    try:
        with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
            # 1. Login
            log(f"Logging in as {EMAIL}...")
            resp = client.post("/auth/login", json={"email": EMAIL, "password": PASSWORD})
            if resp.status_code != 200:
                fail(f"Login failed: {resp.status_code} {resp.text}")
            
            data = resp.json()
            token = data["access_token"]
            user_id = data["user"]["id"]
            log(f"Login successful. User ID: {user_id}")

            headers = {"Authorization": f"Bearer {token}"}

            # 2. Get Profile
            log("Fetching profile...")
            resp = client.get("/auth/me", headers=headers)
            if resp.status_code != 200:
                fail(f"Profile fetch failed: {resp.status_code} {resp.text}")
            user = resp.json()
            log(f"Profile validated for: {user['full_name']}")

            # 3. List Patients (Verifying Seeding)
            log("Fetching patients...")
            resp = client.get("/companion/patients", headers=headers)
            if resp.status_code != 200:
                fail(f"Patients fetch failed: {resp.status_code} {resp.text}")
            patients = resp.json()
            log(f"Found {len(patients)} patients.")
            if len(patients) == 0:
                fail("No patients found. Database might not be seeded.")
            
            for p in patients:
                log(f" - Found Patient: {p['alias']} (Load: {p['emotional_load']})")

            # 4. Chat Interaction (Verifying LLM)
            log("Testing Chat Interaction...")
            chat_payload = {"message": "Hello, I have a patient check-in update."}
            resp = client.post("/companion/chat", json=chat_payload, headers=headers)
            if resp.status_code != 200:
                fail(f"Chat failed: {resp.status_code} {resp.text}")
            chat_resp = resp.json()
            content = chat_resp.get('content', '')
            log(f"Chat Response: {content[:150]}...")

            if not content:
                fail("Chat response was empty.")

            log("VERIFICATION SUCCESSFUL: Backend, Database, Auth, and LLM are operational.")
            
    except Exception as e:
        fail(f"Exception during verification: {e}")

if __name__ == "__main__":
    run_verification()
