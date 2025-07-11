#!/usr/bin/env python3
"""
Display comprehensive pattern-wise metrics in a readable format
"""

import pandas as pd
import os

def display_pattern_metrics():
    """Display pattern metrics in formatted tables"""
    
    # Read the pattern metrics CSV
    metrics_file = '../results/5min_full_backtest/pattern_wise_metrics.csv'
    
    if not os.path.exists(metrics_file):
        print("❌ Pattern metrics file not found. Please run generate_pattern_metrics.py first.")
        return
    
    df = pd.read_csv(metrics_file)
    
    print("📊 ICHIMOKU-ADX PATTERN ANALYSIS")
    print("═" * 80)
    print("🎯 Capital Allocation: ₹100,000 per pattern")
    print("📅 Analysis Period: 2024-01-01 to 2025-06-30")
    print("⏱️  Timeframe: 5-minute data")
    print("═" * 80)
    
    # Summary table
    print("\n📈 PATTERN PERFORMANCE SUMMARY")
    print("-" * 120)
    print(f"{'Rank':<4} {'ID':<3} {'Pattern Name':<35} {'Trades':<7} {'Win%':<6} {'P&L (₹)':<12} {'Return%':<8} {'Sharpe':<7} {'Score':<6}")
    print("-" * 120)
    
    for i, row in df.iterrows():
        print(f"{i+1:<4} {row['pattern_id']:<3} {row['pattern_name'][:33]:<35} "
              f"{row['total_trades']:<7} {row['win_rate_pct']:<6.1f} "
              f"{row['total_net_pnl']:>11,.0f} {row['total_return_pct']:<8.2f} "
              f"{row['sharpe_ratio']:<7.3f} {row['performance_score']:<6.1f}")
    
    # Risk Analysis
    print("\n🛡️ RISK ANALYSIS")
    print("-" * 80)
    print(f"{'Pattern':<3} {'Max Drawdown':<13} {'Volatility':<11} {'Profit Factor':<13} {'Recovery Factor':<15}")
    print("-" * 80)
    
    for _, row in df.iterrows():
        print(f"{row['pattern_id']:<3} {row['max_drawdown_pct']:>11.2f}% "
              f"{row['volatility_pct']:>9.4f}% {row['profit_factor']:>11.2f} "
              f"{row['recovery_factor']:>13.2f}")
    
    # Trading Activity Analysis
    print("\n📊 TRADING ACTIVITY")
    print("-" * 80)
    print(f"{'Pattern':<3} {'Signals':<8} {'Trades/Month':<12} {'Avg Hold (min)':<14} {'Buy/Sell Split':<15}")
    print("-" * 80)
    
    for _, row in df.iterrows():
        buy_sell_ratio = f"{row['buy_signals']}/{row['sell_signals']}"
        print(f"{row['pattern_id']:<3} {row['total_signals']:<8} "
              f"{row['trades_per_month']:>10.1f} {row['avg_holding_minutes']:>12.1f} "
              f"{buy_sell_ratio:>13}")
    
    # Best and Worst Trade Analysis
    print("\n🎯 TRADE EXTREMES")
    print("-" * 80)
    print(f"{'Pattern':<3} {'Best Trade (₹)':<13} {'Best %':<8} {'Worst Trade (₹)':<15} {'Worst %':<8}")
    print("-" * 80)
    
    for _, row in df.iterrows():
        print(f"{row['pattern_id']:<3} {row['best_trade_pnl']:>11,.0f} "
              f"{row['best_trade_return_pct']:>6.3f}% "
              f"{row['worst_trade_pnl']:>13,.0f} {row['worst_trade_return_pct']:>6.3f}%")
    
    # Top Performers by Different Metrics
    print("\n🏆 TOP PERFORMERS BY CATEGORY")
    print("-" * 60)
    
    # Best by Return
    best_return = df.nlargest(3, 'total_return_pct')
    print("💰 Highest Returns:")
    for i, (_, row) in enumerate(best_return.iterrows()):
        print(f"   {i+1}. Pattern {row['pattern_id']} ({row['pattern_name'][:30]}): {row['total_return_pct']:.2f}%")
    
    # Best by Sharpe Ratio
    best_sharpe = df.nlargest(3, 'sharpe_ratio')
    print("\n📊 Best Risk-Adjusted Returns (Sharpe):")
    for i, (_, row) in enumerate(best_sharpe.iterrows()):
        print(f"   {i+1}. Pattern {row['pattern_id']} ({row['pattern_name'][:30]}): {row['sharpe_ratio']:.3f}")
    
    # Most Active
    most_active = df.nlargest(3, 'total_trades')
    print("\n⚡ Most Active Patterns:")
    for i, (_, row) in enumerate(most_active.iterrows()):
        print(f"   {i+1}. Pattern {row['pattern_id']} ({row['pattern_name'][:30]}): {row['total_trades']:,} trades")
    
    # Highest Win Rate
    best_winrate = df.nlargest(3, 'win_rate_pct')
    print("\n🎯 Highest Win Rates:")
    for i, (_, row) in enumerate(best_winrate.iterrows()):
        print(f"   {i+1}. Pattern {row['pattern_id']} ({row['pattern_name'][:30]}): {row['win_rate_pct']:.1f}%")
    
    # Key Insights
    print("\n💡 KEY INSIGHTS")
    print("-" * 60)
    
    profitable_patterns = df[df['total_net_pnl'] > 0]
    losing_patterns = df[df['total_net_pnl'] < 0]
    
    print(f"✅ Profitable Patterns: {len(profitable_patterns)}/10")
    print(f"❌ Losing Patterns: {len(losing_patterns)}/10")
    print(f"🏅 Best Overall: Pattern {df.iloc[0]['pattern_id']} ({df.iloc[0]['pattern_name']})")
    print(f"📈 Total Potential Return: {df['total_net_pnl'].sum():,.0f} ₹ ({df['total_return_pct'].sum():.1f}%)")
    print(f"⚖️  Average Sharpe Ratio: {df['sharpe_ratio'].mean():.3f}")
    print(f"🔥 Most Consistent: Pattern {df.loc[df['volatility_pct'].idxmin(), 'pattern_id']} (lowest volatility)")
    
    # Risk Warning
    print("\n⚠️ RISK CONSIDERATIONS")
    print("-" * 60)
    high_drawdown = df[df['max_drawdown_pct'] < -3]
    if len(high_drawdown) > 0:
        print("🚨 High Drawdown Patterns (>3%):")
        for _, row in high_drawdown.iterrows():
            print(f"   - Pattern {row['pattern_id']}: {row['max_drawdown_pct']:.2f}% max drawdown")
    
    negative_sharpe = df[df['sharpe_ratio'] < 0]
    if len(negative_sharpe) > 0:
        print("⚠️ Negative Sharpe Ratios:")
        for _, row in negative_sharpe.iterrows():
            print(f"   - Pattern {row['pattern_id']}: {row['sharpe_ratio']:.3f} Sharpe ratio")
    
    print("\n📁 Detailed data available in:")
    print("   - pattern_wise_metrics.csv (complete metrics)")
    print("   - pattern_summary_metrics.csv (key metrics)")

if __name__ == "__main__":
    display_pattern_metrics()
