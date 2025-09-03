#!/usr/bin/env python3
"""
Comprehensive Backend API Tests for QR Code Generator
Tests authentication, QR generation, limits, and subscription systems
"""

import requests
import json
import time
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://qr-maker-2.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class QRCodeAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_user_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
        self.test_user_password = "SecurePass123!"
        self.test_user_name = "Test User"
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
    
    def test_health_check(self):
        """Test API health endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "QR Code Generator API" in data["message"]:
                    self.log_result("Health Check", True, "API is responding correctly")
                    return True
                else:
                    self.log_result("Health Check", False, "Unexpected response format", data)
                    return False
            else:
                self.log_result("Health Check", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Health Check", False, f"Connection error: {str(e)}")
            return False
    
    def test_user_registration(self):
        """Test user registration with valid data"""
        try:
            user_data = {
                "email": self.test_user_email,
                "password": self.test_user_password,
                "name": self.test_user_name
            }
            
            response = self.session.post(f"{API_BASE}/auth/register", json=user_data)
            
            if response.status_code == 200:
                data = response.json()
                if "user" in data and "token" in data and "limits" in data:
                    self.auth_token = data["token"]
                    user = data["user"]
                    limits = data["limits"]
                    
                    # Validate user data
                    if (user["email"] == self.test_user_email and 
                        user["name"] == self.test_user_name and
                        user["isPremium"] == False and
                        user["qrCodeCount"] == 0):
                        
                        # Validate limits
                        if limits["used"] == 0 and limits["max"] == 5 and limits["isPremium"] == False:
                            self.log_result("User Registration", True, "User registered successfully with correct data")
                            return True
                        else:
                            self.log_result("User Registration", False, "Invalid limits data", limits)
                            return False
                    else:
                        self.log_result("User Registration", False, "Invalid user data", user)
                        return False
                else:
                    self.log_result("User Registration", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("User Registration", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("User Registration", False, f"Exception: {str(e)}")
            return False
    
    def test_duplicate_registration(self):
        """Test registration with existing email"""
        try:
            user_data = {
                "email": self.test_user_email,  # Same email as before
                "password": "AnotherPass123!",
                "name": "Another User"
            }
            
            response = self.session.post(f"{API_BASE}/auth/register", json=user_data)
            
            if response.status_code == 400:
                data = response.json()
                if "Email already registered" in data.get("detail", ""):
                    self.log_result("Duplicate Registration", True, "Correctly rejected duplicate email")
                    return True
                else:
                    self.log_result("Duplicate Registration", False, "Wrong error message", data)
                    return False
            else:
                self.log_result("Duplicate Registration", False, f"Expected 400, got {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Duplicate Registration", False, f"Exception: {str(e)}")
            return False
    
    def test_user_login(self):
        """Test user login with correct credentials"""
        try:
            login_data = {
                "email": self.test_user_email,
                "password": self.test_user_password
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if "user" in data and "token" in data and "limits" in data:
                    self.auth_token = data["token"]  # Update token
                    user = data["user"]
                    
                    if (user["email"] == self.test_user_email and 
                        user["name"] == self.test_user_name):
                        self.log_result("User Login", True, "Login successful with correct credentials")
                        return True
                    else:
                        self.log_result("User Login", False, "Invalid user data in response", user)
                        return False
                else:
                    self.log_result("User Login", False, "Missing required fields", data)
                    return False
            else:
                self.log_result("User Login", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("User Login", False, f"Exception: {str(e)}")
            return False
    
    def test_invalid_login(self):
        """Test login with invalid credentials"""
        try:
            login_data = {
                "email": self.test_user_email,
                "password": "WrongPassword123!"
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 401:
                data = response.json()
                if "Invalid email or password" in data.get("detail", ""):
                    self.log_result("Invalid Login", True, "Correctly rejected invalid credentials")
                    return True
                else:
                    self.log_result("Invalid Login", False, "Wrong error message", data)
                    return False
            else:
                self.log_result("Invalid Login", False, f"Expected 401, got {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Invalid Login", False, f"Exception: {str(e)}")
            return False
    
    def test_jwt_validation(self):
        """Test JWT token validation on protected endpoint"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.get(f"{API_BASE}/auth/me", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "user" in data and "limits" in data:
                    user = data["user"]
                    if user["email"] == self.test_user_email:
                        self.log_result("JWT Validation", True, "Token validated successfully")
                        return True
                    else:
                        self.log_result("JWT Validation", False, "Wrong user data", user)
                        return False
                else:
                    self.log_result("JWT Validation", False, "Missing required fields", data)
                    return False
            else:
                self.log_result("JWT Validation", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("JWT Validation", False, f"Exception: {str(e)}")
            return False
    
    def test_invalid_jwt(self):
        """Test with invalid JWT token"""
        try:
            headers = {"Authorization": "Bearer invalid_token_here"}
            response = self.session.get(f"{API_BASE}/auth/me", headers=headers)
            
            if response.status_code == 401:
                self.log_result("Invalid JWT", True, "Correctly rejected invalid token")
                return True
            else:
                self.log_result("Invalid JWT", False, f"Expected 401, got {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Invalid JWT", False, f"Exception: {str(e)}")
            return False
    
    def test_qr_generation_authenticated(self):
        """Test QR code generation for authenticated user"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            qr_data = {
                "url": "https://www.example.com",
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
                            self.log_result("QR Generation (Auth)", True, "QR code generated successfully for authenticated user")
                            return True
                        else:
                            self.log_result("QR Generation (Auth)", False, "Limits not updated correctly", limits)
                            return False
                    else:
                        self.log_result("QR Generation (Auth)", False, "Invalid QR code data", qr_code)
                        return False
                else:
                    self.log_result("QR Generation (Auth)", False, "Missing required fields", data)
                    return False
            else:
                self.log_result("QR Generation (Auth)", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("QR Generation (Auth)", False, f"Exception: {str(e)}")
            return False
    
    def test_qr_generation_guest(self):
        """Test QR code generation for guest user"""
        try:
            # Don't include authorization header
            qr_data = {
                "url": "https://www.google.com",
                "size": "150x150"
            }
            
            response = self.session.post(f"{API_BASE}/qr/generate", json=qr_data)
            
            if response.status_code == 200:
                data = response.json()
                if "qrCode" in data and "limits" in data:
                    qr_code = data["qrCode"]
                    limits = data["limits"]
                    
                    # Validate QR code data
                    if (qr_code["url"] == qr_data["url"] and 
                        qr_code["size"] == qr_data["size"]):
                        
                        # Validate guest limits
                        if limits["max"] == 3 and limits["isPremium"] == False:
                            self.log_result("QR Generation (Guest)", True, "QR code generated successfully for guest user")
                            return True
                        else:
                            self.log_result("QR Generation (Guest)", False, "Invalid guest limits", limits)
                            return False
                    else:
                        self.log_result("QR Generation (Guest)", False, "Invalid QR code data", qr_code)
                        return False
                else:
                    self.log_result("QR Generation (Guest)", False, "Missing required fields", data)
                    return False
            else:
                self.log_result("QR Generation (Guest)", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("QR Generation (Guest)", False, f"Exception: {str(e)}")
            return False
    
    def test_invalid_url_validation(self):
        """Test URL validation with invalid URL"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            qr_data = {
                "url": "not-a-valid-url",
                "size": "150x150"
            }
            
            response = self.session.post(f"{API_BASE}/qr/generate", json=qr_data, headers=headers)
            
            if response.status_code == 422:
                data = response.json()
                if "Invalid URL format" in data.get("detail", ""):
                    self.log_result("Invalid URL Validation", True, "Correctly rejected invalid URL")
                    return True
                else:
                    self.log_result("Invalid URL Validation", False, "Wrong error message", data)
                    return False
            else:
                self.log_result("Invalid URL Validation", False, f"Expected 422, got {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Invalid URL Validation", False, f"Exception: {str(e)}")
            return False
    
    def test_invalid_size_validation(self):
        """Test size validation with invalid size format"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            qr_data = {
                "url": "https://www.example.com",
                "size": "invalid-size"
            }
            
            response = self.session.post(f"{API_BASE}/qr/generate", json=qr_data, headers=headers)
            
            if response.status_code == 422:
                data = response.json()
                if "Invalid size format" in data.get("detail", ""):
                    self.log_result("Invalid Size Validation", True, "Correctly rejected invalid size")
                    return True
                else:
                    self.log_result("Invalid Size Validation", False, "Wrong error message", data)
                    return False
            else:
                self.log_result("Invalid Size Validation", False, f"Expected 422, got {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Invalid Size Validation", False, f"Exception: {str(e)}")
            return False
    
    def test_authenticated_user_limits(self):
        """Test generation limits for authenticated users (max 5)"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Generate QR codes up to the limit (we already have 1, so generate 4 more)
            for i in range(4):
                qr_data = {
                    "url": f"https://www.example{i+2}.com",
                    "size": "150x150"
                }
                
                response = self.session.post(f"{API_BASE}/qr/generate", json=qr_data, headers=headers)
                
                if response.status_code != 200:
                    self.log_result("Auth User Limits", False, f"Failed to generate QR {i+2}: HTTP {response.status_code}", response.text)
                    return False
            
            # Try to generate one more (should fail)
            qr_data = {
                "url": "https://www.example6.com",
                "size": "150x150"
            }
            
            response = self.session.post(f"{API_BASE}/qr/generate", json=qr_data, headers=headers)
            
            if response.status_code == 403:
                data = response.json()
                if "Generation limit reached" in data.get("detail", ""):
                    self.log_result("Auth User Limits", True, "Correctly enforced 5 QR code limit for authenticated users")
                    return True
                else:
                    self.log_result("Auth User Limits", False, "Wrong error message", data)
                    return False
            else:
                self.log_result("Auth User Limits", False, f"Expected 403, got {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Auth User Limits", False, f"Exception: {str(e)}")
            return False
    
    def test_guest_user_limits(self):
        """Test generation limits for guest users (max 3)"""
        try:
            # Generate QR codes up to the limit for guest (we already have 1, so generate 2 more)
            for i in range(2):
                qr_data = {
                    "url": f"https://www.guest{i+2}.com",
                    "size": "150x150"
                }
                
                response = self.session.post(f"{API_BASE}/qr/generate", json=qr_data)
                
                if response.status_code != 200:
                    self.log_result("Guest User Limits", False, f"Failed to generate guest QR {i+2}: HTTP {response.status_code}", response.text)
                    return False
            
            # Try to generate one more (should fail)
            qr_data = {
                "url": "https://www.guest4.com",
                "size": "150x150"
            }
            
            response = self.session.post(f"{API_BASE}/qr/generate", json=qr_data)
            
            if response.status_code == 403:
                data = response.json()
                if "Generation limit reached" in data.get("detail", ""):
                    self.log_result("Guest User Limits", True, "Correctly enforced 3 QR code limit for guest users")
                    return True
                else:
                    self.log_result("Guest User Limits", False, "Wrong error message", data)
                    return False
            else:
                self.log_result("Guest User Limits", False, f"Expected 403, got {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Guest User Limits", False, f"Exception: {str(e)}")
            return False
    
    def test_qr_history_authenticated(self):
        """Test QR code history retrieval for authenticated user"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
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
                            self.log_result("QR History (Auth)", True, f"Retrieved {len(qr_codes)} QR codes for authenticated user")
                            return True
                        else:
                            self.log_result("QR History (Auth)", False, "Invalid limits in history", limits)
                            return False
                    else:
                        self.log_result("QR History (Auth)", False, f"Expected 5 QR codes, got {len(qr_codes)}")
                        return False
                else:
                    self.log_result("QR History (Auth)", False, "Missing required fields", data)
                    return False
            else:
                self.log_result("QR History (Auth)", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("QR History (Auth)", False, f"Exception: {str(e)}")
            return False
    
    def test_qr_history_guest(self):
        """Test QR code history retrieval for guest user"""
        try:
            response = self.session.get(f"{API_BASE}/qr/history")
            
            if response.status_code == 200:
                data = response.json()
                if "qrCodes" in data and "limits" in data:
                    qr_codes = data["qrCodes"]
                    limits = data["limits"]
                    
                    # Should have 3 QR codes (the limit we reached)
                    if len(qr_codes) == 3:
                        # Validate guest limits
                        if limits["used"] == 3 and limits["max"] == 3 and limits["isPremium"] == False:
                            self.log_result("QR History (Guest)", True, f"Retrieved {len(qr_codes)} QR codes for guest user")
                            return True
                        else:
                            self.log_result("QR History (Guest)", False, "Invalid guest limits in history", limits)
                            return False
                    else:
                        self.log_result("QR History (Guest)", False, f"Expected 3 QR codes, got {len(qr_codes)}")
                        return False
                else:
                    self.log_result("QR History (Guest)", False, "Missing required fields", data)
                    return False
            else:
                self.log_result("QR History (Guest)", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("QR History (Guest)", False, f"Exception: {str(e)}")
            return False
    
    def test_subscription_upgrade(self):
        """Test premium subscription upgrade"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
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
            headers = {"Authorization": f"Bearer {self.auth_token}"}
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
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Generate a few more QR codes (should work with premium)
            for i in range(3):
                qr_data = {
                    "url": f"https://www.premium{i+1}.com",
                    "size": "150x150"
                }
                
                response = self.session.post(f"{API_BASE}/qr/generate", json=qr_data, headers=headers)
                
                if response.status_code != 200:
                    self.log_result("Premium Unlimited", False, f"Failed to generate premium QR {i+1}: HTTP {response.status_code}", response.text)
                    return False
                
                # Check that limits show unlimited
                data = response.json()
                if data["limits"]["max"] != "unlimited":
                    self.log_result("Premium Unlimited", False, f"Expected unlimited, got {data['limits']['max']}")
                    return False
            
            self.log_result("Premium Unlimited", True, "Successfully generated QR codes with unlimited premium plan")
            return True
                
        except Exception as e:
            self.log_result("Premium Unlimited", False, f"Exception: {str(e)}")
            return False
    
    def test_qr_deletion(self):
        """Test QR code deletion for authenticated users"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
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
    
    def test_unauthorized_deletion(self):
        """Test QR code deletion without authentication"""
        try:
            # Try to delete without auth token
            fake_qr_id = str(uuid.uuid4())
            response = self.session.delete(f"{API_BASE}/qr/{fake_qr_id}")
            
            if response.status_code == 401:
                data = response.json()
                if "Authentication required" in data.get("detail", ""):
                    self.log_result("Unauthorized Deletion", True, "Correctly rejected deletion without authentication")
                    return True
                else:
                    self.log_result("Unauthorized Deletion", False, "Wrong error message", data)
                    return False
            else:
                self.log_result("Unauthorized Deletion", False, f"Expected 401, got {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Unauthorized Deletion", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print(f"\n🚀 Starting QR Code API Tests")
        print(f"Backend URL: {API_BASE}")
        print(f"Test User: {self.test_user_email}")
        print("=" * 60)
        
        # Test sequence
        tests = [
            self.test_health_check,
            self.test_user_registration,
            self.test_duplicate_registration,
            self.test_user_login,
            self.test_invalid_login,
            self.test_jwt_validation,
            self.test_invalid_jwt,
            self.test_qr_generation_authenticated,
            self.test_qr_generation_guest,
            self.test_invalid_url_validation,
            self.test_invalid_size_validation,
            self.test_authenticated_user_limits,
            self.test_guest_user_limits,
            self.test_qr_history_authenticated,
            self.test_qr_history_guest,
            self.test_subscription_upgrade,
            self.test_subscription_status,
            self.test_premium_unlimited_generation,
            self.test_qr_deletion,
            self.test_unauthorized_deletion
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
            
            # Small delay between tests
            time.sleep(0.5)
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 TEST SUMMARY")
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
    tester = QRCodeAPITester()
    passed, failed = tester.run_all_tests()
    
    # Exit with error code if any tests failed
    exit(0 if failed == 0 else 1)