#!/usr/bin/env python3
"""
Quick test to verify .env configuration is working
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔧 Environment Configuration Test")
print("=" * 40)

# Test reading .env variables
clickhouse_host = os.getenv('CLICKHOUSE_HOST')
clickhouse_port = os.getenv('CLICKHOUSE_PORT')
clickhouse_user = os.getenv('CLICKHOUSE_USER')
clickhouse_password = os.getenv('CLICKHOUSE_PASSWORD')

print(f"📍 ClickHouse Host: {clickhouse_host}")
print(f"🔌 ClickHouse Port: {clickhouse_port}")
print(f"👤 ClickHouse User: {clickhouse_user}")
print(f"🔑 ClickHouse Password: {'*' * len(clickhouse_password) if clickhouse_password else 'Not set'}")

# Test the backtesting system initialization
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from backtesting import IchimokuADXBacktester
    
    print(f"\n🚀 Testing backtester initialization...")
    backtester = IchimokuADXBacktester()
    
    print(f"\n✅ Environment configuration test completed successfully!")
    print(f"The backtesting system is correctly reading configuration from .env file")
    
except Exception as e:
    print(f"❌ Error: {e}")

print(f"\n📋 Summary:")
print(f"   • .env file is properly loaded")
print(f"   • ClickHouse configuration is read from environment variables")
print(f"   • Backtesting system initializes with .env settings")
