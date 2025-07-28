#!/usr/bin/env python3
"""
Setup script for Medical Claim RPA AI Agent
This script helps set up the Google Drive API credentials
"""

import os
import json
import webbrowser
from google_auth_oauthlib.flow import Flow

def setup_google_credentials():
    """Interactive setup for Google Drive API credentials"""
    
    print("🏥 Medical Claim RPA AI Agent Setup")
    print("=" * 50)
    print()
    
    # Check if credentials.json exists
    if not os.path.exists('credentials.json'):
        print("❌ credentials.json file not found!")
        print()
        print("Please follow these steps:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing project")
        print("3. Enable Google Drive API")
        print("4. Create credentials (OAuth 2.0 Client ID)")
        print("5. Download the JSON file and rename it to 'credentials.json'")
        print("6. Place the file in the same directory as this script")
        print()
        return False
    
    print("✅ Found credentials.json file")
    
    # Set up OAuth flow
    SCOPES = ['https://www.googleapis.com/auth/drive']
    
    try:
        flow = Flow.from_client_secrets_file(
            'credentials.json',
            scopes=SCOPES,
            redirect_uri='http://localhost:8080/callback'
        )
        
        # Get authorization URL
        auth_url, _ = flow.authorization_url(prompt='consent')
        
        print()
        print("🔐 Google OAuth Authorization Required")
        print("Opening browser for authorization...")
        print()
        
        # Open browser
        webbrowser.open(auth_url)
        
        print("If browser didn't open, please visit this URL:")
        print(auth_url)
        print()
        
        # Get authorization code from user
        auth_code = input("Enter the authorization code from Google: ").strip()
        
        if not auth_code:
            print("❌ No authorization code provided")
            return False
        
        # Exchange code for token
        flow.fetch_token(code=auth_code)
        credentials = flow.credentials
        
        # Save refresh token for production use
        print()
        print("✅ Authorization successful!")
        print()
        print("For production deployment, add these environment variables:")
        print(f"GOOGLE_CLIENT_ID={credentials.client_id}")
        print(f"GOOGLE_CLIENT_SECRET={credentials.client_secret}")
        print(f"GOOGLE_REFRESH_TOKEN={credentials.refresh_token}")
        print()
        
        # Create .env file
        with open('.env', 'w') as f:
            f.write(f"GOOGLE_CLIENT_ID={credentials.client_id}\n")
            f.write(f"GOOGLE_CLIENT_SECRET={credentials.client_secret}\n")
            f.write(f"GOOGLE_REFRESH_TOKEN={credentials.refresh_token}\n")
            f.write("ENVIRONMENT=development\n")
            f.write("MAX_LINES_PER_CLAIM=28\n")
            f.write("ER_CONSOLIDATION_HOURS=24\n")
            f.write("IMAGING_GROUPING_HOURS=24\n")
        
        print("✅ Created .env file with your credentials")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {str(e)}")
        return False

def create_sample_data():
    """Create sample data file for testing"""
    
    sample_data = """Patient ID,Claim ID,Revenue Code,HCPCS Code,Description,Service Date,Units,Charge Amount,Total Charges
P001,C001,0450,99284,ER Visit Level 4,2024-06-01,1,1200,1200
P001,C001,2500,A0428,Ambulance Service,2024-06-01,1,500,500
P001,C001,0300,36415,Lab Draw - CBC,2024-06-01,1,150,150
P001,C001,0300,36415,Lab Draw - CMP,2024-06-01,1,150,150
P001,C001,0350,70450,CT Scan Head/Brain,2024-06-01,1,2000,2000
P001,C001,0350,70553,MRI Brain w/o & w contrast,2024-06-01,1,4500,4500"""
    
    with open('sample_medical_claims.csv', 'w') as f:
        f.write(sample_data)
    
    print("✅ Created sample_medical_claims.csv for testing")

def check_dependencies():
    """Check if all required packages are installed"""
    
    required_packages = [
        'streamlit',
        'google-auth',
        'google-auth-oauthlib',
        'google-api-python-client',
        'pandas
