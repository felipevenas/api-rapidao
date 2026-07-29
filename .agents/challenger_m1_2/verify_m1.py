import asyncio
import os
import sys

sys.path.insert(0, r"C:\Codes\api-rapidao\.app")

import httpx
from main import app

async def run_verification():
    results = []
    issues = []
    
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Test 1: Health check success envelope
        res = await client.get("/health")
        data = res.json()
        if res.status_code == 200 and data.get("status") == "success" and "message" in data and "data" in data:
            results.append("✅ Test 1: GET /health success envelope compliant")
        else:
            issues.append(f"❌ Test 1 failed: status_code={res.status_code}, data={data}")

        # Test 2: Validation Error envelope (HTTP 422)
        res = await client.post("/auth/register", json={})
        data = res.json()
        if res.status_code == 422 and data.get("status") == "error" and "message" in data and "details" in data:
            results.append("✅ Test 2: HTTP 422 Validation error envelope compliant")
        else:
            issues.append(f"❌ Test 2 failed: status_code={res.status_code}, data={data}")

        # Test 3: Business Error - Duplicate email (HTTP 400)
        user_data = {
            "email": "test_dup@example.com",
            "password": "password123",
            "full_name": "Test Dup",
            "role": "client"
        }
        res1 = await client.post("/auth/register", json=user_data)
        res2 = await client.post("/auth/register", json=user_data)
        data2 = res2.json()
        if res2.status_code == 400 and data2.get("status") == "error" and "message" in data2:
            results.append("✅ Test 3: HTTP 400 Duplicate email error envelope compliant")
        else:
            issues.append(f"❌ Test 3 failed: status_code={res2.status_code}, data={data2}")

        # Test 4: Business Error - Bad login (HTTP 401)
        res = await client.post("/auth/login", json={"email": "nonexistent@example.com", "password": "wrong"})
        data = res.json()
        if res.status_code == 401 and data.get("status") == "error" and "message" in data:
            results.append("✅ Test 4: HTTP 401 Bad login error envelope compliant")
        else:
            issues.append(f"❌ Test 4 failed: status_code={res.status_code}, data={data}")

        # Test 5: Authorization Error - Role Mismatch (HTTP 403)
        reg_res = await client.post("/auth/register", json={
            "email": "client_only@example.com",
            "password": "password123",
            "full_name": "Client Only",
            "role": "client"
        })
        token = reg_res.json()["data"]["tokens"]["access_token"]
        res = await client.get("/auth/test-role/store", headers={"Authorization": f"Bearer {token}"})
        data = res.json()
        if res.status_code == 403 and data.get("status") == "error" and "message" in data:
            results.append("✅ Test 5: HTTP 403 Role forbidden error envelope compliant")
        else:
            issues.append(f"❌ Test 5 failed: status_code={res.status_code}, data={data}")

        # Test 6: Unmatched route / 404 Not Found
        res = await client.get("/auth/nonexistent-route-12345")
        data = res.json()
        if res.status_code == 404 and data.get("status") == "error" and "message" in data:
            results.append("✅ Test 6: HTTP 404 Not Found error envelope compliant")
        else:
            issues.append(f"❌ Test 6 FAILED (Envelope Non-compliance on 404): status_code={res.status_code}, data={data}")

        # Test 7: Method Not Allowed / 405
        res = await client.put("/auth/register")
        data = res.json()
        if res.status_code == 405 and data.get("status") == "error" and "message" in data:
            results.append("✅ Test 7: HTTP 405 Method Not Allowed error envelope compliant")
        else:
            issues.append(f"❌ Test 7 FAILED (Envelope Non-compliance on 405): status_code={res.status_code}, data={data}")

        # Test 8: Physical structure validation (No redundant app/ folder under .app)
        app_dir = r"C:\Codes\api-rapidao\.app"
        redundant_app = os.path.join(app_dir, "app")
        if not os.path.exists(redundant_app):
            results.append("✅ Test 8: Physical structure verified (No .app/app folder)")
        else:
            issues.append(f"❌ Test 8 failed: Redundant folder {redundant_app} exists!")

        # Test 9: Domain folder allowed files check
        auth_dir = os.path.join(app_dir, "domain", "auth")
        allowed_files = {"models.py", "schemas.py", "repository.py", "service.py", "usecase.py", "routes.py", "__pycache__"}
        actual_files = set(os.listdir(auth_dir))
        forbidden_files = actual_files - allowed_files
        if len(forbidden_files) == 0:
            results.append("✅ Test 9: Allowed files in domain/auth verified")
        else:
            issues.append(f"❌ Test 9 failed: Forbidden files in domain/auth: {forbidden_files}")

    print("--- EMPIRICAL TEST RESULTS ---")
    for r in results:
        print(r)
    if issues:
        print("\n--- ISSUES DISCOVERED ---")
        for i in issues:
            print(i)

if __name__ == "__main__":
    asyncio.run(run_verification())
