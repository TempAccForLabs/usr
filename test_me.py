import json
import urllib.request
import urllib.parse

def test_auth_me():
    # First login to get token
    login_data = {
        "email": "test@example.com",
        "password": "test123"
    }
    
    # Convert data to JSON bytes
    login_json = json.dumps(login_data).encode('utf-8')
    
    # Login request
    login_req = urllib.request.Request(
        "http://localhost:8000/auth/login",
        data=login_json,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(login_req) as response:
            login_result = json.loads(response.read().decode())
            access_token = login_result["access_token"]
            print("✅ Login successful")
            print(f"Access token: {access_token[:50]}...")
            
            # Now test /auth/me
            me_req = urllib.request.Request(
                "http://localhost:8000/auth/me",
                headers={'Authorization': f'Bearer {access_token}'},
                method='GET'
            )
            
            with urllib.request.urlopen(me_req) as me_response:
                me_result = json.loads(me_response.read().decode())
                print(f"🔍 /auth/me status: {me_response.status}")
                print(f"📦 /auth/me response: {json.dumps(me_result, indent=2)}")
                
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error: {e.code} - {e.reason}")
        error_body = e.read().decode()
        print(f"Error details: {error_body}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_auth_me()