#!/usr/bin/env python3
"""
Standalone script to run Ichimoku-ADX-Wilder backtesting
This script can be run independently to perform comprehensive backtesting
"""

import os
import sys
import argparse
from datetime import datetime

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main function to run the backtesting system"""
    
    parser = argparse.ArgumentParser(description='Ichimoku-ADX-Wilder Backtesting System')
    parser.add_argument('--signals', default='data/ichimoku_adx_wilder_signals.csv',
                       help='Path to signals CSV file')
    parser.add_argument('--capital', type=float, default=100000,
                       help='Initial capital (default: 100000)')
    parser.add_argument('--position-size', type=float, default=0.1,
                       help='Position size as fraction (default: 0.1)')
    parser.add_argument('--symbol', default='NIFTY',
                       help='Trading symbol (default: NIFTY)')
    parser.add_argument('--start-date', type=str,
                       help='Start date (YYYY-MM-DD). If not provided, uses signal data range')
    parser.add_argument('--end-date', type=str,
                       help='End date (YYYY-MM-DD). If not provided, uses signal data range')
    parser.add_argument('--scenarios', action='store_true',
                       help='Run multiple scenarios')
    parser.add_argument('--output-dir', default='./results/',
                       help='Output directory for results (default: ./results/)')
    
    args = parser.parse_args()
    
    print("🚀 Ichimoku-ADX-Wilder Backtesting System")
    print("=" * 60)
    
    try:
        # Import modules
        from signal_generator import SignalGenerator
        from backtesting import run_complete_backtest
        
        # Check if signals file exists
        if not os.path.exists(args.signals):
            print(f"❌ Signals file not found: {args.signals}")
            print("Please provide a valid signals file path.")
            return
        
        # Initialize signal generator
        print(f"📊 Loading signals from: {args.signals}")
        signal_gen = SignalGenerator(args.signals)
        
        # Get date range
        start_date, end_date = signal_gen.get_date_range()
        
        # Use provided dates or default to signal data range
        if args.start_date:
            start_date = args.start_date
        if args.end_date:
            end_date = args.end_date
        
        print(f"📅 Backtesting period: {start_date} to {end_date}")
        print(f"💰 Initial capital: ₹{args.capital:,.2f}")
        print(f"📏 Position size: {args.position_size*100}%")
        print(f"📊 Symbol: {args.symbol}")
        
        # Create output directory
        os.makedirs(args.output_dir, exist_ok=True)
        
        if args.scenarios:
            # Run multiple scenarios
            print("\n🔄 Running multiple scenarios...")
            scenarios = signal_gen.run_multiple_scenarios()
            signal_gen.compare_scenarios(scenarios)
            
        else:
            # Run single backtest
            print("\n🎯 Running single backtest...")
            backtester, metrics = run_complete_backtest(
                signals_file=args.signals,
                symbol=args.symbol,
                start_date=start_date,
                end_date=end_date,
                initial_capital=args.capital,
                position_size=args.position_size
            )
            
            # Save results to specified directory
            backtester.save_results(args.output_dir)
        
        # Generate recent signals
        print("\n📈 Generating recent signals...")
        recent_signals = signal_gen.generate_trading_signals_for_live(lookback_days=30)
        
        if not recent_signals.empty:
            recent_signals.to_csv(f"{args.output_dir}/recent_signals.csv", index=False)
            print(f"Recent signals saved to {args.output_dir}/recent_signals.csv")
        
        print(f"\n✅ Backtesting completed successfully!")
        print(f"📁 Results saved to: {args.output_dir}")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please install required dependencies:")
        print("pip install -r requirements.txt")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
