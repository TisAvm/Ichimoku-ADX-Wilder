"""
Signal Generator for Ichimoku-ADX-Wilder Strategy
This module provides functions to call and execute the backtesting system
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backtesting import IchimokuADXBacktester, run_complete_backtest


class SignalGenerator:
    """
    Signal generator and backtesting orchestrator for Ichimoku-ADX-Wilder strategy
    """
    
    def __init__(self, signals_file_path: str):
        """
        Initialize the signal generator
        
        Args:
            signals_file_path: Path to the CSV file containing pre-generated signals
        """
        self.signals_file_path = signals_file_path
        self.signals_df = None
        self.load_signals()
    
    def load_signals(self):
        """Load and validate the signals data"""
        try:
            self.signals_df = pd.read_csv(self.signals_file_path)
            self.signals_df['datetime'] = pd.to_datetime(self.signals_df['datetime'])
            print(f"Loaded {len(self.signals_df)} signal records from {self.signals_file_path}")
            
            # Display signal summary
            self.display_signal_summary()
            
        except Exception as e:
            print(f"Error loading signals: {e}")
            raise
    
    def display_signal_summary(self):
        """Display a summary of the loaded signals"""
        if self.signals_df is None:
            print("No signals loaded")
            return
        
        print("\n" + "="*50)
        print("SIGNAL DATA SUMMARY")
        print("="*50)
        
        # Date range
        start_date = self.signals_df['datetime'].min()
        end_date = self.signals_df['datetime'].max()
        print(f"Date Range: {start_date} to {end_date}")
        print(f"Total Records: {len(self.signals_df)}")
        
        # Pattern analysis
        pattern_cols = [col for col in self.signals_df.columns if col.startswith('pattern_')]
        if pattern_cols:
            print(f"Signal Patterns Available: {len(pattern_cols)}")
            
            # Calculate total signals per pattern
            pattern_summary = {}
            for col in pattern_cols:
                non_zero = (self.signals_df[col] != 0).sum()
                pattern_summary[col] = non_zero
            
            print("\nPattern Activity:")
            for pattern, count in pattern_summary.items():
                percentage = (count / len(self.signals_df)) * 100
                print(f"  {pattern}: {count} signals ({percentage:.1f}%)")
        
        # Technical indicators summary
        tech_indicators = ['tenkan_sen', 'kijun_sen', 'senkou_a', 'senkou_b', 'chikou', 'adx']
        available_indicators = [ind for ind in tech_indicators if ind in self.signals_df.columns]
        
        if available_indicators:
            print(f"\nTechnical Indicators Available: {len(available_indicators)}")
            for indicator in available_indicators:
                non_null = self.signals_df[indicator].notna().sum()
                percentage = (non_null / len(self.signals_df)) * 100
                print(f"  {indicator}: {non_null} values ({percentage:.1f}% coverage)")
    
    def get_date_range(self) -> Tuple[str, str]:
        """Get the date range of available signals"""
        if self.signals_df is None:
            return None, None
        
        start_date = self.signals_df['datetime'].min().strftime('%Y-%m-%d')
        end_date = self.signals_df['datetime'].max().strftime('%Y-%m-%d')
        
        return start_date, end_date
    
    def filter_signals_by_date(self, start_date: str, end_date: str) -> int:
        """
        Filter signals by date range and return count of filtered signals
        
        Args:
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            
        Returns:
            Number of signals in the filtered range
        """
        if self.signals_df is None:
            return 0
        
        mask = (self.signals_df['datetime'] >= start_date) & (self.signals_df['datetime'] <= end_date)
        filtered_count = mask.sum()
        
        print(f"Signals in date range {start_date} to {end_date}: {filtered_count}")
        return filtered_count
    
    def analyze_signal_quality(self) -> Dict:
        """Analyze the quality and distribution of signals"""
        if self.signals_df is None:
            return {}
        
        analysis = {}
        
        # Pattern analysis
        pattern_cols = [col for col in self.signals_df.columns if col.startswith('pattern_')]
        
        if pattern_cols:
            # Calculate signal strength distribution
            total_signals = self.signals_df[pattern_cols].sum(axis=1)
            signal_strength_dist = total_signals.value_counts().sort_index()
            
            analysis['signal_strength_distribution'] = signal_strength_dist.to_dict()
            analysis['max_signal_strength'] = total_signals.max()
            analysis['min_signal_strength'] = total_signals.min()
            analysis['avg_signal_strength'] = total_signals.mean()
            
            # Signal frequency
            analysis['total_buy_signals'] = (total_signals > 0).sum()
            analysis['total_sell_signals'] = (total_signals < 0).sum()
            analysis['total_neutral'] = (total_signals == 0).sum()
        
        # ADX analysis
        if 'adx' in self.signals_df.columns:
            adx_data = self.signals_df['adx'].dropna()
            analysis['adx_stats'] = {
                'mean': adx_data.mean(),
                'std': adx_data.std(),
                'min': adx_data.min(),
                'max': adx_data.max(),
                'strong_trend_signals': (adx_data > 25).sum(),  # ADX > 25 indicates strong trend
                'weak_trend_signals': (adx_data < 20).sum()     # ADX < 20 indicates weak trend
            }
        
        return analysis
    
    def run_backtest_scenario(self, 
                            scenario_name: str,
                            start_date: str,
                            end_date: str,
                            initial_capital: float = 100000,
                            position_size: float = 0.1,
                            symbol: str = 'NIFTY') -> Dict:
        """
        Run a specific backtesting scenario
        
        Args:
            scenario_name: Name of the scenario for identification
            start_date: Start date for backtesting
            end_date: End date for backtesting
            initial_capital: Initial capital
            position_size: Position size as fraction of capital
            symbol: Trading symbol
            
        Returns:
            Dictionary containing backtest results and metrics
        """
        print(f"\n{'='*60}")
        print(f"RUNNING BACKTEST SCENARIO: {scenario_name}")
        print(f"{'='*60}")
        print(f"Period: {start_date} to {end_date}")
        print(f"Initial Capital: ₹{initial_capital:,.2f}")
        print(f"Position Size: {position_size*100}%")
        print(f"Symbol: {symbol}")
        print()
        
        try:
            # Run the backtest
            backtester, metrics = run_complete_backtest(
                signals_file=self.signals_file_path,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                position_size=position_size
            )
            
            scenario_results = {
                'scenario_name': scenario_name,
                'parameters': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'initial_capital': initial_capital,
                    'position_size': position_size,
                    'symbol': symbol
                },
                'metrics': metrics,
                'backtester': backtester
            }
            
            return scenario_results
            
        except Exception as e:
            print(f"Error running backtest scenario '{scenario_name}': {e}")
            return {'error': str(e)}
    
    def run_multiple_scenarios(self) -> List[Dict]:
        """Run multiple backtesting scenarios with different parameters"""
        scenarios = []
        
        # Get available date range
        start_date, end_date = self.get_date_range()
        
        if not start_date or not end_date:
            print("Cannot determine date range from signals")
            return scenarios
        
        # Scenario 1: Full period with standard parameters
        scenarios.append(self.run_backtest_scenario(
            scenario_name="Full Period - Standard",
            start_date=start_date,
            end_date=end_date,
            initial_capital=100000,
            position_size=0.1
        ))
        
        # Scenario 2: Full period with aggressive position sizing
        scenarios.append(self.run_backtest_scenario(
            scenario_name="Full Period - Aggressive",
            start_date=start_date,
            end_date=end_date,
            initial_capital=100000,
            position_size=0.2
        ))
        
        # Scenario 3: Full period with conservative position sizing
        scenarios.append(self.run_backtest_scenario(
            scenario_name="Full Period - Conservative",
            start_date=start_date,
            end_date=end_date,
            initial_capital=100000,
            position_size=0.05
        ))
        
        # Scenario 4: Higher capital
        scenarios.append(self.run_backtest_scenario(
            scenario_name="High Capital - Standard",
            start_date=start_date,
            end_date=end_date,
            initial_capital=500000,
            position_size=0.1
        ))
        
        return scenarios
    
    def compare_scenarios(self, scenarios: List[Dict]):
        """Compare multiple backtesting scenarios"""
        if not scenarios:
            print("No scenarios to compare")
            return
        
        print("\n" + "="*80)
        print("SCENARIO COMPARISON")
        print("="*80)
        
        comparison_metrics = [
            'Total Return (%)',
            'Sharpe Ratio',
            'Maximum Drawdown (%)',
            'Win Rate (%)',
            'Total Trades',
            'Profit Factor',
            'Final Portfolio Value'
        ]
        
        comparison_data = []
        
        for scenario in scenarios:
            if 'error' in scenario:
                continue
                
            scenario_data = {'Scenario': scenario['scenario_name']}
            
            for metric in comparison_metrics:
                if metric in scenario['metrics']:
                    scenario_data[metric] = scenario['metrics'][metric]
                else:
                    scenario_data[metric] = 'N/A'
            
            comparison_data.append(scenario_data)
        
        if comparison_data:
            import pandas as pd
            comparison_df = pd.DataFrame(comparison_data)
            print(comparison_df.to_string(index=False, float_format='%.2f'))
            
            # Save comparison
            comparison_df.to_csv('./results/scenario_comparison.csv', index=False)
            print(f"\nScenario comparison saved to ./results/scenario_comparison.csv")
    
    def generate_trading_signals_for_live(self, lookback_days: int = 30) -> pd.DataFrame:
        """
        Generate recent trading signals for live trading
        
        Args:
            lookback_days: Number of days to look back for recent signals
            
        Returns:
            DataFrame with recent signals
        """
        if self.signals_df is None:
            return pd.DataFrame()
        
        # Get recent signals
        end_date = self.signals_df['datetime'].max()
        start_date = end_date - timedelta(days=lookback_days)
        
        recent_signals = self.signals_df[
            self.signals_df['datetime'] >= start_date
        ].copy()
        
        # Process signals for live trading
        pattern_cols = [col for col in recent_signals.columns if col.startswith('pattern_')]
        recent_signals['total_signal'] = recent_signals[pattern_cols].sum(axis=1)
        recent_signals['signal_type'] = recent_signals['total_signal'].apply(
            lambda x: 'BUY' if x > 0 else ('SELL' if x < 0 else 'HOLD')
        )
        
        # Filter only actionable signals
        actionable_signals = recent_signals[recent_signals['total_signal'] != 0].copy()
        
        print(f"Recent {lookback_days} days: {len(actionable_signals)} actionable signals")
        
        return actionable_signals


def main():
    """Main function to demonstrate signal generation and backtesting"""
    # Path to signals file
    signals_file = "data/ichimoku_adx_wilder_signals.csv"
    
    if not os.path.exists(signals_file):
        print(f"Signals file not found: {signals_file}")
        print("Please ensure the signals file exists before running backtests.")
        return
    
    # Initialize signal generator
    print("Initializing Signal Generator...")
    signal_gen = SignalGenerator(signals_file)
    
    # Analyze signal quality
    print("\nAnalyzing signal quality...")
    quality_analysis = signal_gen.analyze_signal_quality()
    
    if quality_analysis:
        print("\nSIGNAL QUALITY ANALYSIS:")
        print("-" * 30)
        for key, value in quality_analysis.items():
            if isinstance(value, dict):
                print(f"{key}:")
                for sub_key, sub_value in value.items():
                    print(f"  {sub_key}: {sub_value}")
            else:
                print(f"{key}: {value}")
    
    # Run multiple scenarios
    print("\nRunning multiple backtesting scenarios...")
    scenarios = signal_gen.run_multiple_scenarios()
    
    # Compare scenarios
    signal_gen.compare_scenarios(scenarios)
    
    # Generate recent signals for live trading
    print("\nGenerating recent signals for live trading...")
    recent_signals = signal_gen.generate_trading_signals_for_live(lookback_days=30)
    
    if not recent_signals.empty:
        print(f"\nRecent actionable signals (last 30 days):")
        print(recent_signals[['datetime', 'close', 'signal_type', 'total_signal', 'adx']].tail(10))
        
        # Save recent signals
        recent_signals.to_csv('./results/recent_signals.csv', index=False)
        print("Recent signals saved to ./results/recent_signals.csv")
    
    print("\n" + "="*60)
    print("SIGNAL GENERATION AND BACKTESTING COMPLETED")
    print("="*60)
    print("Check the ./results/ directory for detailed outputs:")
    print("  - backtest_results.csv: Detailed backtest data")
    print("  - trades.csv: Individual trade records")
    print("  - metrics.csv: Performance metrics")
    print("  - scenario_comparison.csv: Comparison of different scenarios")
    print("  - recent_signals.csv: Recent signals for live trading")


if __name__ == "__main__":
    main()
