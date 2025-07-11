#!/usr/bin/env python3
"""
Simple script to run the Ichimoku-ADX backtesting system
Edit config_backtesting.py to customize parameters before running
"""

import sys
import os
from datetime import datetime

def main():
    print("🚀 Ichimoku-ADX-Wilder Backtesting System")
    print("=" * 50)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Import and run the backtesting system
        from backtesting import IchimokuADXBacktester
        
        # Initialize and run backtester
        print("\n🔧 Initializing backtester...")
        backtester = IchimokuADXBacktester()
        
        print("📊 Running comprehensive backtest...")
        results = backtester.run_comprehensive_backtest()
        
        print("\n📈 Generating summary...")
        backtester.print_summary()
        
        print("\n💾 Saving results...")
        backtester.save_results()
        
        print(f"\n✅ Backtesting completed successfully!")
        print(f"📁 Results saved to '{backtester.BACKTEST_NAME}' folder in results directory")
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're in the correct directory and all dependencies are installed")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error during backtesting: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
