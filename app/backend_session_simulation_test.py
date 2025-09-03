#!/usr/bin/env python3
"""
Simulate authenticated user testing by directly creating session in database
This allows us to test authenticated features without real OAuth
"""

import requests
import json
import uuid
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv('/app/backend/.env')

# Get backend URL from frontend env
load_dotenv('/app/frontend/.env')
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://qr-maker-2.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# MongoDB connection
MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.getenv('DB_NAME', 'qr_generator')

class SessionSimulationTester:
    def __init__(self):
        self.session = requests.Session()
        self.mongo_client = MongoClient(MONGO_URL)
        self.db = self.mongo_client[DB_NAME]
        self.test_user_id = str(uuid.uuid4())
        self.session_token = str(uuid.uuid4())
        self.results = []
        
    def log_result(self, test_name, success, message="", details=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def setup_test_user(self):
        """Create a test user and session in the database"""
        try:
            # Create test user
            user_doc = {
                "_id": self.test_user_id,
                "email": "testuser@example.com",
                "name": "Test User",
                "picture": "https://example.com/avatar.jpg",
                "isPremium": False,
                "qrCodeCount": 0,
                "subscriptionExpiresAt": None,
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            }
            
            # Insert or update user
            self.db.users.replace_one(
                {"_id": self.test_user_id},
                user_doc,
                upsert=True
            )
            
            # Create session
            session_doc = {
                "session_token": self.session_token,
                "user_id": self.test_user_id,
                "expires_at": datetime.utcnow() + timedelta(days=7),
                "created_at": datetime.utcnow()
            }
            
            self.db.sessions.replace_one(
                {"user_id": self.test_user_id},
                session_doc,
                upsert=True
            )
            
            self.log_result("Setup Test User", True, "Created test user and session in database")
            return True
            
        except Exception as e:
            self.log_result("Setup Test User", False, f"Failed to setup test user: {str(e)}")
            return False
    
    def test_auth_me_with_session(self):
        """Test /auth/me with valid session token"""
        try:
            headers = {"Authorization": f"Bearer {self.session_token}"}
            response = self.session.get(f"{API_BASE}/auth/me", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "user" in data and "limits" in data:
                    user = data["user"]
                    limits = data["limits"]
                    
                    if (user["email"] == "testuser@example.com" and 
                        user["name"] == "Test User" and
                        user["isPremium"] == False and
                        limits["max"] == 5 and
                        limits["isPremium"] == False):
                        self.log_result("Auth Me (With Session)", True, "Successfully retrieved user info with session token")
                        return True
                    else:
                        self.log_result("Auth Me (With Session)", False, "Invalid user or limits data", {"user": user, "limits": limits})
                        return False
                else:
                    self.log_result("Auth Me (With Session)", False, "Missing required fields", data)
                    return False
            else:
                self.log_result("Auth Me (With Session)", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Auth Me (With Session)", False, f"Exception: {str(e)}")
            return False
    
    def test_qr_generation_authenticated(self):
        """Test QR code generation for authenticated user"""
        try:
            headers = {"Authorization": f"Bearer {self.session_token}"}
            qr_data = {
                "url": "https://www.authenticated-test.com",
                "size": "200x200"
            }
            
            response = self.session.post(f"{API_BASE}/qr/generate", json=qr_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "qrCode" in data and "limits" in data:
                    qr_code = data["qrCode"]
                    limits = data["limits"]
                    
                    # Validate QR code data
                    if (qr_code["url"] == qr_data["url"] and 
                        qr_code["size"] == qr_data["size"] and
                        "qrCodeUrl" in qr_code and
                        "id" in qr_code):
                        
                        # Validate limits updated
                        if limits["used"] == 1 and limits["max"] == 5:
                            self.log_result("QR Generation (Authenticated)", True, "QR code generated successfully for authenticated user")
                            return True
                        else:
                            self.log_result("QR Generation (Authenticated)", False, "Limits not updated correctly", limits)
                            return False
                    else:
                        self.log_result("QR Generation (Authenticated)", False, "Invalid QR code data", qr_code)
                        return False
                else:
                    self.log_result("QR Generation (Authenticated)", False, "Missing required fields", data)
                    return False
            else:
                self.log_result("QR Generation (Authenticated)", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("QR Generation (Authenticated)", False, f"Exception: {str(e)}")
            return False
    
    def test_authenticated_user_limits(self):
        """Test generation limits for authenticated users (max 5)"""
        try:
            headers = {"Authorization": f"Bearer {self.session_token}"}
            
            # Generate QR codes up to the limit (we already have 1, so generate 4 more)
            for i in range(4):
                qr_data = {
                    "url": f"https://www.auth-test{i+2}.com",
                    "size": "150x150"
                }
                
                response = self.session.post(f"{API_BASE}/qr/generate", json=qr_data, headers=headers)
                
                if response.status_code != 200:
                    self.log_result("Authenticated User Limits", False, f"Failed to generate QR {i+2}: HTTP {response.status_code}", response.text)
                    return False
            
            # Try to generate one more (should fail)
            qr_data = {
                "url": "https://www.auth-test6.com",
                "size": "150x150"
            }
            
            response = self.session.post(f"{API_BASE}/qr/generate", json=qr_data, headers=headers)
            
            if response.status_code == 403:
                data = response.json()
                if "Generation limit reached" in data.get("detail", ""):
                    self.log_result("Authenticated User Limits", True, "Correctly enforced 5 QR code limit for authenticated users")
                    return True
                else:
                    self.log_result("Authenticated User Limits", False, "Wrong error message", data)
                    return False
            else:
                self.log_result("Authenticated User Limits", False, f"Expected 403, got {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Authenticated User Limits", False, f"Exception: {str(e)}")
            return False
    
    def test_qr_history_authenticated(self):
        """Test QR code history retrieval for authenticated user"""
        try:
            headers = {"Authorization": f"Bearer {self.session_token}"}
            response = self.session.get(f"{API_BASE}/qr/history", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "qrCodes" in data and "limits" in data:
                    qr_codes = data["qrCodes"]
                    limits = data["limits"]
                    
                    # Should have 5 QR codes (the limit we reached)
                    if len(qr_codes) == 5:
                        # Validate limits
                        if limits["used"] == 5 and limits["max"] == 5:
                            self.log_result("QR History (Authenticated)", True, f"Retrieved {len(qr_codes)} QR codes for authenticated user")
                            return True
                        else:
                            self.log_result("QR History (Authenticated)", False, "Invalid limits in history", limits)
                            return False
                    else:
                        self.log_result("QR History (Authenticated)", False, f"Expected 5 QR codes, got {len(qr_codes)}")
                        return False
                else:
                    self.log_result("QR History (Authenticated)", False, "Missing required fields", data)
                    return False
            else:
                self.log_result("QR History (Authenticated)", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("QR History (Authenticated)", False, f"Exception: {str(e)}")
            return False
    
    def test_qr_deletion(self):
        """Test QR code deletion for authenticated users"""
        try:
            headers = {"Authorization": f"Bearer {self.session_token}"}
            
            # First get the history to find a QR code to delete
            response = self.session.get(f"{API_BASE}/qr/history", headers=headers)
            
            if response.status_code != 200:
                self.log_result("QR Deletion", False, "Failed to get QR history for deletion test")
                return False
            
            data = response.json()
            qr_codes = data["qrCodes"]
            
            if not qr_codes:
                self.log_result("QR Deletion", False, "No QR codes found to delete")
                return False
            
            # Delete the first QR code
            qr_id = qr_codes[0]["id"]
            response = self.session.delete(f"{API_BASE}/qr/{qr_id}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") == True:
                    self.log_result("QR Deletion", True, "Successfully deleted QR code")
                    return True
                else:
                    self.log_result("QR Deletion", False, "Invalid deletion response", data)
                    return False
            else:
                self.log_result("QR Deletion", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("QR Deletion", False, f"Exception: {str(e)}")
            return False
    
    def test_subscription_upgrade(self):
        """Test premium subscription upgrade"""
        try:
            headers = {"Authorization": f"Bearer {self.session_token}"}
            sub_data = {"planType": "monthly"}
            
            response = self.session.post(f"{API_BASE}/subscription/upgrade", json=sub_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "subscription" in data and "limits" in data:
                    subscription = data["subscription"]
                    limits = data["limits"]
                    
                    # Validate subscription
                    if (subscription["planType"] == "monthly" and 
                        subscription["status"] == "active"):
                        
                        # Validate unlimited limits
                        if limits["max"] == "unlimited" and limits["isPremium"] == True:
                            self.log_result("Subscription Upgrade", True, "Successfully upgraded to premium subscription")
                            return True
                        else:
                            self.log_result("Subscription Upgrade", False, "Invalid premium limits", limits)
                            return False
                    else:
                        self.log_result("Subscription Upgrade", False, "Invalid subscription data", subscription)
                        return False
                else:
                    self.log_result("Subscription Upgrade", False, "Missing required fields", data)
                    return False
            else:
                self.log_result("Subscription Upgrade", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Subscription Upgrade", False, f"Exception: {str(e)}")
            return False
    
    def test_subscription_status(self):
        """Test subscription status retrieval"""
        try:
            headers = {"Authorization": f"Bearer {self.session_token}"}
            response = self.session.get(f"{API_BASE}/subscription/status", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "subscription" in data and "limits" in data:
                    subscription = data["subscription"]
                    limits = data["limits"]
                    
                    # Should have active subscription
                    if subscription and subscription["status"] == "active":
                        # Should have unlimited limits
                        if limits["max"] == "unlimited" and limits["isPremium"] == True:
                            self.log_result("Subscription Status", True, "Retrieved active subscription status")
                            return True
                        else:
                            self.log_result("Subscription Status", False, "Invalid premium limits", limits)
                            return False
                    else:
                        self.log_result("Subscription Status", False, "No active subscription found", subscription)
                        return False
                else:
                    self.log_result("Subscription Status", False, "Missing required fields", data)
                    return False
            else:
                self.log_result("Subscription Status", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Subscription Status", False, f"Exception: {str(e)}")
            return False
    
    def test_premium_unlimited_generation(self):
        """Test unlimited QR generation for premium users"""
        try:
            headers = {"Authorization": f"Bearer {self.session_token}"}
            
            # Generate a few more QR codes (should work with premium)
            for i in range(3):
                qr_data = {
                    "url": f"https://www.premium{i+1}.com",
                    "size": "150x150"
                }
                
                response = self.session.post(f"{API_BASE}/qr/generate", json=qr_data, headers=headers)
                
                if response.status_code != 200:
                    self.log_result("Premium Unlimited Generation", False, f"Failed to generate premium QR {i+1}: HTTP {response.status_code}", response.text)
                    return False
                
                # Check that limits show unlimited
                data = response.json()
                if data["limits"]["max"] != "unlimited":
                    self.log_result("Premium Unlimited Generation", False, f"Expected unlimited, got {data['limits']['max']}")
                    return False
            
            self.log_result("Premium Unlimited Generation", True, "Successfully generated QR codes with unlimited premium plan")
            return True
                
        except Exception as e:
            self.log_result("Premium Unlimited Generation", False, f"Exception: {str(e)}")
            return False
    
    def test_logout_with_session(self):
        """Test logout with valid session"""
        try:
            headers = {"Authorization": f"Bearer {self.session_token}"}
            response = self.session.post(f"{API_BASE}/auth/logout", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") == True:
                    # Verify session is deleted from database
                    session_count = self.db.sessions.count_documents({"user_id": self.test_user_id})
                    if session_count == 0:
                        self.log_result("Logout (With Session)", True, "Successfully logged out and cleared session from database")
                        return True
                    else:
                        self.log_result("Logout (With Session)", False, f"Session not cleared from database, count: {session_count}")
                        return False
                else:
                    self.log_result("Logout (With Session)", False, "Invalid logout response", data)
                    return False
            else:
                self.log_result("Logout (With Session)", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Logout (With Session)", False, f"Exception: {str(e)}")
            return False
    
    def cleanup_test_data(self):
        """Clean up test data from database"""
        try:
            # Delete test user and related data
            self.db.users.delete_many({"_id": self.test_user_id})
            self.db.sessions.delete_many({"user_id": self.test_user_id})
            self.db.qr_codes.delete_many({"userId": self.test_user_id})
            self.db.subscriptions.delete_many({"userId": self.test_user_id})
            
            self.log_result("Cleanup Test Data", True, "Cleaned up test data from database")
            return True
            
        except Exception as e:
            self.log_result("Cleanup Test Data", False, f"Failed to cleanup: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all authenticated user tests"""
        print(f"\n🚀 Starting Authenticated User Session Tests")
        print(f"Backend URL: {API_BASE}")
        print("Testing with simulated authenticated session")
        print("=" * 70)
        
        # Setup
        if not self.setup_test_user():
            print("❌ Failed to setup test user, aborting tests")
            return 0, 1
        
        # Test sequence
        tests = [
            self.test_auth_me_with_session,
            self.test_qr_generation_authenticated,
            self.test_authenticated_user_limits,
            self.test_qr_history_authenticated,
            self.test_qr_deletion,
            self.test_subscription_upgrade,
            self.test_subscription_status,
            self.test_premium_unlimited_generation,
            self.test_logout_with_session
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ FAIL: {test.__name__} - Exception: {str(e)}")
                failed += 1
        
        # Cleanup
        self.cleanup_test_data()
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"📊 AUTHENTICATED USER TEST SUMMARY")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
        
        if failed > 0:
            print(f"\n🔍 FAILED TESTS:")
            for result in self.results:
                if "❌ FAIL" in result["status"]:
                    print(f"   • {result['test']}: {result['message']}")
        
        return passed, failed

if __name__ == "__main__":
    tester = SessionSimulationTester()
    passed, failed = tester.run_all_tests()
    
    # Exit with error code if any tests failed
    exit(0 if failed == 0 else 1)