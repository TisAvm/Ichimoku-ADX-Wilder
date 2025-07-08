"""
Test the updated ClickHouse query with real data
"""

import os
import sys
from dotenv import load_dotenv
import clickhouse_connect
import pandas as pd

# Load environment variables
load_dotenv()

def test_updated_query():
    """Test the updated ClickHouse query for backtesting"""
    
    print("🧪 Testing Updated ClickHouse Query")
    print("=" * 40)
    
    # Get configuration from .env
    host = os.getenv('CLICKHOUSE_HOST', 'localhost')
    port = int(os.getenv('CLICKHOUSE_PORT', 8123))
    username = os.getenv('CLICKHOUSE_USER', 'default')
    password = os.getenv('CLICKHOUSE_PASSWORD', '')
    
    try:
        # Connect to ClickHouse
        client = clickhouse_connect.get_client(
            host=host,
            port=port,
            username=username,
            password=password
        )
        
        print("✅ Connected to ClickHouse")
        
        # Test the exact query from backtesting
        symbol = 'NIFTY'
        start_date = '2021-01-01'
        end_date = '2021-01-02'
        
        query = f"""
        SELECT 
            datetime,
            open,
            high,
            low,
            close,
            volume
        FROM minute_data.spot
        WHERE underlying_symbol = '{symbol}'
          AND datetime >= '{start_date} 09:20:00'
          AND datetime <= '{end_date} 15:25:00'
          AND formatDateTime(datetime, '%H:%M') >= '09:20'
          AND formatDateTime(datetime, '%H:%M') <= '15:25'
        ORDER BY datetime
        LIMIT 20
        """
        
        print(f"📊 Testing query for {symbol} from {start_date} to {end_date}")
        print("Query:")
        print(query)
        print()
        
        result = client.query(query)
        
        if result.result_rows:
            df = pd.DataFrame(result.result_rows, columns=result.column_names)
            print(f"✅ Query successful! Retrieved {len(df)} records")
            print("\nSample data:")
            print(df.head(10).to_string(index=False))
            
            # Check time range
            df['datetime'] = pd.to_datetime(df['datetime'])
            print(f"\nTime range verification:")
            print(f"First record: {df['datetime'].min()}")
            print(f"Last record: {df['datetime'].max()}")
            
            # Check trading hours
            df['time'] = df['datetime'].dt.time
            print(f"Earliest time: {df['time'].min()}")
            print(f"Latest time: {df['time'].max()}")
            
            return True
            
        else:
            print("❌ Query returned no results")
            return False
            
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False


if __name__ == "__main__":
    test_updated_query()
