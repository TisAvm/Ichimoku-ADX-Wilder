"""
Ichimoku-ADX-Wilder Backtesting System
Performs backtesting on minute-level data with comprehensive analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
import clickhouse_connect
from typing import Dict, List, Tuple, Optional
import warnings
import os
from dotenv import load_dotenv
warnings.filterwarnings('ignore')

# Load environment variables from .env file
load_dotenv()


class IchimokuADXBacktester:
    """
    Comprehensive backtesting system for Ichimoku-ADX-Wilder signals
    """
    
    def __init__(self, 
                 clickhouse_host: str = None,
                 clickhouse_port: int = None,
                 clickhouse_username: str = None,
                 clickhouse_password: str = None,
                 initial_capital: float = 100000.0,
                 position_size: float = 0.1,
                 transaction_cost: float = 0.001):
        """
        Initialize the backtester
        
        Args:
            clickhouse_host: ClickHouse server host (if None, reads from .env)
            clickhouse_port: ClickHouse server port (if None, reads from .env)
            clickhouse_username: ClickHouse username (if None, reads from .env)
            clickhouse_password: ClickHouse password (if None, reads from .env)
            initial_capital: Starting capital for backtesting
            position_size: Position size as fraction of capital (0.1 = 10%)
            transaction_cost: Transaction cost as fraction (0.001 = 0.1%)
        """
        # Load ClickHouse configuration from .env file or use provided values
        self.clickhouse_host = clickhouse_host or os.getenv('CLICKHOUSE_HOST', 'localhost')
        self.clickhouse_port = clickhouse_port or int(os.getenv('CLICKHOUSE_PORT', '8123'))
        self.clickhouse_username = clickhouse_username or os.getenv('CLICKHOUSE_USER', 'default')
        self.clickhouse_password = clickhouse_password or os.getenv('CLICKHOUSE_PASSWORD', '')
        
        print(f"ClickHouse Configuration:")
        print(f"  Host: {self.clickhouse_host}")
        print(f"  Port: {self.clickhouse_port}")
        print(f"  Username: {self.clickhouse_username}")
        print(f"  Password: {'*' * len(self.clickhouse_password) if self.clickhouse_password else 'Not set'}")
        
        self.initial_capital = initial_capital
        self.position_size = position_size
        self.transaction_cost = transaction_cost
        
        self.client = None
        self.signals_df = None
        self.minute_data = None
        self.backtest_results = None
        
        # Trading session parameters
        self.session_start = time(9, 20)  # 9:20 AM
        self.session_end = time(15, 25)   # 3:25 PM
        
    def connect_clickhouse(self):
        """Connect to ClickHouse database"""
        try:
            self.client = clickhouse_connect.get_client(
                host=self.clickhouse_host,
                port=self.clickhouse_port,
                username=self.clickhouse_username,
                password=self.clickhouse_password
            )
            print("Successfully connected to ClickHouse")
        except Exception as e:
            print(f"Failed to connect to ClickHouse: {e}")
            raise
    
    def load_signals(self, signals_file_path: str):
        """
        Load the pre-generated signals from CSV file
        
        Args:
            signals_file_path: Path to the signals CSV file
        """
        try:
            self.signals_df = pd.read_csv(signals_file_path)
            self.signals_df['datetime'] = pd.to_datetime(self.signals_df['datetime'])
            self.signals_df.set_index('datetime', inplace=True)
            
            # Extract signal patterns
            pattern_cols = [col for col in self.signals_df.columns if col.startswith('pattern_')]
            self.signals_df['signal'] = self.signals_df[pattern_cols].sum(axis=1)
            self.signals_df['signal_type'] = np.where(self.signals_df['signal'] > 0, 'BUY', 
                                                    np.where(self.signals_df['signal'] < 0, 'SELL', 'HOLD'))
            
            print(f"Loaded {len(self.signals_df)} signal records")
            print(f"Signal distribution: {self.signals_df['signal_type'].value_counts()}")
            
        except Exception as e:
            print(f"Error loading signals: {e}")
            raise
    
    def fetch_minute_data(self, symbol: str, start_date: str, end_date: str, database: str = 'market_data'):
        """
        Fetch minute-level data from ClickHouse
        
        Args:
            symbol: Trading symbol (e.g., 'NIFTY')
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            database: ClickHouse database name
        """
        try:
            if not self.client:
                self.connect_clickhouse()
            
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
            """
            
            result = self.client.query(query)
            
            if result.result_rows:
                self.minute_data = pd.DataFrame(result.result_rows, columns=result.column_names)
                self.minute_data['datetime'] = pd.to_datetime(self.minute_data['datetime'])
                self.minute_data.set_index('datetime', inplace=True)
                
                print(f"✅ Successfully fetched {len(self.minute_data)} minute-level records from ClickHouse")
                return self.minute_data
            else:
                print("ClickHouse query returned no data, using sample data")
                return self._generate_sample_minute_data(start_date, end_date)
                
        except Exception as e:
            print(f"ClickHouse error: {e}")
            print("Using sample minute data for backtesting...")
            return self._generate_sample_minute_data(start_date, end_date)
    
    def _generate_sample_minute_data(self, start_date: str, end_date: str):
        """Generate sample minute data for testing when ClickHouse is not available"""
        print("Generating sample minute data for testing...")
        
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        minute_data_list = []
        
        base_price = 14000
        
        for date in date_range:
            # Skip weekends
            if date.weekday() >= 5:
                continue
                
            # Generate minute data for trading session (9:20 to 15:25)
            trading_minutes = pd.date_range(
                start=date.replace(hour=9, minute=20),
                end=date.replace(hour=15, minute=25),
                freq='min',
                tz='Asia/Kolkata'  # Match the timezone of signals data
            )
            
            for i, dt in enumerate(trading_minutes):
                # Generate realistic price movement
                noise = np.random.normal(0, 1)
                price_change = noise * 0.1
                
                if i == 0:
                    open_price = base_price + np.random.normal(0, 10)
                else:
                    open_price = close_price
                
                high_price = open_price + abs(np.random.normal(0, 5))
                low_price = open_price - abs(np.random.normal(0, 5))
                close_price = open_price + price_change
                
                # Ensure high >= max(open, close) and low <= min(open, close)
                high_price = max(high_price, open_price, close_price)
                low_price = min(low_price, open_price, close_price)
                
                volume = np.random.randint(1000, 10000)
                
                minute_data_list.append({
                    'datetime': dt,
                    'open': round(open_price, 2),
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'close': round(close_price, 2),
                    'volume': volume
                })
        
        self.minute_data = pd.DataFrame(minute_data_list)
        self.minute_data.set_index('datetime', inplace=True)
        
        print(f"Generated {len(self.minute_data)} sample minute records")
        return self.minute_data
    
    def align_signals_with_minute_data(self):
        """Align signals with minute-level data"""
        if self.signals_df is None or self.minute_data is None:
            raise ValueError("Both signals and minute data must be loaded first")
        
        # Resample signals to minute level using forward fill
        minute_index = self.minute_data.index
        aligned_signals = self.signals_df.reindex(minute_index, method='ffill')
        
        # Combine minute data with signals
        self.combined_data = self.minute_data.copy()
        self.combined_data['signal'] = aligned_signals['signal'].fillna(0)
        self.combined_data['signal_type'] = aligned_signals['signal_type'].fillna('HOLD')
        
        # Add technical indicators from signals
        tech_indicators = ['tenkan_sen', 'kijun_sen', 'senkou_a', 'senkou_b', 'chikou', 'adx']
        for indicator in tech_indicators:
            if indicator in aligned_signals.columns:
                self.combined_data[indicator] = aligned_signals[indicator]
        
        print(f"Aligned data contains {len(self.combined_data)} records")
        return self.combined_data
    
    def run_backtest(self):
        """Run the comprehensive backtest"""
        if self.combined_data is None:
            raise ValueError("Data must be aligned first")
        
        # Initialize tracking variables
        positions = []
        trades = []
        portfolio_value = [self.initial_capital]
        cash = self.initial_capital
        current_position = 0  # 0 = no position, 1 = long, -1 = short
        entry_price = 0
        entry_time = None
        
        results = []
        
        for i, (timestamp, row) in enumerate(self.combined_data.iterrows()):
            current_price = row['close']
            signal_type = row['signal_type']
            signal_strength = row['signal']
            
            # Calculate current portfolio value
            if current_position != 0:
                unrealized_pnl = current_position * (current_price - entry_price)
                current_portfolio_value = cash + unrealized_pnl
            else:
                current_portfolio_value = cash
            
            portfolio_value.append(current_portfolio_value)
            
            # Signal processing
            if signal_type == 'BUY' and current_position <= 0:
                # Close short position if exists
                if current_position < 0:
                    pnl = -current_position * (current_price - entry_price)
                    transaction_cost_amount = abs(current_position) * current_price * self.transaction_cost
                    net_pnl = pnl - transaction_cost_amount
                    cash += net_pnl
                    
                    trades.append({
                        'entry_time': entry_time,
                        'exit_time': timestamp,
                        'type': 'SHORT',
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'quantity': abs(current_position),
                        'pnl': pnl,
                        'transaction_cost': transaction_cost_amount,
                        'net_pnl': net_pnl
                    })
                
                # Open long position
                position_value = cash * self.position_size
                quantity = position_value / current_price
                transaction_cost_amount = quantity * current_price * self.transaction_cost
                
                if cash >= transaction_cost_amount:
                    current_position = quantity
                    entry_price = current_price
                    entry_time = timestamp
                    cash -= transaction_cost_amount
            
            elif signal_type == 'SELL' and current_position >= 0:
                # Close long position if exists
                if current_position > 0:
                    pnl = current_position * (current_price - entry_price)
                    transaction_cost_amount = current_position * current_price * self.transaction_cost
                    net_pnl = pnl - transaction_cost_amount
                    cash += net_pnl
                    
                    trades.append({
                        'entry_time': entry_time,
                        'exit_time': timestamp,
                        'type': 'LONG',
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'quantity': current_position,
                        'pnl': pnl,
                        'transaction_cost': transaction_cost_amount,
                        'net_pnl': net_pnl
                    })
                
                # Open short position
                position_value = cash * self.position_size
                quantity = position_value / current_price
                transaction_cost_amount = quantity * current_price * self.transaction_cost
                
                if cash >= transaction_cost_amount:
                    current_position = -quantity
                    entry_price = current_price
                    entry_time = timestamp
                    cash -= transaction_cost_amount
            
            # Record position and portfolio state
            results.append({
                'timestamp': timestamp,
                'price': current_price,
                'signal': signal_strength,
                'signal_type': signal_type,
                'position': current_position,
                'cash': cash,
                'portfolio_value': current_portfolio_value,
                'unrealized_pnl': current_position * (current_price - entry_price) if current_position != 0 else 0
            })
        
        # Close any remaining position
        if current_position != 0:
            final_price = self.combined_data['close'].iloc[-1]
            pnl = current_position * (final_price - entry_price)
            transaction_cost_amount = abs(current_position) * final_price * self.transaction_cost
            net_pnl = pnl - transaction_cost_amount
            
            trades.append({
                'entry_time': entry_time,
                'exit_time': self.combined_data.index[-1],
                'type': 'LONG' if current_position > 0 else 'SHORT',
                'entry_price': entry_price,
                'exit_price': final_price,
                'quantity': abs(current_position),
                'pnl': pnl,
                'transaction_cost': transaction_cost_amount,
                'net_pnl': net_pnl
            })
        
        self.backtest_results = pd.DataFrame(results)
        self.trades_df = pd.DataFrame(trades)
        self.portfolio_values = portfolio_value[1:]  # Remove initial value
        
        return self.backtest_results
    
    def calculate_metrics(self):
        """Calculate comprehensive performance metrics"""
        if self.backtest_results is None:
            raise ValueError("Backtest must be run first")
        
        # Basic metrics
        initial_value = self.initial_capital
        final_value = self.backtest_results['portfolio_value'].iloc[-1]
        total_return = (final_value - initial_value) / initial_value * 100
        
        # Calculate daily returns
        daily_values = self.backtest_results.groupby(self.backtest_results['timestamp'].dt.date)['portfolio_value'].last()
        daily_returns = daily_values.pct_change().dropna()
        
        # Risk metrics
        volatility = daily_returns.std() * np.sqrt(252) * 100  # Annualized
        sharpe_ratio = (daily_returns.mean() * 252) / (daily_returns.std() * np.sqrt(252)) if daily_returns.std() != 0 else 0
        
        # Drawdown calculation
        peak = daily_values.expanding().max()
        drawdown = (daily_values - peak) / peak * 100
        max_drawdown = drawdown.min()
        
        # Trade-based metrics
        if len(self.trades_df) > 0:
            winning_trades = self.trades_df[self.trades_df['net_pnl'] > 0]
            losing_trades = self.trades_df[self.trades_df['net_pnl'] < 0]
            
            win_rate = len(winning_trades) / len(self.trades_df) * 100
            avg_win = winning_trades['net_pnl'].mean() if len(winning_trades) > 0 else 0
            avg_loss = losing_trades['net_pnl'].mean() if len(losing_trades) > 0 else 0
            profit_factor = abs(winning_trades['net_pnl'].sum() / losing_trades['net_pnl'].sum()) if len(losing_trades) > 0 and losing_trades['net_pnl'].sum() != 0 else float('inf')
            
            total_trades = len(self.trades_df)
            total_pnl = self.trades_df['net_pnl'].sum()
            total_transaction_costs = self.trades_df['transaction_cost'].sum()
        else:
            win_rate = 0
            avg_win = 0
            avg_loss = 0
            profit_factor = 0
            total_trades = 0
            total_pnl = 0
            total_transaction_costs = 0
        
        metrics = {
            'Initial Capital': initial_value,
            'Final Portfolio Value': final_value,
            'Total Return (%)': total_return,
            'Annualized Volatility (%)': volatility,
            'Sharpe Ratio': sharpe_ratio,
            'Maximum Drawdown (%)': max_drawdown,
            'Total Trades': total_trades,
            'Win Rate (%)': win_rate,
            'Average Win': avg_win,
            'Average Loss': avg_loss,
            'Profit Factor': profit_factor,
            'Total PnL': total_pnl,
            'Total Transaction Costs': total_transaction_costs,
            'Net PnL': total_pnl
        }
        
        return metrics
    
    def generate_report(self):
        """Generate a comprehensive backtest report"""
        metrics = self.calculate_metrics()
        
        print("=" * 60)
        print("ICHIMOKU-ADX-WILDER BACKTEST REPORT")
        print("=" * 60)
        print(f"Backtest Period: {self.backtest_results['timestamp'].iloc[0]} to {self.backtest_results['timestamp'].iloc[-1]}")
        print(f"Trading Session: {self.session_start} to {self.session_end}")
        print(f"Data Points: {len(self.backtest_results)}")
        print()
        
        print("PERFORMANCE METRICS:")
        print("-" * 30)
        for key, value in metrics.items():
            if isinstance(value, float):
                if 'Rate' in key or 'Return' in key or 'Volatility' in key or 'Drawdown' in key:
                    print(f"{key}: {value:.2f}%")
                elif 'Ratio' in key or 'Factor' in key:
                    print(f"{key}: {value:.2f}")
                else:
                    print(f"{key}: {value:,.2f}")
            else:
                print(f"{key}: {value}")
        
        print()
        print("SIGNAL ANALYSIS:")
        print("-" * 20)
        signal_counts = self.backtest_results['signal_type'].value_counts()
        for signal_type, count in signal_counts.items():
            percentage = count / len(self.backtest_results) * 100
            print(f"{signal_type}: {count} ({percentage:.1f}%)")
        
        if len(self.trades_df) > 0:
            print()
            print("TRADE DETAILS:")
            print("-" * 15)
            print(f"Best Trade: {self.trades_df['net_pnl'].max():.2f}")
            print(f"Worst Trade: {self.trades_df['net_pnl'].min():.2f}")
            print(f"Average Trade Duration: {self._calculate_avg_trade_duration()}")
        
        return metrics
    
    def _calculate_avg_trade_duration(self):
        """Calculate average trade duration"""
        if len(self.trades_df) == 0:
            return "N/A"
        
        durations = []
        for _, trade in self.trades_df.iterrows():
            duration = trade['exit_time'] - trade['entry_time']
            durations.append(duration.total_seconds() / 60)  # in minutes
        
        avg_duration_minutes = np.mean(durations)
        hours = int(avg_duration_minutes // 60)
        minutes = int(avg_duration_minutes % 60)
        
        return f"{hours}h {minutes}m"
    
    def save_results(self, output_dir: str = './results/'):
        """Save backtest results to files"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Save main results
        self.backtest_results.to_csv(f"{output_dir}/backtest_results.csv")
        
        # Save trades
        if len(self.trades_df) > 0:
            self.trades_df.to_csv(f"{output_dir}/trades.csv", index=False)
        
        # Save metrics
        metrics = self.calculate_metrics()
        metrics_df = pd.DataFrame(list(metrics.items()), columns=['Metric', 'Value'])
        metrics_df.to_csv(f"{output_dir}/metrics.csv", index=False)
        
        print(f"Results saved to {output_dir}")


def run_complete_backtest(signals_file: str, 
                         symbol: str = 'NIFTY',
                         start_date: str = '2021-01-01',
                         end_date: str = '2021-12-31',
                         initial_capital: float = 100000,
                         position_size: float = 0.1):
    """
    Run a complete backtest with the given parameters
    
    Args:
        signals_file: Path to the signals CSV file
        symbol: Trading symbol
        start_date: Start date for backtesting
        end_date: End date for backtesting
        initial_capital: Initial capital for backtesting
        position_size: Position size as fraction of capital
    """
    print("Initializing Ichimoku-ADX-Wilder Backtester...")
    
    # Initialize backtester
    backtester = IchimokuADXBacktester(
        initial_capital=initial_capital,
        position_size=position_size
    )
    
    # Load signals
    print("Loading signals...")
    backtester.load_signals(signals_file)
    
    # Fetch minute data (will use sample data if ClickHouse unavailable)
    print("Fetching minute-level data...")
    backtester.fetch_minute_data(symbol, start_date, end_date)
    
    # Align signals with minute data
    print("Aligning signals with minute data...")
    backtester.align_signals_with_minute_data()
    
    # Run backtest
    print("Running backtest...")
    backtester.run_backtest()
    
    # Generate report
    print("Generating report...")
    metrics = backtester.generate_report()
    
    # Save results
    backtester.save_results()
    
    return backtester, metrics


if __name__ == "__main__":
    # Example usage
    signals_file = "data/ichimoku_adx_wilder_signals.csv"
    
    backtester, metrics = run_complete_backtest(
        signals_file=signals_file,
        symbol='NIFTY',
        start_date='2021-01-01',
        end_date='2021-12-31',
        initial_capital=100000,
        position_size=0.1
    )
