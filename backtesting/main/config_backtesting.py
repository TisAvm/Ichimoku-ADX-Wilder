"""
Quick Configuration Script for Backtesting
Modify the variables in this file to customize your backtesting parameters
"""

# ============================================================================
# USER CONFIGURABLE VARIABLES - MODIFY THESE BEFORE RUNNING BACKTESTING
# ============================================================================

# Data Configuration
TIMEFRAME = "5min"  # Source timeframe: "1min", "5min", "10min", "15min"
CSV_PATH = "/home/algolinux/Documents/aviral/Ichimoku-ADX-Wilder/backtesting/data/ichimoku_adx_wilder_signals_5min.csv"  # Path to signals CSV file
SYMBOL = "NIFTY"  # Symbol to analyze in ClickHouse

# Date Range
START_DATE = "2024-01-01"  # Format: YYYY-MM-DD
END_DATE = "2025-06-30"    # Format: YYYY-MM-DD (Testing with smaller range first)

# Trading Parameters
INITIAL_CAPITAL = 100000      # Starting capital in rupees
POSITION_SIZE = 1           # Position size: 1 = buy 1 share/unit
QUANTITY = 2                # Number of shares/units to trade (fixed quantity)
TRANSACTION_COST = 0      # Transaction cost as fraction (0.001 = 0.1%)

# Risk Management
STOP_LOSS_PCT = 0.01          # Stop loss percentage (0.01 = 1%)
TAKE_PROFIT_PCT = 0.015       # Take profit percentage (0.015 = 1.5%)

# Analysis Parameters
MIN_HOLDING_MINUTES = 1       # Minimum holding period in minutes
MAX_HOLDING_MINUTES = 60      # Maximum holding period to analyze

# Output Configuration
OUTPUT_DIR = "../results"        # Base directory to save results
BACKTEST_NAME = "5min_full_backtest"  # Name for this backtest run (creates subfolder)
SAVE_DETAILED_TRADES = True   # Save minute-by-minute trade analysis
SAVE_PATTERN_SUMMARY = True   # Save pattern performance summary

# Available CSV Files (uncomment the one you want to use):
# CSV_PATH = "data/ichimoku_adx_wilder_signals_1min.csv"
# CSV_PATH = "data/ichimoku_adx_wilder_signals_5min.csv" 
# CSV_PATH = "data/ichimoku_adx_wilder_signals_10min.csv"
# CSV_PATH = "data/ichimoku_adx_wilder_signals_15min.csv"

# ============================================================================
# BACKTEST NAMING EXAMPLES (choose one or create your own)
# ============================================================================
"""
Example backtest names based on configuration:

# BACKTEST_NAME = "5min_full_2021_2025"     # 5min data, full period
# BACKTEST_NAME = "1min_recent_2024"        # 1min data, recent year
# BACKTEST_NAME = "10min_conservative_test"  # 10min data, conservative settings
# BACKTEST_NAME = "15min_high_capital"       # 15min data, high capital test
# BACKTEST_NAME = "pattern_optimization_v1"  # Pattern optimization run
# BACKTEST_NAME = "risk_analysis_2pct_sl"    # Risk analysis with 2% stop loss
# BACKTEST_NAME = "quick_validation_test"    # Quick validation run
"""

# ============================================================================
# PATTERN INFORMATION (for reference only)
# ============================================================================
"""
Pattern 0: Price-Tenkan Crossover
Pattern 1: Tenkan-Kijun Crossover
Pattern 2: Price-Senkou A Crossover
Pattern 3: Senkou A-B Crossover (Cloud)
Pattern 4: Chikou Span Confirmation
Pattern 5: Price Bounce/Rejection at Tenkan
Pattern 6: Price Crossing Kijun
Pattern 7: Price Bounce/Rejection at Senkou B
Pattern 8: Price Above/Below Cloud
Pattern 9: Additional Pattern
"""

# ============================================================================
# QUICK START EXAMPLES
# ============================================================================
"""
Example 1 - Test 5-minute signals on full period:
TIMEFRAME = "5min"
CSV_PATH = "data/ichimoku_adx_wilder_signals_5min.csv"
START_DATE = "2021-01-01"
END_DATE = "2025-06-30"

Example 2 - Test 1-minute signals on recent data:
TIMEFRAME = "1min"
CSV_PATH = "data/ichimoku_adx_wilder_signals_1min.csv"
START_DATE = "2024-01-01"
END_DATE = "2024-12-31"

Example 3 - Conservative testing with higher capital:
INITIAL_CAPITAL = 500000
POSITION_SIZE = 0.05  # 5% position size
STOP_LOSS_PCT = 0.01  # 1% stop loss
TAKE_PROFIT_PCT = 0.015  # 1.5% take profit
"""
