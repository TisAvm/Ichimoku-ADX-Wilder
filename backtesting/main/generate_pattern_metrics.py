#!/usr/bin/env python3
"""
Generate pattern-wise metrics CSV from existing backtest results
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backtesting import IchimokuADXBacktester

def generate_pattern_metrics():
    """Generate comprehensive pattern-wise metrics"""
    
    print("📊 Generating Pattern-Wise Metrics with ₹100,000 Capital per Pattern")
    print("=" * 70)
    
    # Initialize backtester
    backtester = IchimokuADXBacktester()
    
    # Run backtest to get results
    print("🔄 Loading backtest results...")
    results = backtester.run_comprehensive_backtest()
    
    # Generate pattern metrics
    output_dir = os.path.join('../results', backtester.BACKTEST_NAME)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n💾 Saving pattern metrics to {output_dir}")
    
    # Calculate and save pattern metrics with ₹100,000 per pattern
    pattern_capital = 100000
    metrics_path, summary_path, metrics_df = backtester.save_pattern_metrics_csv(output_dir, pattern_capital)
    
    # Display detailed metrics table
    print(f"\n📈 DETAILED PATTERN METRICS (Capital: ₹{pattern_capital:,} per pattern)")
    print("=" * 120)
    
    # Key columns to display
    display_columns = [
        'pattern_id', 'pattern_name', 'total_trades', 'win_rate_pct', 
        'total_net_pnl', 'total_return_pct', 'max_drawdown_pct', 
        'sharpe_ratio', 'profit_factor', 'performance_score'
    ]
    
    # Format and display the table
    pd_display = metrics_df[display_columns].copy()
    pd_display['pattern_name'] = pd_display['pattern_name'].str[:25]  # Truncate long names
    
    print(pd_display.to_string(index=False, float_format='%.2f'))
    
    # Show risk-adjusted rankings
    print(f"\n🎯 RISK-ADJUSTED RANKINGS:")
    print("-" * 60)
    print(f"{'Rank':<4} {'Pattern':<8} {'Name':<25} {'Sharpe':<8} {'Return%':<8}")
    print("-" * 60)
    
    sharpe_sorted = metrics_df.sort_values('sharpe_ratio', ascending=False).head(5)
    for i, (_, row) in enumerate(sharpe_sorted.iterrows()):
        print(f"{i+1:<4} {row['pattern_id']:<8} {row['pattern_name'][:23]:<25} "
              f"{row['sharpe_ratio']:<8.3f} {row['total_return_pct']:<8.2f}")
    
    # Show absolute return rankings
    print(f"\n💰 ABSOLUTE RETURN RANKINGS:")
    print("-" * 60)
    print(f"{'Rank':<4} {'Pattern':<8} {'Name':<25} {'P&L':<12} {'Return%':<8}")
    print("-" * 60)
    
    return_sorted = metrics_df.sort_values('total_net_pnl', ascending=False).head(5)
    for i, (_, row) in enumerate(return_sorted.iterrows()):
        print(f"{i+1:<4} {row['pattern_id']:<8} {row['pattern_name'][:23]:<25} "
              f"₹{row['total_net_pnl']:>10,.0f} {row['total_return_pct']:<8.2f}")
    
    print(f"\n✅ Pattern metrics saved successfully!")
    print(f"📁 Files created:")
    print(f"   - {metrics_path}")
    print(f"   - {summary_path}")
    
    return metrics_df

if __name__ == "__main__":
    import pandas as pd
    generate_pattern_metrics()
