#!/usr/bin/env python3
"""
Helper script for setting up ngrok for Salt Edge callbacks during development.
"""

import subprocess
import sys
import time
import requests
import json

def check_ngrok_installed():
    """Check if ngrok is installed."""
    try:
        result = subprocess.run(['ngrok', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ ngrok is installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ ngrok not found")
            return False
    except FileNotFoundError:
        print("❌ ngrok not found")
        return False

def get_ngrok_tunnels():
    """Get current ngrok tunnels."""
    try:
        response = requests.get('http://localhost:4040/api/tunnels')
        if response.status_code == 200:
            tunnels = response.json()['tunnels']
            return tunnels
        else:
            return []
    except requests.exceptions.ConnectionError:
        return []

def setup_ngrok():
    """Set up ngrok tunnel for the Money Manager API."""
    print("🔧 Setting up ngrok for Salt Edge callbacks...")
    
    if not check_ngrok_installed():
        print("\n📥 Install ngrok:")
        print("   1. Go to https://ngrok.com/")
        print("   2. Sign up for a free account")
        print("   3. Download and install ngrok")
        print("   4. Follow their setup instructions")
        return False
    
    # Check if ngrok is already running
    tunnels = get_ngrok_tunnels()
    existing_tunnel = None
    
    for tunnel in tunnels:
        if tunnel.get('config', {}).get('addr') == 'localhost:8000':
            existing_tunnel = tunnel
            break
    
    if existing_tunnel:
        public_url = existing_tunnel['public_url']
        print(f"✅ ngrok tunnel already running: {public_url}")
    else:
        print("🚀 Starting ngrok tunnel...")
        print("   Note: This will run in the background")
        
        # Start ngrok in background
        try:
            subprocess.Popen(['ngrok', 'http', '8000'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            
            # Wait a moment for ngrok to start
            print("   Waiting for ngrok to initialize...")
            time.sleep(3)
            
            # Get the public URL
            tunnels = get_ngrok_tunnels()
            if tunnels:
                public_url = tunnels[0]['public_url']
                print(f"✅ ngrok tunnel started: {public_url}")
            else:
                print("❌ Failed to start ngrok tunnel")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start ngrok: {e}")
            return False
    
    # Display callback configuration
    print("\n" + "="*80)
    print("📋 SALT EDGE CALLBACK CONFIGURATION")
    print("="*80)
    
    print("\n🏦 AIS (Account Information) Callbacks:")
    print(f"  Success:         {public_url}/api/v1/callbacks/ais/success")
    print(f"  Failure:         {public_url}/api/v1/callbacks/ais/failure")
    print(f"  Notify:          {public_url}/api/v1/callbacks/ais/notify")
    print(f"  Destroy:         {public_url}/api/v1/callbacks/ais/destroy")
    print(f"  Provider Changes: {public_url}/api/v1/callbacks/ais/provider-changes")
    
    print("\n💳 PIS (Payment Initiation) Callbacks:")
    print(f"  Success:         {public_url}/api/v1/callbacks/pis/success")
    print(f"  Failure:         {public_url}/api/v1/callbacks/pis/failure")
    print(f"  Notify:          {public_url}/api/v1/callbacks/pis/notify")
    
    print("\n🔄 Legacy (Single Endpoint):")
    print(f"  All Types:       {public_url}/api/v1/callbacks/salt-edge")
    
    print("\n📝 Setup Instructions:")
    print("1. Go to https://www.saltedge.com/clients/profile")
    print("2. Navigate to 'Callbacks' section")
    print("3. Configure specific URLs for each callback type (recommended)")
    print("   OR use the single legacy endpoint for all types")
    print("4. Save the configuration")
    
    print(f"\n🧪 Test your callback:")
    print(f"   GET {public_url}/api/v1/callbacks/test")
    
    print(f"\n🔍 Monitor ngrok traffic:")
    print("   Open http://localhost:4040 in your browser")
    
    # Test the callback endpoint
    try:
        test_response = requests.get(f"{public_url}/api/v1/callbacks/test", timeout=10)
        if test_response.status_code == 200:
            print("✅ Callback endpoint is accessible")
        else:
            print(f"⚠️  Callback endpoint returned {test_response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Could not test callback endpoint: {e}")
    
    return True

def main():
    """Main function."""
    print("🔗 Money Manager - ngrok Setup for Salt Edge Callbacks")
    print("="*60)
    
    if not setup_ngrok():
        print("\n❌ Setup failed. Please check the instructions above.")
        sys.exit(1)
    
    print("\n✅ Setup complete!")
    print("\n💡 Tips:")
    print("   • Keep this ngrok tunnel running while testing")
    print("   • Free ngrok accounts get new URLs each time you restart")
    print("   • Update Salt Edge Dashboard if the URL changes")
    print("   • Use ngrok's web interface at http://localhost:4040")
    
    print("\n🚀 Next steps:")
    print("   1. Start your Money Manager API: python main.py")
    print("   2. Configure callbacks in Salt Edge Dashboard")
    print("   3. Test with fake providers")
    print("   4. Monitor webhook traffic in ngrok interface")

if __name__ == "__main__":
    main()
