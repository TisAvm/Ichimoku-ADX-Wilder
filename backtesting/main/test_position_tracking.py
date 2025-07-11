#!/usr/bin/env python3
"""
Test script to demonstrate the position tracking functionality
that prevents consecutive signals when a position is already active.
"""

import pandas as pd
from datetime import datetime, timedelta
import numpy as np

def create_test_signals():
    """Create test data with consecutive signals to test position tracking"""
    
    # Create sample data with consecutive signals
    dates = pd.date_range('2024-01-01 09:15:00', periods=20, freq='5min')
    
    # Create test signals - some consecutive
    pattern_0_signals = [0, 1, 1, 0, 0, -1, -1, 0, 0, 1, 1, 1, 0, 0, 0, -1, 0, 0, 1, 0]
    close_prices = [100 + i*0.5 + np.random.normal(0, 0.2) for i in range(20)]
    
    data = {
        'datetime': dates,
        'close': close_prices,
        'pattern_0': pattern_0_signals
    }
    
    df = pd.DataFrame(data)
    
    # Save test signals
    test_file = '/home/algolinux/Documents/aviral/Ichimoku-ADX-Wilder/backtesting/data/test_signals.csv'
    df.to_csv(test_file, index=False)
    print(f"Created test signals file: {test_file}")
    
    return df

def analyze_position_tracking():
    """Demonstrate how position tracking prevents consecutive signals"""
    
    print("=" * 60)
    print("POSITION TRACKING DEMONSTRATION")
    print("=" * 60)
    
    # Create test data
    df = create_test_signals()
    
    print("\nTest Signal Data:")
    print("-" * 50)
    print(f"{'Time':<20} {'Close':<8} {'Signal':<8} {'Action'}")
    print("-" * 50)
    
    # Simulate the position tracking logic
    active_position = None
    position_exit_time = None
    max_holding_minutes = 30  # 30 minutes max holding
    trades_taken = []
    signals_skipped = []
    
    for idx, row in df.iterrows():
        signal_time = row['datetime']
        signal_type = row['pattern_0']
        close_price = row['close']
        
        action = "No Signal"
        
        if signal_type != 0:
            # Check if we have an active position
            if active_position is not None and position_exit_time is not None:
                if signal_time < position_exit_time:
                    # Position is still active, skip this signal
                    action = f"SKIP ({active_position} active)"
                    signals_skipped.append({
                        'time': signal_time,
                        'signal': signal_type,
                        'reason': f'{active_position} position active'
                    })
                else:
                    # Position has expired, can take new position
                    active_position = None
                    position_exit_time = None
            
            # If no active position, take the signal
            if active_position is None:
                if signal_type == 1:
                    active_position = 'LONG'
                    action = "ENTER LONG"
                elif signal_type == -1:
                    active_position = 'SHORT'
                    action = "ENTER SHORT"
                
                # Set position exit time
                adjusted_signal_time = signal_time + timedelta(minutes=5)  # 5min timeframe
                position_exit_time = adjusted_signal_time + timedelta(minutes=max_holding_minutes)
                
                trades_taken.append({
                    'time': signal_time,
                    'signal': signal_type,
                    'position': active_position,
                    'exit_time': position_exit_time
                })
        
        signal_str = "BUY" if signal_type == 1 else ("SELL" if signal_type == -1 else "0")
        print(f"{signal_time.strftime('%Y-%m-%d %H:%M'):<20} {close_price:<8.2f} {signal_str:<8} {action}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total signals generated: {len(df[df['pattern_0'] != 0])}")
    print(f"Trades taken: {len(trades_taken)}")
    print(f"Signals skipped: {len(signals_skipped)}")
    
    print(f"\nTrades Taken:")
    for i, trade in enumerate(trades_taken, 1):
        print(f"  {i}. {trade['time'].strftime('%H:%M')} - {trade['position']} (exit by {trade['exit_time'].strftime('%H:%M')})")
    
    print(f"\nSignals Skipped:")
    for i, skip in enumerate(signals_skipped, 1):
        signal_str = "BUY" if skip['signal'] == 1 else "SELL"
        print(f"  {i}. {skip['time'].strftime('%H:%M')} - {signal_str} signal ({skip['reason']})")
    
    efficiency = len(trades_taken) / len(df[df['pattern_0'] != 0]) * 100
    print(f"\nSignal Efficiency: {efficiency:.1f}% (prevented overtrading)")

if __name__ == "__main__":
    analyze_position_tracking()
