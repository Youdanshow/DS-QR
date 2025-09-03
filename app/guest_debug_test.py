#!/usr/bin/env python3
"""
Debug test for guest user functionality
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://qr-maker-2.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def test_guest_behavior():
    """Test guest user behavior with same session"""
    session = requests.Session()
    
    print("🔍 Testing Guest User Behavior")
    print(f"Backend URL: {API_BASE}")
    print("=" * 50)
    
    # Generate QR codes as guest using same session
    for i in range(5):  # Try to generate 5 (should fail after 3)
        qr_data = {
            "url": f"https://www.test{i+1}.com",
            "size": "150x150"
        }
        
        response = session.post(f"{API_BASE}/qr/generate", json=qr_data)
        
        print(f"QR {i+1}: Status {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            limits = data["limits"]
            print(f"   Limits: {limits['used']}/{limits['max']} (Premium: {limits['isPremium']})")
        else:
            print(f"   Error: {response.text}")
            break
    
    # Check history
    print("\n📋 Checking Guest History:")
    response = session.get(f"{API_BASE}/qr/history")
    
    if response.status_code == 200:
        data = response.json()
        qr_codes = data["qrCodes"]
        limits = data["limits"]
        print(f"   Found {len(qr_codes)} QR codes")
        print(f"   Limits: {limits['used']}/{limits['max']} (Premium: {limits['isPremium']})")
    else:
        print(f"   Error: {response.text}")

if __name__ == "__main__":
    test_guest_behavior()