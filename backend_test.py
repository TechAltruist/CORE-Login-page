#!/usr/bin/env python3
"""
Backend API Testing Suite for CORE VR Therapeutic Platform
Tests JWT authentication, user profiles, protected routes, and VR sessions
"""

import requests
import json
import jwt
import time
from datetime import datetime, timedelta
import uuid

# Configuration
BACKEND_URL = "https://5854bdae-9629-434c-a2e5-c4169ed30201.preview.emergentagent.com/api"
SUPABASE_JWT_SECRET = "2W+Gtk9hfwgQvLF6s67tvJOvgC8xABm68gL367Y5DBKKOz4v3XfPf9c9mLuLfcKrXL4nUEDK4yOOAG+PbbhGNg=="

class COREBackendTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.jwt_secret = SUPABASE_JWT_SECRET
        self.test_results = []
        
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   Details: {details}")
    
    def generate_valid_jwt(self, user_id=None, email=None):
        """Generate a valid JWT token for testing"""
        if not user_id:
            user_id = str(uuid.uuid4())
        if not email:
            email = "test.user@coreplatform.com"
            
        payload = {
            "sub": user_id,
            "email": email,
            "role": "authenticated",
            "aud": "authenticated",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600  # 1 hour expiry
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        return token, user_id, email
    
    def generate_invalid_jwt(self):
        """Generate an invalid JWT token for testing"""
        payload = {
            "sub": str(uuid.uuid4()),
            "email": "invalid@test.com",
            "role": "authenticated",
            "aud": "authenticated",
            "iat": int(time.time()),
            "exp": int(time.time()) - 3600  # Expired token
        }
        
        # Use wrong secret to make it invalid
        token = jwt.encode(payload, "wrong_secret", algorithm="HS256")
        return token
    
    def test_jwt_authentication_middleware(self):
        """Test JWT Authentication Middleware"""
        print("\n=== Testing JWT Authentication Middleware ===")
        
        # Test 1: Valid JWT token
        try:
            valid_token, user_id, email = self.generate_valid_jwt()
            headers = {"Authorization": f"Bearer {valid_token}"}
            
            response = requests.get(f"{self.backend_url}/auth/me", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("user_id") == user_id and data.get("email") == email:
                    self.log_test("JWT Valid Token", True, "Valid JWT token accepted and decoded correctly")
                else:
                    self.log_test("JWT Valid Token", False, "Valid JWT token accepted but user data mismatch", data)
            else:
                self.log_test("JWT Valid Token", False, f"Valid JWT token rejected with status {response.status_code}", response.text)
        except Exception as e:
            self.log_test("JWT Valid Token", False, f"Exception during valid JWT test: {str(e)}")
        
        # Test 2: Invalid JWT token
        try:
            invalid_token = self.generate_invalid_jwt()
            headers = {"Authorization": f"Bearer {invalid_token}"}
            
            response = requests.get(f"{self.backend_url}/auth/me", headers=headers)
            
            if response.status_code == 401:
                self.log_test("JWT Invalid Token", True, "Invalid JWT token correctly rejected with 401")
            else:
                self.log_test("JWT Invalid Token", False, f"Invalid JWT token not rejected properly, got status {response.status_code}")
        except Exception as e:
            self.log_test("JWT Invalid Token", False, f"Exception during invalid JWT test: {str(e)}")
        
        # Test 3: Missing JWT token
        try:
            response = requests.get(f"{self.backend_url}/auth/me")
            
            if response.status_code == 401:
                self.log_test("JWT Missing Token", True, "Missing JWT token correctly rejected with 401")
            else:
                self.log_test("JWT Missing Token", False, f"Missing JWT token not rejected properly, got status {response.status_code}")
        except Exception as e:
            self.log_test("JWT Missing Token", False, f"Exception during missing JWT test: {str(e)}")
    
    def test_protected_routes(self):
        """Test Protected Routes Implementation"""
        print("\n=== Testing Protected Routes Implementation ===")
        
        valid_token, user_id, email = self.generate_valid_jwt()
        headers = {"Authorization": f"Bearer {valid_token}"}
        
        # Test /api/auth/me endpoint
        try:
            response = requests.get(f"{self.backend_url}/auth/me", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ["user_id", "email", "role"]
                if all(field in data for field in expected_fields):
                    self.log_test("Protected Route /auth/me", True, "Auth me endpoint working correctly", data)
                else:
                    self.log_test("Protected Route /auth/me", False, "Auth me endpoint missing required fields", data)
            else:
                self.log_test("Protected Route /auth/me", False, f"Auth me endpoint failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Protected Route /auth/me", False, f"Exception testing /auth/me: {str(e)}")
        
        # Test /api/auth/protected endpoint
        try:
            response = requests.get(f"{self.backend_url}/auth/protected", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "user_email" in data:
                    self.log_test("Protected Route /auth/protected", True, "Protected route working correctly", data)
                else:
                    self.log_test("Protected Route /auth/protected", False, "Protected route missing expected fields", data)
            else:
                self.log_test("Protected Route /auth/protected", False, f"Protected route failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Protected Route /auth/protected", False, f"Exception testing /auth/protected: {str(e)}")
        
        # Test protected routes without authentication
        try:
            response = requests.get(f"{self.backend_url}/auth/protected")
            
            if response.status_code == 401:
                self.log_test("Protected Route Unauthorized", True, "Protected route correctly rejects unauthenticated requests")
            else:
                self.log_test("Protected Route Unauthorized", False, f"Protected route should reject unauthenticated requests, got status {response.status_code}")
        except Exception as e:
            self.log_test("Protected Route Unauthorized", False, f"Exception testing unauthorized access: {str(e)}")
    
    def test_user_profile_management(self):
        """Test User Profile Management API"""
        print("\n=== Testing User Profile Management API ===")
        
        valid_token, user_id, email = self.generate_valid_jwt()
        headers = {"Authorization": f"Bearer {valid_token}"}
        
        # Test GET profile (should create basic profile if doesn't exist)
        try:
            response = requests.get(f"{self.backend_url}/profile", headers=headers)
            
            if response.status_code == 200:
                profile_data = response.json()
                required_fields = ["id", "supabase_uid", "email", "created_at"]
                if all(field in profile_data for field in required_fields):
                    self.log_test("Profile GET", True, "Profile retrieval working correctly", profile_data)
                else:
                    self.log_test("Profile GET", False, "Profile missing required fields", profile_data)
            else:
                self.log_test("Profile GET", False, f"Profile GET failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Profile GET", False, f"Exception testing profile GET: {str(e)}")
        
        # Test POST profile (create/update)
        try:
            profile_data = {
                "full_name": "Dr. Sarah Chen",
                "therapy_preferences": ["memory_reconstruction", "anxiety_therapy"],
                "vr_settings": {"comfort_level": "intermediate", "session_duration": 30}
            }
            
            response = requests.post(f"{self.backend_url}/profile", 
                                   headers=headers, 
                                   json=profile_data)
            
            if response.status_code == 200:
                created_profile = response.json()
                if (created_profile.get("full_name") == profile_data["full_name"] and 
                    created_profile.get("therapy_preferences") == profile_data["therapy_preferences"]):
                    self.log_test("Profile POST", True, "Profile creation/update working correctly", created_profile)
                else:
                    self.log_test("Profile POST", False, "Profile data not saved correctly", created_profile)
            else:
                self.log_test("Profile POST", False, f"Profile POST failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Profile POST", False, f"Exception testing profile POST: {str(e)}")
        
        # Test PUT profile (update)
        try:
            update_data = {
                "full_name": "Dr. Sarah Chen-Williams",
                "therapy_preferences": ["memory_reconstruction", "anxiety_therapy", "ptsd_treatment"]
            }
            
            response = requests.put(f"{self.backend_url}/profile", 
                                  headers=headers, 
                                  json=update_data)
            
            if response.status_code == 200:
                updated_profile = response.json()
                if (updated_profile.get("full_name") == update_data["full_name"] and 
                    len(updated_profile.get("therapy_preferences", [])) == 3):
                    self.log_test("Profile PUT", True, "Profile update working correctly", updated_profile)
                else:
                    self.log_test("Profile PUT", False, "Profile update data not saved correctly", updated_profile)
            else:
                self.log_test("Profile PUT", False, f"Profile PUT failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Profile PUT", False, f"Exception testing profile PUT: {str(e)}")
        
        # Test profile endpoints without authentication
        try:
            response = requests.get(f"{self.backend_url}/profile")
            
            if response.status_code == 401:
                self.log_test("Profile Unauthorized", True, "Profile endpoints correctly reject unauthenticated requests")
            else:
                self.log_test("Profile Unauthorized", False, f"Profile endpoints should reject unauthenticated requests, got status {response.status_code}")
        except Exception as e:
            self.log_test("Profile Unauthorized", False, f"Exception testing profile unauthorized access: {str(e)}")
    
    def test_vr_sessions_api(self):
        """Test VR Sessions API"""
        print("\n=== Testing VR Sessions API ===")
        
        valid_token, user_id, email = self.generate_valid_jwt()
        headers = {"Authorization": f"Bearer {valid_token}"}
        
        # Test GET VR sessions
        try:
            response = requests.get(f"{self.backend_url}/vr/sessions", headers=headers)
            
            if response.status_code == 200:
                sessions_data = response.json()
                if ("user_id" in sessions_data and 
                    "sessions" in sessions_data and 
                    isinstance(sessions_data["sessions"], list)):
                    
                    # Check if sessions have required fields
                    if sessions_data["sessions"]:
                        session = sessions_data["sessions"][0]
                        required_fields = ["id", "title", "date", "duration", "type"]
                        if all(field in session for field in required_fields):
                            self.log_test("VR Sessions GET", True, "VR sessions endpoint working correctly", sessions_data)
                        else:
                            self.log_test("VR Sessions GET", False, "VR sessions missing required fields", sessions_data)
                    else:
                        self.log_test("VR Sessions GET", True, "VR sessions endpoint working (empty sessions list)", sessions_data)
                else:
                    self.log_test("VR Sessions GET", False, "VR sessions response format incorrect", sessions_data)
            else:
                self.log_test("VR Sessions GET", False, f"VR sessions GET failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_test("VR Sessions GET", False, f"Exception testing VR sessions GET: {str(e)}")
        
        # Test VR sessions without authentication
        try:
            response = requests.get(f"{self.backend_url}/vr/sessions")
            
            if response.status_code == 401:
                self.log_test("VR Sessions Unauthorized", True, "VR sessions endpoint correctly rejects unauthenticated requests")
            else:
                self.log_test("VR Sessions Unauthorized", False, f"VR sessions should reject unauthenticated requests, got status {response.status_code}")
        except Exception as e:
            self.log_test("VR Sessions Unauthorized", False, f"Exception testing VR sessions unauthorized access: {str(e)}")
    
    def test_basic_connectivity(self):
        """Test basic API connectivity"""
        print("\n=== Testing Basic API Connectivity ===")
        
        try:
            response = requests.get(f"{self.backend_url}/")
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_test("API Connectivity", True, "Backend API is accessible and responding", data)
                else:
                    self.log_test("API Connectivity", False, "Backend API responding but unexpected format", data)
            else:
                self.log_test("API Connectivity", False, f"Backend API not accessible, status {response.status_code}", response.text)
        except Exception as e:
            self.log_test("API Connectivity", False, f"Cannot connect to backend API: {str(e)}")
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting CORE VR Therapeutic Platform Backend Tests")
        print(f"Backend URL: {self.backend_url}")
        print("=" * 60)
        
        # Run tests in order
        self.test_basic_connectivity()
        self.test_jwt_authentication_middleware()
        self.test_protected_routes()
        self.test_user_profile_management()
        self.test_vr_sessions_api()
        
        # Summary
        print("\n" + "=" * 60)
        print("🏁 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        failed = len(self.test_results) - passed
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        return self.test_results

if __name__ == "__main__":
    tester = COREBackendTester()
    results = tester.run_all_tests()