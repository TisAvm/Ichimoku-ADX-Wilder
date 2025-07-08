"""
Quick test of backtesting with ClickHouse data using smaller date range
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def quick_backtest():
    """Run a quick backtest with a small date range"""
    
    print("🚀 Quick Backtesting Test with ClickHouse Data")
    print("=" * 50)
    
    try:
        # Import our modules
        from signal_generator import SignalGenerator
        from backtesting import run_complete_backtest
        
        # Check if signals file exists
        signals_file = "data/ichimoku_adx_wilder_signals.csv"
        
        if not os.path.exists(signals_file):
            print(f"❌ Signals file not found: {signals_file}")
            return
        
        print("📊 Running quick backtest (1 week of data)...")
        
        # Quick backtest configuration - just 1 week
        config = {
            'signals_file': signals_file,
            'symbol': 'NIFTY',
            'start_date': '2021-01-01',  # Start date
            'end_date': '2021-01-07',    # Just 1 week
            'initial_capital': 100000,
            'position_size': 0.1
        }
        
        print(f"📅 Period: {config['start_date']} to {config['end_date']}")
        print(f"💰 Capital: ₹{config['initial_capital']:,}")
        print(f"📏 Position size: {config['position_size']*100}%")
        print()
        
        # Run the backtest
        backtester, metrics = run_complete_backtest(
            signals_file=config['signals_file'],
            symbol=config['symbol'],
            start_date=config['start_date'],
            end_date=config['end_date'],
            initial_capital=config['initial_capital'],
            position_size=config['position_size']
        )
        
        print("\n✅ Quick backtest completed!")
        print(f"\n📊 RESULTS SUMMARY:")
        print(f"   Total Return: {metrics['Total Return (%)']:.2f}%")
        print(f"   Final Value: ₹{metrics['Final Portfolio Value']:,.2f}")
        print(f"   Total Trades: {metrics['Total Trades']}")
        print(f"   Win Rate: {metrics['Win Rate (%)']:.2f}%")
        
        if metrics['Total Trades'] > 0:
            print(f"   Avg Trade P&L: ₹{metrics['Total PnL']/metrics['Total Trades']:,.2f}")
        
        print(f"\n📁 Results saved to ./results/ directory")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    quick_backtest()
