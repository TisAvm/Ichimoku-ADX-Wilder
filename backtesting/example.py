"""
Simple example script demonstrating the Ichimoku-ADX-Wilder backtesting system
"""

import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_simple_example():
    """Run a simple example of the backtesting system"""
    
    print("🚀 Simple Ichimoku-ADX-Wilder Backtesting Example")
    print("=" * 60)
    
    # Check if signals file exists
    signals_file = "data/ichimoku_adx_wilder_signals.csv"
    
    if not os.path.exists(signals_file):
        print(f"❌ Signals file not found: {signals_file}")
        print("Please ensure you have the signals file in the data directory.")
        return
    
    try:
        # Import our modules
        from signal_generator import SignalGenerator
        from backtesting import run_complete_backtest
        
        print("📊 Loading signals and running backtest...")
        
        # Simple backtest configuration
        config = {
            'signals_file': signals_file,
            'symbol': 'NIFTY',
            'initial_capital': 100000,
            'position_size': 0.1
        }
        
        # Initialize signal generator
        signal_gen = SignalGenerator(config['signals_file'])
        
        # Get date range
        start_date, end_date = signal_gen.get_date_range()
        
        print(f"📅 Backtesting period: {start_date} to {end_date}")
        print(f"💰 Initial capital: ₹{config['initial_capital']:,}")
        print(f"📏 Position size: {config['position_size']*100}%")
        
        # Run the backtest
        backtester, metrics = run_complete_backtest(
            signals_file=config['signals_file'],
            symbol=config['symbol'],
            start_date=start_date,
            end_date=end_date,
            initial_capital=config['initial_capital'],
            position_size=config['position_size']
        )
        
        print("\n✅ Backtesting completed successfully!")
        print(f"📈 Results saved to ./results/ directory")
        
        # Display summary
        print(f"\n📊 QUICK SUMMARY:")
        print(f"   Total Return: {metrics['Total Return (%)']:.2f}%")
        print(f"   Final Value: ₹{metrics['Final Portfolio Value']:,.2f}")
        print(f"   Max Drawdown: {metrics['Maximum Drawdown (%)']:.2f}%")
        print(f"   Win Rate: {metrics['Win Rate (%)']:.2f}%")
        print(f"   Total Trades: {metrics['Total Trades']}")
        
        # Generate recent signals
        recent_signals = signal_gen.generate_trading_signals_for_live(lookback_days=10)
        
        if not recent_signals.empty:
            latest_signal = recent_signals.iloc[-1]
            print(f"\n🕐 LATEST SIGNAL:")
            print(f"   Date: {latest_signal['datetime']}")
            print(f"   Type: {latest_signal['signal_type']}")
            print(f"   Price: ₹{latest_signal['close']:.2f}")
            
        print(f"\n🎉 Example completed! Check ./results/ for detailed files.")
        
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Please install required packages:")
        print("pip install pandas numpy")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    run_simple_example()
