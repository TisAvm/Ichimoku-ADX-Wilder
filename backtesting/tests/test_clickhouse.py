"""
Simple ClickHouse connectivity test using .env configuration
"""

import os
import sys
from dotenv import load_dotenv
import clickhouse_connect
import pandas as pd

# Load environment variables
load_dotenv()

def test_clickhouse_connection():
    """Test ClickHouse connectivity and basic queries"""
    
    print("🔍 Testing ClickHouse Connectivity")
    print("=" * 40)
    
    # Get configuration from .env
    host = os.getenv('CLICKHOUSE_HOST', 'localhost')
    port = int(os.getenv('CLICKHOUSE_PORT',8123))
    username = os.getenv('CLICKHOUSE_USER', 'default')
    password = os.getenv('CLICKHOUSE_PASSWORD', '')
    
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password) if password else 'None'}")
    print()
    
    try:
        # Connect to ClickHouse
        client = clickhouse_connect.get_client(
            host=host,
            port=port,
            username=username,
            password=password
        )
        
        print("✅ Successfully connected to ClickHouse")
        
        # Test 1: Show databases
        print("\n📁 Available databases:")
        databases = client.query("SHOW DATABASES")
        for db in databases.result_rows:
            print(f"  - {db[0]}")
        
        # Test 2: Check minute_data database
        print("\n📊 Tables in minute_data database:")
        try:
            tables = client.query("SHOW TABLES FROM minute_data")
            for table in tables.result_rows:
                print(f"  - {table[0]}")
        except Exception as e:
            print(f"  Error accessing minute_data: {e}")
        
        # Test 3: Check spot table structure
        print("\n🔧 Structure of minute_data.spot table:")
        try:
            structure = client.query("DESCRIBE minute_data.spot")
            for col in structure.result_rows:
                print(f"  - {col[0]}: {col[1]}")
        except Exception as e:
            print(f"  Error describing spot table: {e}")
        
        # Test 4: Sample data from spot table
        print("\n📈 Sample data from minute_data.spot (first 5 rows):")
        try:
            sample_query = """
            SELECT datetime, underlying_symbol, open, high, low, close
            FROM minute_data.spot
            ORDER BY datetime DESC
            LIMIT 5
            """
            sample_data = client.query(sample_query)
            
            if sample_data.result_rows:
                df = pd.DataFrame(sample_data.result_rows, columns=sample_data.column_names)
                print(df.to_string(index=False))
                
                # Check available symbols
                print(f"\n🎯 Available symbols in spot table:")
                symbols_query = """
                SELECT DISTINCT underlying_symbol
                FROM minute_data.spot
                ORDER BY underlying_symbol
                LIMIT 10
                """
                symbols = client.query(symbols_query)
                for symbol in symbols.result_rows:
                    print(f"  - {symbol[0]}")
            else:
                print("  No data found in spot table")
                
        except Exception as e:
            print(f"  Error querying spot table: {e}")
        
        # Test 5: Test NIFTY data with time filtering
        print(f"\n🕐 Testing NIFTY data with time filtering:")
        try:
            nifty_query = """
            SELECT datetime, underlying_symbol, open, high, low, close
            FROM minute_data.spot
            WHERE underlying_symbol = 'NIFTY'
              AND datetime >= '2021-01-01 00:00:00'
              AND datetime <= '2021-01-02 23:59:59'
            ORDER BY datetime
            LIMIT 10
            """
            nifty_data = client.query(nifty_query)
            
            if nifty_data.result_rows:
                nifty_df = pd.DataFrame(nifty_data.result_rows, columns=nifty_data.column_names)
                print(nifty_df.to_string(index=False))
            else:
                print("  No NIFTY data found for the specified period")
                
        except Exception as e:
            print(f"  Error querying NIFTY data: {e}")
        
        print(f"\n✅ ClickHouse connectivity test completed!")
        
    except Exception as e:
        print(f"❌ ClickHouse connection failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    test_clickhouse_connection()
