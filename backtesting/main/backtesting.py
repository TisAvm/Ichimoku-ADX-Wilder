"""
Enhanced Backtesting System for Ichimoku-ADX-Wilder Strategy
Tests signals on 1-minute ClickHouse data to validate signal accuracy and profitability
"""

import os
import sys
import pandas as pd
import numpy as np
import clickhouse_connect
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dotenv import load_dotenv
import warnings
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from io import StringIO
import json
# Import user configuration
from config_backtesting import *

warnings.filterwarnings('ignore')

# Set matplotlib backend for server environments
plt.style.use('default')
sns.set_palette("husl")

# Load environment variables
load_dotenv()



class IchimokuADXBacktester:
    """
    Comprehensive backtesting system for Ichimoku-ADX signals
    """
    
    def __init__(self):
        """Initialize the backtester with configuration"""
        
        # User configurable variables - loaded from config_backtesting.py
        self.TIMEFRAME = TIMEFRAME
        self.CSV_PATH = CSV_PATH
        self.START_DATE = START_DATE
        self.END_DATE = END_DATE
        self.SYMBOL = SYMBOL
        self.INITIAL_CAPITAL = INITIAL_CAPITAL
        self.POSITION_SIZE = POSITION_SIZE
        self.QUANTITY = getattr(globals(), 'QUANTITY', 1) # Default to 1 if not defined
        self.TRANSACTION_COST = TRANSACTION_COST
        self.MIN_HOLDING_MINUTES = MIN_HOLDING_MINUTES
        self.MAX_HOLDING_MINUTES = MAX_HOLDING_MINUTES
        self.STOP_LOSS_PCT = STOP_LOSS_PCT
        self.TAKE_PROFIT_PCT = TAKE_PROFIT_PCT
        self.OUTPUT_DIR = OUTPUT_DIR
        self.BACKTEST_NAME = BACKTEST_NAME
        
        # Pattern names for analysis
        self.PATTERN_NAMES = {
            0: "Price-Tenkan Crossover",
            1: "Tenkan-Kijun Crossover", 
            2: "Price-Senkou A Crossover",
            3: "Senkou A-B Crossover",
            4: "Chikou Span Confirmation",
            5: "Price Bounce/Rejection at Tenkan",
            6: "Price Crossing Kijun",
            7: "Price Bounce/Rejection at Senkou B",
            8: "Price Above/Below Cloud",
            9: "Additional Pattern"
        }
        
        # Initialize ClickHouse client
        self.client = self._init_clickhouse()
        
        # Results storage
        self.results = {}
        self.detailed_trades = []
        
    def _init_clickhouse(self):
        """Initialize ClickHouse connection"""
        try:
            host = os.getenv('CLICKHOUSE_HOST', 'localhost')
            port = int(os.getenv('CLICKHOUSE_PORT', 8123))
            username = os.getenv('CLICKHOUSE_USER', 'default')
            password = os.getenv('CLICKHOUSE_PASSWORD', '')
            
            client = clickhouse_connect.get_client(
                host=host,
                port=port,
                username=username,
                password=password
            )
            
            print(f"✅ Connected to ClickHouse at {host}:{port}")
            return client
            
        except Exception as e:
            print(f"❌ ClickHouse connection failed: {e}")
            raise
    
    def load_signals(self) -> pd.DataFrame:
        """Load signals from CSV file"""
        try:
            print(f"📊 Loading signals from {self.CSV_PATH}")
            signals_df = pd.read_csv(self.CSV_PATH)
            signals_df['datetime'] = pd.to_datetime(signals_df['datetime'])
            
            # Filter by date range
            mask = (signals_df['datetime'] >= self.START_DATE) & (signals_df['datetime'] <= self.END_DATE)
            signals_df = signals_df[mask].copy()
            
            print(f"📈 Loaded {len(signals_df)} signal data points from {signals_df['datetime'].min()} to {signals_df['datetime'].max()}")
            return signals_df
            
        except Exception as e:
            print(f"❌ Error loading signals: {e}")
            raise
    
    def get_minute_data(self, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        """Get 1-minute data from ClickHouse for the specified time range"""
        try:
            query = f"""
            SELECT datetime, open, high, low, close
            FROM minute_data.spot
            WHERE underlying_symbol = '{self.SYMBOL}'
              AND datetime >= '{start_time.strftime('%Y-%m-%d %H:%M:%S')}'
              AND datetime <= '{end_time.strftime('%Y-%m-%d %H:%M:%S')}'
            ORDER BY datetime
            """
            
            result = self.client.query(query)
            
            if not result.result_rows:
                return pd.DataFrame()
            
            df = pd.DataFrame(result.result_rows, columns=result.column_names)
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.set_index('datetime')
            
            return df
            
        except Exception as e:
            print(f"❌ Error fetching minute data: {e}")
            return pd.DataFrame()
    
    def analyze_signal_accuracy(self, signal_time: datetime, signal_type: int, entry_price: float) -> Dict[str, Any]:
        """
        Analyze how long a signal was profitable and by how much
        signal_type: 1 for buy, -1 for sell, 0 for no signal
        Uses quantity-based trading (fixed number of shares/units)
        """
        if signal_type == 0:
            return None
        
        # Adjust signal time based on timeframe
        # If signal came at 9:45 on 5min data, it actually came at 9:50 (candle close)
        if self.TIMEFRAME == "5min":
            adjusted_signal_time = signal_time + timedelta(minutes=5)
        elif self.TIMEFRAME == "10min":
            adjusted_signal_time = signal_time + timedelta(minutes=10)
        elif self.TIMEFRAME == "15min":
            adjusted_signal_time = signal_time + timedelta(minutes=15)
        else:
            adjusted_signal_time = signal_time
        
        # Get minute data for analysis period
        end_time = adjusted_signal_time + timedelta(minutes=self.MAX_HOLDING_MINUTES)
        minute_data = self.get_minute_data(adjusted_signal_time, end_time)
        
        if minute_data.empty:
            return None
        
        # Calculate transaction costs
        buy_cost = entry_price * self.QUANTITY * self.TRANSACTION_COST
        sell_cost = 0  # Will be calculated at exit
        
        # Initialize tracking variables
        max_profit = 0
        max_loss = 0
        profit_duration = 0
        loss_duration = 0
        total_profitable_minutes = 0
        total_loss_minutes = 0
        
        # Calculate stop loss and take profit levels
        if signal_type == 1:  # Buy signal
            stop_loss_price = entry_price * (1 - self.STOP_LOSS_PCT)
            take_profit_price = entry_price * (1 + self.TAKE_PROFIT_PCT)
            position_direction = "BUY"
        else:  # Sell signal
            stop_loss_price = entry_price * (1 + self.STOP_LOSS_PCT)
            take_profit_price = entry_price * (1 - self.TAKE_PROFIT_PCT)
            position_direction = "SELL"
        
        minute_results = []
        exit_reason = None
        exit_minute = None
        
        for i, (timestamp, row) in enumerate(minute_data.iterrows()):
            current_price = row['close']
            
            # Calculate P&L with quantity-based approach
            if signal_type == 1:  # Buy signal
                # P&L = (Current Price - Entry Price) * Quantity - Transaction Costs
                gross_pnl = (current_price - entry_price) * self.QUANTITY
                # Check stop loss and take profit
                if current_price <= stop_loss_price:
                    exit_reason = "Stop Loss"
                    exit_minute = i + 1
                    sell_cost = current_price * self.QUANTITY * self.TRANSACTION_COST
                    break
                elif current_price >= take_profit_price:
                    exit_reason = "Take Profit"
                    exit_minute = i + 1
                    sell_cost = current_price * self.QUANTITY * self.TRANSACTION_COST
                    break
            else:  # Sell signal
                # P&L = (Entry Price - Current Price) * Quantity - Transaction Costs
                gross_pnl = (entry_price - current_price) * self.QUANTITY
                # Check stop loss and take profit
                if current_price >= stop_loss_price:
                    exit_reason = "Stop Loss"
                    exit_minute = i + 1
                    sell_cost = current_price * self.QUANTITY * self.TRANSACTION_COST
                    break
                elif current_price <= take_profit_price:
                    exit_reason = "Take Profit"
                    exit_minute = i + 1
                    sell_cost = current_price * self.QUANTITY * self.TRANSACTION_COST
                    break
            
            # Net P&L includes transaction costs
            net_pnl = gross_pnl - buy_cost
            pnl_pct = (gross_pnl / (entry_price * self.QUANTITY)) * 100 if entry_price > 0 else 0
            
            # Track profitability
            if gross_pnl > 0:
                max_profit = max(max_profit, gross_pnl)
                total_profitable_minutes += 1
                if profit_duration == 0:
                    profit_duration = i + 1
            else:
                max_loss = min(max_loss, gross_pnl)
                total_loss_minutes += 1
                if loss_duration == 0:
                    loss_duration = i + 1
            
            minute_results.append({
                'minute': i + 1,
                'timestamp': timestamp,
                'price': current_price,
                'gross_pnl': gross_pnl,
                'net_pnl': net_pnl,
                'pnl_pct': pnl_pct,
                'cumulative_profit_minutes': total_profitable_minutes,
                'cumulative_loss_minutes': total_loss_minutes
            })
        
        # Calculate final metrics
        if minute_results:
            final_price = minute_results[-1]['price']
            final_gross_pnl = minute_results[-1]['gross_pnl']
            
            # If exited due to stop loss or take profit, use that exit price
            if exit_reason:
                if signal_type == 1:
                    final_price = stop_loss_price if exit_reason == "Stop Loss" else take_profit_price
                else:
                    final_price = stop_loss_price if exit_reason == "Stop Loss" else take_profit_price
                
                if signal_type == 1:
                    final_gross_pnl = (final_price - entry_price) * self.QUANTITY
                else:
                    final_gross_pnl = (entry_price - final_price) * self.QUANTITY
            
            # Add sell transaction cost if position was closed
            total_transaction_cost = buy_cost + (sell_cost if exit_reason else final_price * self.QUANTITY * self.TRANSACTION_COST)
            final_net_pnl = final_gross_pnl - total_transaction_cost
            final_pnl_pct = (final_gross_pnl / (entry_price * self.QUANTITY)) * 100 if entry_price > 0 else 0
        else:
            final_price = entry_price
            final_gross_pnl = 0
            final_net_pnl = -buy_cost  # Only entry transaction cost
            final_pnl_pct = 0
            total_transaction_cost = buy_cost
        
        return {
            'signal_time': signal_time,
            'adjusted_signal_time': adjusted_signal_time,
            'signal_type': position_direction,
            'entry_price': entry_price,
            'exit_price': final_price,
            'quantity': self.QUANTITY,
            'gross_pnl': final_gross_pnl,
            'net_pnl': final_net_pnl,
            'transaction_costs': total_transaction_cost,
            'pnl_percentage': final_pnl_pct,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'total_profitable_minutes': total_profitable_minutes,
            'total_loss_minutes': total_loss_minutes,
            'profit_start_minute': profit_duration if profit_duration > 0 else None,
            'loss_start_minute': loss_duration if loss_duration > 0 else None,
            'exit_reason': exit_reason,
            'exit_minute': exit_minute,
            'minute_by_minute': minute_results,
            'total_minutes_analyzed': len(minute_results)
        }
    
    def analyze_pattern(self, pattern_id: int, signals_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze a specific pattern's performance with position tracking"""
        pattern_col = f'pattern_{pattern_id}'
        pattern_name = self.PATTERN_NAMES[pattern_id]
        
        print(f"\n🔍 Analyzing Pattern {pattern_id}: {pattern_name}")
        
        # Get all signals for this pattern
        pattern_signals = signals_df[signals_df[pattern_col] != 0].copy()
        
        if pattern_signals.empty:
            print(f"⚠️  No signals found for pattern {pattern_id}")
            return {
                'pattern_id': pattern_id,
                'pattern_name': pattern_name,
                'total_signals': 0,
                'trades': []
            }
        
        print(f"📊 Found {len(pattern_signals)} signals for pattern {pattern_id}")
        
        trades = []
        buy_signals = 0
        sell_signals = 0
        skipped_signals = 0
        
        # Position tracking variables
        active_position = None  # None, 'LONG', or 'SHORT'
        position_exit_time = None
        
        for idx, row in pattern_signals.iterrows():
            signal_type = row[pattern_col]
            signal_time = row['datetime']
            entry_price = row['close']
            
            # Check if we have an active position that hasn't expired yet
            if active_position is not None and position_exit_time is not None:
                if signal_time < position_exit_time:
                    # Position is still active, skip this signal
                    skipped_signals += 1
                    print(f"⏭️  Skipping signal at {signal_time} - {active_position} position still active until {position_exit_time}")
                    continue
                else:
                    # Position has expired, clear it
                    active_position = None
                    position_exit_time = None
            
            if signal_type == 1:
                buy_signals += 1
            elif signal_type == -1:
                sell_signals += 1
            
            # Analyze this signal
            analysis = self.analyze_signal_accuracy(signal_time, signal_type, entry_price)
            
            if analysis:
                analysis['pattern_id'] = pattern_id
                analysis['pattern_name'] = pattern_name
                trades.append(analysis)
                
                # Update position tracking
                if signal_type == 1:
                    active_position = 'LONG'
                elif signal_type == -1:
                    active_position = 'SHORT'
                
                # Calculate position exit time based on the analysis
                adjusted_signal_time = analysis['adjusted_signal_time']
                if analysis['exit_reason'] and analysis['exit_minute']:
                    # Position exited early due to stop loss or take profit
                    position_exit_time = adjusted_signal_time + timedelta(minutes=analysis['exit_minute'])
                else:
                    # Position held for maximum duration
                    position_exit_time = adjusted_signal_time + timedelta(minutes=self.MAX_HOLDING_MINUTES)
        
        print(f"✅ Analyzed {len(trades)} trades for pattern {pattern_id} ({buy_signals} buys, {sell_signals} sells, {skipped_signals} skipped)")
        
        # Calculate pattern statistics
        if trades:
            profitable_trades = [t for t in trades if t['net_pnl'] > 0]
            losing_trades = [t for t in trades if t['net_pnl'] <= 0]
            
            win_rate = len(profitable_trades) / len(trades) * 100
            avg_profit = np.mean([t['net_pnl'] for t in profitable_trades]) if profitable_trades else 0
            avg_loss = np.mean([t['net_pnl'] for t in losing_trades]) if losing_trades else 0
            avg_profit_duration = np.mean([t['total_profitable_minutes'] for t in trades])
            avg_loss_duration = np.mean([t['total_loss_minutes'] for t in trades])
            total_pnl = sum([t['net_pnl'] for t in trades])
            total_gross_pnl = sum([t['gross_pnl'] for t in trades])
            total_transaction_costs = sum([t['transaction_costs'] for t in trades])
            
            pattern_stats = {
                'pattern_id': pattern_id,
                'pattern_name': pattern_name,
                'total_signals': len(pattern_signals),
                'analyzed_trades': len(trades),
                'skipped_signals': skipped_signals,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'profitable_trades': len(profitable_trades),
                'losing_trades': len(losing_trades),
                'win_rate': win_rate,
                'avg_profit': avg_profit,
                'avg_loss': avg_loss,
                'avg_profitable_minutes': avg_profit_duration,
                'avg_loss_minutes': avg_loss_duration,
                'total_net_pnl': total_pnl,
                'total_gross_pnl': total_gross_pnl,
                'total_transaction_costs': total_transaction_costs,
                'max_single_profit': max([t['max_profit'] for t in trades]) if trades else 0,
                'max_single_loss': min([t['max_loss'] for t in trades]) if trades else 0,
                'trades': trades
            }
        else:
            pattern_stats = {
                'pattern_id': pattern_id,
                'pattern_name': pattern_name,
                'total_signals': len(pattern_signals),
                'analyzed_trades': 0,
                'skipped_signals': skipped_signals,
                'trades': []
            }
        
        return pattern_stats
    
    def run_comprehensive_backtest(self) -> Dict[str, Any]:
        """Run backtest for all patterns"""
        print("🚀 Starting Comprehensive Ichimoku-ADX Backtest")
        print("=" * 60)
        print(f"📅 Period: {self.START_DATE} to {self.END_DATE}")
        print(f"⏱️  Timeframe: {self.TIMEFRAME}")
        print(f"💰 Capital: ₹{self.INITIAL_CAPITAL:,}")
        print(f"� Quantity per Trade: {self.QUANTITY} unit(s)")
        print(f"📈 Symbol: {self.SYMBOL}")
        print(f"🔴 Stop Loss: {self.STOP_LOSS_PCT*100}%")
        print(f"🟢 Take Profit: {self.TAKE_PROFIT_PCT*100}%")
        print(f"� Transaction Cost: {self.TRANSACTION_COST*100}%")
        
        # Load signals
        signals_df = self.load_signals()
        
        # Analyze each pattern
        all_pattern_results = {}
        all_trades = []
        
        for pattern_id in range(10):  # Patterns 0-9
            pattern_results = self.analyze_pattern(pattern_id, signals_df)
            all_pattern_results[pattern_id] = pattern_results
            all_trades.extend(pattern_results['trades'])
        
        # Calculate overall statistics
        if all_trades:
            total_profitable = len([t for t in all_trades if t['net_pnl'] > 0])
            total_trades = len(all_trades)
            overall_win_rate = total_profitable / total_trades * 100
            overall_net_pnl = sum([t['net_pnl'] for t in all_trades])
            overall_gross_pnl = sum([t['gross_pnl'] for t in all_trades])
            overall_transaction_costs = sum([t['transaction_costs'] for t in all_trades])
            total_skipped_signals = sum([pattern_results.get('skipped_signals', 0) for pattern_results in all_pattern_results.values()])
            
            overall_stats = {
                'total_trades': total_trades,
                'profitable_trades': total_profitable,
                'losing_trades': total_trades - total_profitable,
                'overall_win_rate': overall_win_rate,
                'total_net_pnl': overall_net_pnl,
                'total_gross_pnl': overall_gross_pnl,
                'total_transaction_costs': overall_transaction_costs,
                'total_skipped_signals': total_skipped_signals,
                'avg_trade_duration': np.mean([len(t['minute_by_minute']) for t in all_trades]),
                'total_quantity_traded': total_trades * self.QUANTITY
            }
        else:
            overall_stats = {
                'total_trades': 0,
                'profitable_trades': 0,
                'losing_trades': 0,
                'overall_win_rate': 0,
                'total_net_pnl': 0,
                'total_gross_pnl': 0,
                'total_transaction_costs': 0,
                'total_skipped_signals': 0,
                'total_quantity_traded': 0
            }
        
        results = {
            'config': {
                'timeframe': self.TIMEFRAME,
                'start_date': self.START_DATE,
                'end_date': self.END_DATE,
                'symbol': self.SYMBOL,
                'initial_capital': self.INITIAL_CAPITAL,
                'position_size': self.POSITION_SIZE
            },
            'overall_stats': overall_stats,
            'pattern_results': all_pattern_results,
            'all_trades': all_trades
        }
        
        self.results = results
        return results
    
    def print_summary(self):
        """Print simple summary of backtest results"""
        if not self.results:
            print("❌ No results to display. Run backtest first.")
            return
        
        print("=" * 80)
        print("📊 BACKTEST RESULTS SUMMARY")
        print("=" * 80)
        
        # Overall stats
        overall = self.results['overall_stats']
        print(f"\n🎯 OVERALL PERFORMANCE:")
        print(f"   Total Trades: {overall['total_trades']}")
        print(f"   Profitable Trades: {overall['profitable_trades']}")
        print(f"   Losing Trades: {overall['losing_trades']}")
        print(f"   Skipped Signals: {overall.get('total_skipped_signals', 0)}")
        print(f"   Win Rate: {overall['overall_win_rate']:.2f}%")
        print(f"   Total Net P&L: ₹{overall['total_net_pnl']:,.2f}")
        
        # Pattern breakdown
        print(f"\n📈 PATTERN RESULTS:")
        print("-" * 95)
        print(f"{'Pattern':<8} {'Name':<35} {'Trades':<8} {'Skipped':<8} {'Win%':<8} {'Net P&L':<15}")
        print("-" * 95)
        
        patterns_with_trades = []
        for pattern_id, pattern_data in self.results['pattern_results'].items():
            if pattern_data.get('analyzed_trades', 0) > 0:
                patterns_with_trades.append((pattern_id, pattern_data))
                
                name = pattern_data['pattern_name'][:33]
                trades = pattern_data['analyzed_trades']
                skipped = pattern_data.get('skipped_signals', 0)
                win_rate = pattern_data['win_rate']
                pnl = pattern_data['total_net_pnl']
                
                print(f"{pattern_id:<8} {name:<35} {trades:<8} {skipped:<8} {win_rate:<8.1f} ₹{pnl:<14,.2f}")
        
        # Top patterns
        if patterns_with_trades:
            sorted_patterns = sorted(patterns_with_trades, key=lambda x: x[1]['total_net_pnl'], reverse=True)
            print(f"\n🏆 TOP 5 PATTERNS BY P&L:")
            for i, (pattern_id, data) in enumerate(sorted_patterns[:5]):
                print(f"   {i+1}. Pattern {pattern_id}: {data['pattern_name']} - ₹{data['total_net_pnl']:,.2f}")
        
        print(f"\n⏰ Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
    
    def save_results(self, output_dir: str = None):
        """Save pattern-wise PnL CSV files"""
        if not self.results:
            print("❌ No results to save. Run backtest first.")
            return
        
        if output_dir is None:
            # Create named folder structure: results/backtest_name/
            base_dir = self.OUTPUT_DIR
            backtest_folder = os.path.join(base_dir, self.BACKTEST_NAME)
            output_dir = backtest_folder
        
        os.makedirs(output_dir, exist_ok=True)
        
        print("💾 Saving pattern-wise PnL results...")
        
        # Save configuration for reference
        config_info = {
            'backtest_name': self.BACKTEST_NAME,
            'timeframe': self.TIMEFRAME,
            'csv_path': self.CSV_PATH,
            'start_date': self.START_DATE,
            'end_date': self.END_DATE,
            'symbol': self.SYMBOL,
            'quantity_per_trade': self.QUANTITY,
            'stop_loss_pct': self.STOP_LOSS_PCT,
            'take_profit_pct': self.TAKE_PROFIT_PCT,
            'max_holding_minutes': self.MAX_HOLDING_MINUTES,
            'transaction_cost_pct': self.TRANSACTION_COST,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        config_df = pd.DataFrame([config_info])
        config_path = os.path.join(output_dir, 'backtest_config.csv')
        config_df.to_csv(config_path, index=False)
        print(f"💾 Saved backtest configuration to {config_path}")
        
        # Create pattern-wise PnL CSV files
        saved_files = []
        
        for pattern_id, pattern_data in self.results['pattern_results'].items():
            if pattern_data.get('trades', []):
                trades = pattern_data['trades']
                pattern_name = pattern_data['pattern_name']
                
                # Create clean PnL DataFrame
                pnl_data = []
                for trade in trades:
                    pnl_data.append({
                        'signal_time': trade['signal_time'],
                        'position_entry_time': trade['adjusted_signal_time'],
                        'position_exit_time': trade['adjusted_signal_time'] + timedelta(minutes=trade['total_minutes_analyzed']),
                        'signal_type': trade['signal_type'],
                        'buy_price': trade['entry_price'],
                        'sell_price': trade['exit_price'],
                        'quantity': trade['quantity'],
                        'gross_pnl': trade['gross_pnl'],
                        'net_pnl': trade['net_pnl'],
                        'transaction_costs': trade['transaction_costs'],
                        'exit_reason': trade['exit_reason'] or 'Timeout',
                        'holding_minutes': trade['total_minutes_analyzed']
                    })
                
                pnl_df = pd.DataFrame(pnl_data)
                
                # Sort by signal time
                pnl_df = pnl_df.sort_values('signal_time').reset_index(drop=True)
                
                # Save pattern-specific CSV
                pattern_filename = f"pattern_{pattern_id}_{pattern_name.replace(' ', '_').replace('/', '_')}_pnl.csv"
                pattern_path = os.path.join(output_dir, pattern_filename)
                pnl_df.to_csv(pattern_path, index=False)
                
                saved_files.append(pattern_path)
                print(f"💾 Saved Pattern {pattern_id} PnL ({len(pnl_df)} trades) to {pattern_filename}")
        
        # Create a summary of all patterns
        summary_data = []
        total_trades = 0
        total_pnl = 0
        
        for pattern_id, pattern_data in self.results['pattern_results'].items():
            trades = pattern_data.get('trades', [])
            if trades:
                pattern_pnl = sum([t['net_pnl'] for t in trades])
                profitable_trades = len([t for t in trades if t['net_pnl'] > 0])
                win_rate = (profitable_trades / len(trades)) * 100 if trades else 0
                
                summary_data.append({
                    'pattern_id': pattern_id,
                    'pattern_name': pattern_data['pattern_name'],
                    'total_trades': len(trades),
                    'profitable_trades': profitable_trades,
                    'win_rate_pct': round(win_rate, 2),
                    'total_net_pnl': round(pattern_pnl, 2),
                    'skipped_signals': pattern_data.get('skipped_signals', 0)
                })
                
                total_trades += len(trades)
                total_pnl += pattern_pnl
        
        # Save summary
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            summary_df = summary_df.sort_values('total_net_pnl', ascending=False).reset_index(drop=True)
            summary_path = os.path.join(output_dir, 'patterns_summary.csv')
            summary_df.to_csv(summary_path, index=False)
            print(f"💾 Saved patterns summary to patterns_summary.csv")
            
            # Print summary
            print(f"\n📊 BACKTEST SUMMARY:")
            print(f"   Total Patterns with Trades: {len(summary_data)}")
            print(f"   Total Trades: {total_trades}")
            print(f"   Total Net P&L: ₹{total_pnl:,.2f}")
            print(f"\n🏆 TOP 3 PATTERNS:")
            for i, row in summary_df.head(3).iterrows():
                print(f"   {i+1}. Pattern {row['pattern_id']}: {row['pattern_name']} - ₹{row['total_net_pnl']:,.2f} ({row['total_trades']} trades)")
        
        return output_dir
        if self.results['all_trades']:
            trades_data = []
            for trade in self.results['all_trades']:
                trades_data.append({
                    'pattern_id': trade['pattern_id'],
                    'pattern_name': trade['pattern_name'],
                    'signal_time': trade['signal_time'],
                    'signal_type': trade['signal_type'],
                    'entry_price': trade['entry_price'],
                    'exit_price': trade['exit_price'],
                    'quantity': trade['quantity'],
                    'gross_pnl': trade['gross_pnl'],
                    'net_pnl': trade['net_pnl'],
                    'transaction_costs': trade['transaction_costs'],
                    'pnl_percentage': trade['pnl_percentage'],
                    'max_profit': trade['max_profit'],
                    'max_loss': trade['max_loss'],
                    'total_profitable_minutes': trade['total_profitable_minutes'],
                    'total_loss_minutes': trade['total_loss_minutes'],
                    'exit_reason': trade['exit_reason'],
                    'total_minutes_analyzed': trade['total_minutes_analyzed']
                })
            
            trades_df = pd.DataFrame(trades_data)
            trades_path = os.path.join(output_dir, 'detailed_trades.csv')
            trades_df.to_csv(trades_path, index=False)
            print(f"💾 Saved detailed trades to {trades_path}")
        
        # Save summary text
        summary_text_path = self.save_summary_text(output_dir)
        
        # Save comprehensive pattern metrics with individual capital allocation
        pattern_capital = 100000  # ₹1 lakh per pattern
        metrics_path, summary_path, metrics_df = self.save_pattern_metrics_csv(output_dir, pattern_capital)
        
        # Create visualizations
        try:
            equity_path = self.create_equity_curves(output_dir)
            dashboard_path = self.create_performance_dashboard(output_dir)
            
            print(f"📊 Created visualizations:")
            if isinstance(equity_path, list):
                for path in equity_path:
                    print(f"   - Equity curve: {path}")
            else:
                print(f"   - Equity curves: {equity_path}")
            print(f"   - Performance dashboard: {dashboard_path}")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not create visualizations: {e}")
            print("   Data files were saved successfully.")
        
        # Save advanced metrics as CSV instead of JSON
        if self.results['all_trades']:
            overall_metrics = self.calculate_financial_metrics(self.results['all_trades'])
            
            # Create overall metrics CSV
            overall_data = {
                'metric': [],
                'value': [],
                'description': []
            }
            
            metric_descriptions = {
                'total_trades': 'Total number of trades executed',
                'profitable_trades': 'Number of profitable trades',
                'win_rate': 'Percentage of profitable trades',
                'total_pnl': 'Total profit and loss amount',
                'avg_trade': 'Average profit/loss per trade',
                'max_trade': 'Best single trade result',
                'min_trade': 'Worst single trade result',
                'std_returns': 'Standard deviation of returns',
                'sharpe_ratio': 'Risk-adjusted return measure',
                'max_drawdown': 'Largest peak-to-trough decline',
                'max_drawdown_pct': 'Maximum drawdown as percentage',
                'profit_factor': 'Gross profit / Gross loss',
                'recovery_factor': 'Total P&L / Maximum drawdown',
                'sortino_ratio': 'Downside risk-adjusted return'
            }
            
            for key, value in overall_metrics.items():
                if key not in ['dates', 'cumulative_returns'] and key in metric_descriptions:
                    overall_data['metric'].append(key)
                    if isinstance(value, (np.integer, np.floating)):
                        overall_data['value'].append(float(value))
                    else:
                        overall_data['value'].append(value)
                    overall_data['description'].append(metric_descriptions[key])
            
            overall_df = pd.DataFrame(overall_data)
            overall_metrics_path = os.path.join(output_dir, 'overall_metrics.csv')
            overall_df.to_csv(overall_metrics_path, index=False)
            print(f"💾 Saved overall metrics to {overall_metrics_path}")
        
        # Save pattern-wise metrics to CSV
        try:
            pattern_metrics_path, pattern_summary_path, _ = self.save_pattern_metrics_csv(output_dir)
            print(f"💾 Saved pattern-wise metrics to {pattern_metrics_path} and summary to {pattern_summary_path}")
        except Exception as e:
            print(f"⚠️  Warning: Could not save pattern-wise metrics: {e}")
        
        return output_dir

# End of IchimokuADXBacktester class
        """Calculate advanced financial metrics for a set of trades"""
        if not trades:
            return {}
        
        # Extract trade P&Ls and dates
        returns = [trade['net_pnl'] for trade in trades]
        dates = [trade['signal_time'] for trade in trades]
        
        # Convert to pandas Series for easier calculation
        returns_series = pd.Series(returns, index=pd.to_datetime(dates))
        returns_series = returns_series.sort_index()
        
        # Calculate cumulative returns
        cumulative_returns = returns_series.cumsum()
        
        # Calculate percentage returns
        if len(trades) > 0:
            initial_value = self.INITIAL_CAPITAL
            pct_returns = [(ret / initial_value) * 100 for ret in returns]
            pct_returns_series = pd.Series(pct_returns, index=returns_series.index)
        else:
            pct_returns = []
            pct_returns_series = pd.Series([])
        
        # Basic metrics
        total_trades = len(trades)
        profitable_trades = len([t for t in trades if t['net_pnl'] > 0])
        win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
        
        # P&L metrics
        total_pnl = sum(returns)
        avg_trade = np.mean(returns) if returns else 0
        max_trade = max(returns) if returns else 0
        min_trade = min(returns) if returns else 0
        
        # Risk metrics
        std_returns = np.std(returns) if len(returns) > 1 else 0
        
        # Sharpe ratio (assuming risk-free rate of 6% annually, adjusted for trade frequency)
        risk_free_rate = 0.06
        if len(returns) > 1 and std_returns > 0:
            # Estimate trading frequency (trades per year)
            if len(dates) > 1:
                time_span = (max(dates) - min(dates)).days / 365.25
                trades_per_year = len(returns) / time_span if time_span > 0 else len(returns)
            else:
                trades_per_year = 252  # Default assumption
            
            # Convert risk-free rate to per-trade basis
            risk_free_per_trade = (risk_free_rate / trades_per_year) * initial_value
            excess_return = avg_trade - risk_free_per_trade
            sharpe_ratio = excess_return / std_returns
        else:
            sharpe_ratio = 0
        
        # Maximum Drawdown
        if len(cumulative_returns) > 0:
            running_max = cumulative_returns.expanding().max()
            drawdown = cumulative_returns - running_max
            max_drawdown = drawdown.min()
            max_drawdown_pct = (max_drawdown / initial_value * 100) if initial_value > 0 else 0
        else:
            max_drawdown = 0
            max_drawdown_pct = 0
        
        # Profit Factor
        gross_profit = sum([ret for ret in returns if ret > 0])
        gross_loss = abs(sum([ret for ret in returns if ret < 0]))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0
        
        # Recovery Factor
        recovery_factor = abs(total_pnl / max_drawdown) if max_drawdown != 0 else 0
        
        # Sortino Ratio (using downside deviation)
        negative_returns = [ret for ret in returns if ret < 0]
        downside_std = np.std(negative_returns) if len(negative_returns) > 1 else 0
        if downside_std > 0:
            sortino_ratio = excess_return / downside_std
        else:
            sortino_ratio = 0
        
        return {
            'total_trades': total_trades,
            'profitable_trades': profitable_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_trade': avg_trade,
            'max_trade': max_trade,
            'min_trade': min_trade,
            'std_returns': std_returns,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown_pct,
            'profit_factor': profit_factor,
            'recovery_factor': recovery_factor,
            'sortino_ratio': sortino_ratio,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'cumulative_returns': cumulative_returns.tolist() if len(cumulative_returns) > 0 else [],
            'dates': [d.strftime('%Y-%m-%d %H:%M:%S') for d in cumulative_returns.index] if len(cumulative_returns) > 0 else []
        }
    
    def calculate_pattern_metrics_with_capital(self, pattern_capital: float = 100000) -> pd.DataFrame:
        """
        Calculate detailed metrics for each pattern assuming individual capital allocation
        
        Args:
            pattern_capital: Capital allocated to each pattern individually (default: ₹100,000)
        
        Returns:
            DataFrame with comprehensive pattern-wise metrics
        """
        print(f"📊 Calculating pattern metrics with ₹{pattern_capital:,} capital per pattern...")
        
        pattern_metrics = []
        
        for pattern_id, pattern_data in self.results['pattern_results'].items():
            if pattern_data.get('analyzed_trades', 0) > 0:
                trades = pattern_data['trades']
                
                # Basic metrics
                total_trades = len(trades)
                profitable_trades = len([t for t in trades if t['net_pnl'] > 0])
                losing_trades = total_trades - profitable_trades
                win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
                
                # P&L metrics (actual trade results)
                total_gross_pnl = sum([t['gross_pnl'] for t in trades])
                total_net_pnl = sum([t['net_pnl'] for t in trades])
                avg_trade_pnl = total_net_pnl / total_trades if total_trades > 0 else 0
                
                # Best and worst trades
                best_trade = max([t['net_pnl'] for t in trades]) if trades else 0
                worst_trade = min([t['net_pnl'] for t in trades]) if trades else 0
                
                # Calculate percentage returns based on allocated capital
                total_return_pct = (total_net_pnl / pattern_capital) * 100
                avg_trade_return_pct = (avg_trade_pnl / pattern_capital) * 100
                best_trade_pct = (best_trade / pattern_capital) * 100
                worst_trade_pct = (worst_trade / pattern_capital) * 100
                
                # Profit and loss analysis
                profit_trades = [t['net_pnl'] for t in trades if t['net_pnl'] > 0]
                loss_trades = [t['net_pnl'] for t in trades if t['net_pnl'] <= 0]
                
                avg_profit = np.mean(profit_trades) if profit_trades else 0
                avg_loss = np.mean(loss_trades) if loss_trades else 0
                avg_profit_pct = (avg_profit / pattern_capital) * 100 if avg_profit > 0 else 0
                avg_loss_pct = (avg_loss / pattern_capital) * 100 if avg_loss < 0 else 0
                
                # Risk metrics
                returns_list = [t['net_pnl'] for t in trades]
                std_returns = np.std(returns_list) if len(returns_list) > 1 else 0
                
                # Calculate returns as percentage of allocated capital for risk metrics
                pct_returns_list = [(ret / pattern_capital) * 100 for ret in returns_list]
                
                # Sharpe ratio calculation
                if len(pct_returns_list) > 1 and std_returns > 0:
                    # Estimate annual risk-free rate (6%) adjusted for trading frequency
                    risk_free_annual = 6.0  # 6% annually
                    
                    # Get trading timespan
                    dates = [trade['signal_time'] for trade in trades]
                    if len(dates) > 1:
                        time_span_days = (max(dates) - min(dates)).days
                        trades_per_year = (total_trades / time_span_days) * 365.25 if time_span_days > 0 else total_trades
                    else:
                        trades_per_year = 252  # Default assumption
                    
                    # Risk-free return per trade as percentage of capital
                    risk_free_per_trade_pct = (risk_free_annual / trades_per_year)
                    excess_return_pct = avg_trade_return_pct - risk_free_per_trade_pct
                    
                    # Convert std_returns to percentage terms
                    std_returns_pct = (std_returns / pattern_capital) * 100
                    sharpe_ratio = excess_return_pct / std_returns_pct if std_returns_pct > 0 else 0
                else:
                    sharpe_ratio = 0
                
                # Maximum Drawdown calculation
                if len(returns_list) > 0:
                    cumulative_returns = np.cumsum(returns_list)
                    running_max = np.maximum.accumulate(cumulative_returns)
                    drawdown = cumulative_returns - running_max
                    max_drawdown = np.min(drawdown)
                    max_drawdown_pct = (max_drawdown / pattern_capital) * 100
                else:
                    max_drawdown = 0
                    max_drawdown_pct = 0
                
                # Profit Factor
                gross_profit = sum([ret for ret in returns_list if ret > 0])
                gross_loss = abs(sum([ret for ret in returns_list if ret < 0]))
                profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0
                
                # Recovery Factor
                recovery_factor = abs(total_net_pnl / max_drawdown) if max_drawdown != 0 else 0
                
                # Sortino Ratio (downside deviation)
                negative_returns = [ret for ret in returns_list if ret < 0]
                downside_std = np.std(negative_returns) if len(negative_returns) > 1 else 0
                downside_std_pct = (downside_std / pattern_capital) * 100 if downside_std > 0 else 0
                
                if downside_std_pct > 0:
                    sortino_ratio = excess_return_pct / downside_std_pct
                else:
                    sortino_ratio = 0
                
                # Trade frequency analysis
                if len(dates) > 1:
                    time_span_days = (max(dates) - min(dates)).days
                    trades_per_month = (total_trades / time_span_days) * 30.44 if time_span_days > 0 else 0
                else:
                    trades_per_month = 0
                
                # Calmar Ratio (Annual Return / Max Drawdown)
                if len(dates) > 1 and max_drawdown_pct < 0:
                    time_span_years = time_span_days / 365.25 if time_span_days > 0 else 1
                    annualized_return = (total_return_pct / time_span_years)
                    calmar_ratio = annualized_return / abs(max_drawdown_pct)
                else:
                    calmar_ratio = 0
                    annualized_return = 0
                
                # Compile all metrics
                pattern_metrics.append({
                    'pattern_id': pattern_id,
                    'pattern_name': pattern_data['pattern_name'],
                    'allocated_capital': pattern_capital,
                    
                    # Trade Statistics
                    'total_signals': pattern_data['total_signals'],
                    'total_trades': total_trades,
                    'skipped_signals': pattern_data.get('skipped_signals', 0),
                    'buy_signals': pattern_data['buy_signals'],
                    'sell_signals': pattern_data['sell_signals'],
                    'profitable_trades': profitable_trades,
                    'losing_trades': losing_trades,
                    'win_rate_pct': round(win_rate, 2),
                    
                    # P&L Metrics (Actual Amounts)
                    'total_gross_pnl': round(total_gross_pnl, 2),
                    'total_net_pnl': round(total_net_pnl, 2),
                    'avg_trade_pnl': round(avg_trade_pnl, 2),
                    'best_trade_pnl': round(best_trade, 2),
                    'worst_trade_pnl': round(worst_trade, 2),
                    'avg_profit_pnl': round(avg_profit, 2),
                    'avg_loss_pnl': round(avg_loss, 2),
                    
                    # Return Metrics (Percentage of Allocated Capital)
                    'total_return_pct': round(total_return_pct, 4),
                    'avg_trade_return_pct': round(avg_trade_return_pct, 4),
                    'best_trade_return_pct': round(best_trade_pct, 4),
                    'worst_trade_return_pct': round(worst_trade_pct, 4),
                    'avg_profit_return_pct': round(avg_profit_pct, 4),
                    'avg_loss_return_pct': round(avg_loss_pct, 4),
                    'annualized_return_pct': round(annualized_return, 2),
                    
                    # Risk Metrics
                    'volatility_pct': round(std_returns_pct, 4) if 'std_returns_pct' in locals() else 0,
                    'max_drawdown_pnl': round(max_drawdown, 2),
                    'max_drawdown_pct': round(max_drawdown_pct, 4),
                    'sharpe_ratio': round(sharpe_ratio, 4),
                    'sortino_ratio': round(sortino_ratio, 4),
                    'calmar_ratio': round(calmar_ratio, 4),
                    'profit_factor': round(profit_factor, 2),
                    'recovery_factor': round(recovery_factor, 2),
                    
                    # Trading Activity
                    'trades_per_month': round(trades_per_month, 2),
                    'avg_holding_minutes': round(np.mean([len(t['minute_by_minute']) for t in trades]), 1) if trades else 0,
                    
                    # Performance Score (Custom metric combining multiple factors)
                    'performance_score': round(
                        (win_rate * 0.3) + 
                        (total_return_pct * 0.4) + 
                        (sharpe_ratio * 10 * 0.2) + 
                        (profit_factor * 10 * 0.1), 2
                    )
                })
        
        # Convert to DataFrame and sort by performance score
        df = pd.DataFrame(pattern_metrics)
        df = df.sort_values('performance_score', ascending=False).reset_index(drop=True)
        return df
    
    def save_pattern_metrics_csv(self, output_dir: str, pattern_capital: float = 100000):
        """Save comprehensive pattern metrics to CSV"""
        
        # Calculate pattern metrics
        metrics_df = self.calculate_pattern_metrics_with_capital(pattern_capital)
        
        # Save to CSV
        metrics_path = os.path.join(output_dir, 'pattern_wise_metrics.csv')
        metrics_df.to_csv(metrics_path, index=False)
        
        # Also create a summary table with key metrics only
        summary_columns = [
            'pattern_id', 'pattern_name', 'total_trades', 'skipped_signals', 'win_rate_pct',
            'total_net_pnl', 'total_return_pct', 'max_drawdown_pct',
            'sharpe_ratio', 'profit_factor', 'performance_score'
        ]
        
        summary_df = metrics_df[summary_columns].copy()
        summary_path = os.path.join(output_dir, 'pattern_summary_metrics.csv')
        summary_df.to_csv(summary_path, index=False)
        
        print(f"💾 Saved pattern metrics to {metrics_path}")
        print(f"💾 Saved pattern summary metrics to {summary_path}")
        
        # Print top 5 patterns
        print(f"\n🏆 TOP 5 PATTERNS BY PERFORMANCE SCORE:")
        print("-" * 115)
        print(f"{'Rank':<4} {'Pattern':<8} {'Name':<30} {'Trades':<7} {'Skipped':<8} {'Win%':<6} {'Return%':<8} {'Score':<6}")
        print("-" * 115)
        
        for i, row in summary_df.head(5).iterrows():
            print(f"{i+1:<4} {row['pattern_id']:<8} {row['pattern_name'][:28]:<30} "
                  f"{row['total_trades']:<7} {row['skipped_signals']:<8} {row['win_rate_pct']:<6.1f} {row['total_return_pct']:<8.2f} {row['performance_score']:<6.1f}")
        
        return metrics_path, summary_path, metrics_df
    
    def create_equity_curves(self, output_dir: str):
        """Create equity curve visualizations for all patterns"""
        print("📊 Creating equity curve visualizations...")
        
        # Create figure with subplots - split into two separate figures to avoid overcrowding
        
        # Figure 1: Overall equity curve and top 5 patterns
        fig1 = plt.figure(figsize=(16, 12))
        
        # Overall equity curve (top plot, spans full width)
        ax1 = plt.subplot(3, 2, (1, 2))
        
        # Combine all trades and sort by time
        all_trades_sorted = sorted(self.results['all_trades'], key=lambda x: x['signal_time'])
        if all_trades_sorted:
            cumulative_pnl = []
            dates = []
            running_total = 0
            
            for trade in all_trades_sorted:
                running_total += trade['net_pnl']
                cumulative_pnl.append(running_total)
                dates.append(trade['signal_time'])
            
            ax1.plot(dates, cumulative_pnl, linewidth=3, color='darkblue', label='Overall Strategy')
            ax1.axhline(y=0, color='red', linestyle='--', alpha=0.7)
            ax1.set_title('Overall Strategy Equity Curve', fontsize=16, fontweight='bold')
            ax1.set_ylabel('Cumulative P&L (₹)', fontsize=12)
            ax1.grid(True, alpha=0.3)
            ax1.legend(fontsize=12)
            
            # Format x-axis
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        # Top 5 performing patterns (by P&L)
        patterns_with_trades = [(k, v) for k, v in self.results['pattern_results'].items() 
                               if v.get('trades', [])]
        top_patterns = sorted(patterns_with_trades, key=lambda x: x[1]['total_net_pnl'], reverse=True)[:4]
        
        colors = ['#2E8B57', '#FF6347', '#4682B4', '#DAA520']  # Nice colors for top patterns
        
        for i, (pattern_id, pattern_data) in enumerate(top_patterns):
            ax = plt.subplot(3, 2, i + 3)
            
            trades = sorted(pattern_data['trades'], key=lambda x: x['signal_time'])
            cumulative_pnl = []
            dates = []
            running_total = 0
            
            for trade in trades:
                running_total += trade['net_pnl']
                cumulative_pnl.append(running_total)
                dates.append(trade['signal_time'])
            
            ax.plot(dates, cumulative_pnl, linewidth=2, color=colors[i])
            ax.axhline(y=0, color='red', linestyle='--', alpha=0.7)
            ax.set_title(f'Pattern {pattern_id}: {pattern_data["pattern_name"][:25]}', fontsize=11, fontweight='bold')
            ax.set_ylabel('P&L (₹)', fontsize=10)
            ax.grid(True, alpha=0.3)
            
            # Add performance text
            ax.text(0.02, 0.98, f'Total: ₹{pattern_data["total_net_pnl"]:,.0f}\nWin Rate: {pattern_data["win_rate"]:.1f}%', 
                   transform=ax.transAxes, fontsize=9, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            # Format x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%y'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, fontsize=9)
        
        plt.tight_layout()
        equity_path1 = os.path.join(output_dir, 'equity_curves_main.png')
        plt.savefig(equity_path1, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Figure 2: Remaining patterns
        if len(patterns_with_trades) > 4:
            fig2 = plt.figure(figsize=(16, 12))
            remaining_patterns = patterns_with_trades[4:]  # Skip the top 4 already shown
            
            # Show up to 6 more patterns
            for i, (pattern_id, pattern_data) in enumerate(remaining_patterns[:6]):
                ax = plt.subplot(3, 2, i + 1)
                
                trades = sorted(pattern_data['trades'], key=lambda x: x['signal_time'])
                cumulative_pnl = []
                dates = []
                running_total = 0
                
                for trade in trades:
                    running_total += trade['net_pnl']
                    cumulative_pnl.append(running_total)
                    dates.append(trade['signal_time'])
                
                color = plt.cm.tab10(i)
                ax.plot(dates, cumulative_pnl, linewidth=2, color=color)
                ax.axhline(y=0, color='red', linestyle='--', alpha=0.7)
                ax.set_title(f'Pattern {pattern_id}: {pattern_data["pattern_name"][:25]}', fontsize=11, fontweight='bold')
                ax.set_ylabel('P&L (₹)', fontsize=10)
                ax.grid(True, alpha=0.3)
                
                # Add performance text
                ax.text(0.02, 0.98, f'Total: ₹{pattern_data["total_net_pnl"]:,.0f}\nWin Rate: {pattern_data["win_rate"]:.1f}%', 
                       transform=ax.transAxes, fontsize=9, verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
                
                # Format x-axis
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%y'))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, fontsize=9)
            
            plt.tight_layout()
            equity_path2 = os.path.join(output_dir, 'equity_curves_additional.png')
            plt.savefig(equity_path2, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"💾 Saved equity curves to {equity_path1} and {equity_path2}")
            return [equity_path1, equity_path2]
        else:
            print(f"💾 Saved equity curves to {equity_path1}")
            return [equity_path1]
    
    def create_performance_dashboard(self, output_dir: str):
        """Create comprehensive performance dashboard"""
        print("📊 Creating performance dashboard...")
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Trading Strategy Performance Dashboard', fontsize=16, fontweight='bold')
        
        # 1. Win Rate by Pattern
        ax1 = axes[0, 0]
        patterns_with_trades = [(k, v) for k, v in self.results['pattern_results'].items() 
                               if v.get('analyzed_trades', 0) > 0]
        
        if patterns_with_trades:
            pattern_names = [f"P{k}" for k, v in patterns_with_trades]
            win_rates = [v['win_rate'] for k, v in patterns_with_trades]
            colors = plt.cm.RdYlGn(np.array(win_rates) / 100)
            
            bars = ax1.bar(pattern_names, win_rates, color=colors)
            ax1.set_title('Win Rate by Pattern (%)', fontweight='bold')
            ax1.set_ylabel('Win Rate (%)')
            ax1.axhline(y=50, color='red', linestyle='--', alpha=0.7)
            ax1.grid(True, alpha=0.3)
            
            # Add value labels on bars
            for bar, rate in zip(bars, win_rates):
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                        f'{rate:.1f}%', ha='center', va='bottom', fontsize=9)
        
        # 2. P&L by Pattern
        ax2 = axes[0, 1]
        if patterns_with_trades:
            pnl_values = [v['total_net_pnl'] for k, v in patterns_with_trades]
            colors = ['green' if pnl > 0 else 'red' for pnl in pnl_values]
            
            bars = ax2.bar(pattern_names, pnl_values, color=colors, alpha=0.7)
            ax2.set_title('Net P&L by Pattern (₹)', fontweight='bold')
            ax2.set_ylabel('Net P&L (₹)')
            ax2.axhline(y=0, color='black', linestyle='-', alpha=0.8)
            ax2.grid(True, alpha=0.3)
            
            # Add value labels on bars
            for bar, pnl in zip(bars, pnl_values):
                ax2.text(bar.get_x() + bar.get_width()/2, 
                        bar.get_height() + (max(pnl_values) * 0.01) if pnl > 0 else bar.get_height() - (max(pnl_values) * 0.01), 
                        f'₹{pnl:,.0f}', ha='center', va='bottom' if pnl > 0 else 'top', fontsize=8)
        
        # 3. Trade Distribution
        ax3 = axes[0, 2]
        if patterns_with_trades:
            trade_counts = [v['analyzed_trades'] for k, v in patterns_with_trades]
            ax3.pie(trade_counts, labels=pattern_names, autopct='%1.1f%%', startangle=90)
            ax3.set_title('Trade Distribution by Pattern', fontweight='bold')
        
        # 4. Monthly P&L
        ax4 = axes[1, 0]
        if self.results['all_trades']:
            trades_df = pd.DataFrame(self.results['all_trades'])
            trades_df['signal_time'] = pd.to_datetime(trades_df['signal_time'])
            trades_df['month'] = trades_df['signal_time'].dt.to_period('M')
            monthly_pnl = trades_df.groupby('month')['net_pnl'].sum()
            
            colors = ['green' if pnl > 0 else 'red' for pnl in monthly_pnl.values]
            ax4.bar(range(len(monthly_pnl)), monthly_pnl.values, color=colors, alpha=0.7)
            ax4.set_title('Monthly P&L', fontweight='bold')
            ax4.set_ylabel('P&L (₹)')
            ax4.axhline(y=0, color='black', linestyle='-', alpha=0.8)
            ax4.grid(True, alpha=0.3)
            
            # Set x-axis labels
            ax4.set_xticks(range(len(monthly_pnl)))
            ax4.set_xticklabels([str(m) for m in monthly_pnl.index], rotation=45)
        
        # 5. Sharpe Ratio by Pattern
        ax5 = axes[1, 1]
        if patterns_with_trades:
            sharpe_ratios = []
            for k, v in patterns_with_trades:
                metrics = self.calculate_financial_metrics(v['trades'])
                sharpe_ratios.append(metrics.get('sharpe_ratio', 0))
            
            colors = plt.cm.RdYlGn(np.array([max(0, min(2, s + 1)) / 2 for s in sharpe_ratios]))
            bars = ax5.bar(pattern_names, sharpe_ratios, color=colors)
            ax5.set_title('Sharpe Ratio by Pattern', fontweight='bold')
            ax5.set_ylabel('Sharpe Ratio')
            ax5.axhline(y=0, color='red', linestyle='--', alpha=0.7)
            ax5.grid(True, alpha=0.3)
            
            # Add value labels on bars
            for bar, ratio in zip(bars, sharpe_ratios):
                ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05 if ratio > 0 else bar.get_height() - 0.05, 
                        f'{ratio:.2f}', ha='center', va='bottom' if ratio > 0 else 'top', fontsize=9)
        
        # 6. Drawdown Analysis
        ax6 = axes[1, 2]
        if self.results['all_trades']:
            overall_metrics = self.calculate_financial_metrics(self.results['all_trades'])
            if overall_metrics.get('cumulative_returns'):
                cumulative = np.array(overall_metrics['cumulative_returns'])
                running_max = np.maximum.accumulate(cumulative)
                drawdown = cumulative - running_max
                
                dates = pd.to_datetime(overall_metrics['dates'])
                ax6.fill_between(dates, drawdown, 0, color='red', alpha=0.3)
                ax6.plot(dates, drawdown, color='red', linewidth=1)
                ax6.set_title('Strategy Drawdown', fontweight='bold')
                ax6.set_ylabel('Drawdown (₹)')
                ax6.grid(True, alpha=0.3)
                
                # Format x-axis
                ax6.xaxis.set_major_formatter(mdates.DateFormatter('%m/%y'))
                plt.setp(ax6.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        dashboard_path = os.path.join(output_dir, 'performance_dashboard.png')
        plt.savefig(dashboard_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"💾 Saved performance dashboard to {dashboard_path}")
        
        return dashboard_path

    def generate_summary_text(self) -> str:
        """Generate the complete summary text that's displayed in console"""
        if not self.results:
            return "❌ No results to display. Run backtest first."
        
        summary = StringIO()
        
        # Header
        summary.write("=" * 80 + "\n")
        summary.write("📊 COMPREHENSIVE BACKTEST RESULTS SUMMARY\n")
        summary.write("=" * 80 + "\n")
        
        # Overall performance
        overall = self.results['overall_stats']
        summary.write(f"\n🎯 OVERALL PERFORMANCE:\n")
        summary.write(f"   Total Trades: {overall['total_trades']}\n")
        summary.write(f"   Profitable Trades: {overall['profitable_trades']}\n")
        summary.write(f"   Losing Trades: {overall['losing_trades']}\n")
        summary.write(f"   Skipped Signals: {overall.get('total_skipped_signals', 0)}\n")
        summary.write(f"   Win Rate: {overall['overall_win_rate']:.2f}%\n")
        summary.write(f"   Total Quantity Traded: {overall['total_quantity_traded']} units\n")
        summary.write(f"   Total Net P&L: ₹{overall['total_net_pnl']:,.2f}\n")
        summary.write(f"   Total Gross P&L: ₹{overall['total_gross_pnl']:,.2f}\n")
        summary.write(f"   Total Transaction Costs: ₹{overall['total_transaction_costs']:,.2f}\n")
        
        # Advanced metrics
        if self.results['all_trades']:
            overall_metrics = self.calculate_financial_metrics(self.results['all_trades'])
            summary.write(f"\n📈 ADVANCED METRICS:\n")
            summary.write(f"   Average Trade: ₹{overall_metrics['avg_trade']:,.2f}\n")
            summary.write(f"   Best Trade: ₹{overall_metrics['max_trade']:,.2f}\n")
            summary.write(f"   Worst Trade: ₹{overall_metrics['min_trade']:,.2f}\n")
            summary.write(f"   Sharpe Ratio: {overall_metrics['sharpe_ratio']:.3f}\n")
            summary.write(f"   Sortino Ratio: {overall_metrics['sortino_ratio']:.3f}\n")
            summary.write(f"   Profit Factor: {overall_metrics['profit_factor']:.2f}\n")
            summary.write(f"   Maximum Drawdown: ₹{overall_metrics['max_drawdown']:,.2f} ({overall_metrics['max_drawdown_pct']:.2f}%)\n")
            summary.write(f"   Recovery Factor: {overall_metrics['recovery_factor']:.2f}\n")
        
        # Pattern breakdown
        summary.write(f"\n📈 PATTERN BREAKDOWN:\n")
        summary.write("-" * 105 + "\n")
        summary.write(f"{'Pattern':<5} {'Name':<30} {'Signals':<8} {'Trades':<7} {'Skipped':<8} {'Win%':<6} {'Net P&L':<12} {'Sharpe':<8}\n")
        summary.write("-" * 105 + "\n")
        
        for pattern_id, pattern_data in self.results['pattern_results'].items():
            if pattern_data.get('analyzed_trades', 0) > 0:
                name = pattern_data['pattern_name'][:28]
                signals = pattern_data['total_signals']
                trades = pattern_data['analyzed_trades']
                skipped = pattern_data.get('skipped_signals', 0)
                win_rate = pattern_data['win_rate']
                pnl = pattern_data['total_net_pnl']
                
                # Calculate pattern-specific metrics
                pattern_metrics = self.calculate_financial_metrics(pattern_data['trades'])
                sharpe = pattern_metrics.get('sharpe_ratio', 0)
                
                summary.write(f"{pattern_id:<5} {name:<30} {signals:<8} {trades:<7} {skipped:<8} {win_rate:<6.1f} ₹{pnl:<11.2f} {sharpe:<8.3f}\n")
        
        # Top performing patterns
        summary.write("\n🔍 TOP PERFORMING PATTERNS:\n")
        sorted_patterns = sorted(
            [(k, v) for k, v in self.results['pattern_results'].items() if v.get('analyzed_trades', 0) > 0],
            key=lambda x: x[1]['total_net_pnl'],
            reverse=True
        )
        
        for i, (pattern_id, data) in enumerate(sorted_patterns[:5]):
            pattern_metrics = self.calculate_financial_metrics(data['trades'])
            summary.write(f"   {i+1}. Pattern {pattern_id} ({data['pattern_name']}): ₹{data['total_net_pnl']:,.2f} net P&L, "
                         f"Sharpe: {pattern_metrics.get('sharpe_ratio', 0):.3f}\n")
        
        # Detailed trade examples
        summary.write(f"\n💡 DETAILED TRADE EXAMPLES:\n")
        summary.write("-" * 90 + "\n")
        summary.write(f"{'Pattern':<8} {'Type':<5} {'Entry':<10} {'Exit':<10} {'P&L':<12} {'Reason':<12}\n")
        summary.write("-" * 90 + "\n")
        
        for pattern_id, pattern_data in self.results['pattern_results'].items():
            trades = pattern_data.get('trades', [])
            if trades:
                profit_trades = [t for t in trades if t['net_pnl'] > 0]
                loss_trades = [t for t in trades if t['net_pnl'] <= 0]
                
                if profit_trades:
                    trade = profit_trades[0]
                    summary.write(f"{pattern_id:<8} {trade['signal_type']:<5} {trade['entry_price']:<10.2f} "
                                f"{trade['exit_price']:<10.2f} ₹{trade['net_pnl']:<11.2f} {trade['exit_reason'] or 'Timeout':<12}\n")
                
                if loss_trades:
                    trade = loss_trades[0]
                    summary.write(f"{pattern_id:<8} {trade['signal_type']:<5} {trade['entry_price']:<10.2f} "
                                f"{trade['exit_price']:<10.2f} ₹{trade['net_pnl']:<11.2f} {trade['exit_reason'] or 'Timeout':<12}\n")
        
        # Configuration info
        summary.write(f"\n⚙️ CONFIGURATION:\n")
        config = self.results['config']
        summary.write(f"   Timeframe: {config['timeframe']}\n")
        summary.write(f"   Period: {config['start_date']} to {config['end_date']}\n")
        summary.write(f"   Symbol: {config['symbol']}\n")
        summary.write(f"   Initial Capital: ₹{config['initial_capital']:,}\n")
        summary.write(f"   Quantity per Trade: {getattr(self, 'QUANTITY', 1)}\n")
        summary.write(f"   Stop Loss: {getattr(self, 'STOP_LOSS_PCT', 0.01)*100:.1f}%\n")
        summary.write(f"   Take Profit: {getattr(self, 'TAKE_PROFIT_PCT', 0.015)*100:.1f}%\n")
        summary.write(f"   Transaction Cost: {getattr(self, 'TRANSACTION_COST', 0)*100:.1f}%\n")
        
        # Timestamp
        summary.write(f"\n⏰ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        return summary.getvalue()
    
    def save_summary_text(self, output_dir: str):
        """Save the summary text to a file"""
        summary_text = self.generate_summary_text()
        
        # Save as text file
        summary_path = os.path.join(output_dir, 'backtest_summary.txt')
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_text)
        
        print(f"💾 Saved summary text to {summary_path}")
        return summary_path


def main():
    """Main function to run the backtesting system"""
    
    # Initialize backtester
    backtester = IchimokuADXBacktester()
    
    # Run comprehensive backtest
    results = backtester.run_comprehensive_backtest()
    
    # Print summary
    backtester.print_summary()
    
    # Save results
    backtester.save_results()
    
    print(f"\n✅ Backtesting completed successfully!")
    print(f"📁 Results saved to '{backtester.BACKTEST_NAME}' folder in results directory")


if __name__ == "__main__":
    main()
