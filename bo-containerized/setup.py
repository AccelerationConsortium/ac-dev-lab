#!/usr/bin/env python3
"""
Setup script for containerized BO workflow
Configures Slack webhook block automatically
"""

import os
import asyncio
from prefect.blocks.notifications import SlackWebhook

async def setup_slack_webhook():
    """Create the Slack webhook block programmatically"""
    
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("❌ SLACK_WEBHOOK_URL environment variable not set!")
        return False
    
    try:
        # Create the Slack webhook block
        slack_webhook = SlackWebhook(url=webhook_url)
        
        # Save it with the name expected by your BO workflow
        await slack_webhook.save("prefect-test", overwrite=True)
        
        print("✅ Slack webhook block 'prefect-test' created successfully!")
        print(f"📍 Webhook URL: {webhook_url[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ Error creating Slack webhook block: {e}")
        return False

async def verify_setup():
    """Verify that all components are ready"""
    
    print("🔍 Verifying setup...")
    
    # Check if we can import required packages
    try:
        import ax
        import prefect
        import numpy
        print(f"✅ ax-platform: installed")
        print(f"✅ prefect: {prefect.__version__}")
        print(f"✅ numpy: {numpy.__version__}")
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        return False
    
    # Check Slack webhook
    webhook_success = await setup_slack_webhook()
    
    if webhook_success:
        print("\n🚀 Setup completed successfully!")
        print("You can now run your BO workflow with:")
        print("   python complete_workflow/bo_hitl_slack_tutorial.py")
        return True
    else:
        return False

if __name__ == "__main__":
    print("🔧 Setting up Containerized BO HITL Workflow...")
    
    # Run setup
    success = asyncio.run(verify_setup())
    
    if success:
        print("\n✅ Container is ready for BO experiments!")
    else:
        print("\n❌ Setup failed. Check the errors above.")
        exit(1)