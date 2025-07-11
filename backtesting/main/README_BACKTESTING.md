# Ichimoku-ADX-Wilder Backtesting System

A comprehensive backtesting system that tests trading signals on 1-minute ClickHouse data to validate signal accuracy and profitability.

## Features

- **Multi-timeframe Analysis**: Test signals from 1min, 5min, 10min, or 15min data
- **Pattern Analysis**: Analyze all 10 Ichimoku-ADX patterns individually
- **Minute-by-Minute Tracking**: Track P&L for each minute after signal generation
- **Risk Management**: Built-in stop loss and take profit functionality
- **Comprehensive Reporting**: Detailed statistics and trade analysis
- **ClickHouse Integration**: Real-time data fetching from ClickHouse database

## Quick Start

### 1. Configure Parameters

Edit `config_backtesting.py` to customize your backtesting parameters:

```python
# Data Configuration
TIMEFRAME = "5min"  # Source timeframe for signals
CSV_PATH = "data/ichimoku_adx_wilder_signals_5min.csv"
SYMBOL = "NIFTY"

# Date Range
START_DATE = "2021-01-01"
END_DATE = "2025-06-30"

# Trading Parameters
INITIAL_CAPITAL = 100000
POSITION_SIZE = 0.1  # 10% position size
STOP_LOSS_PCT = 0.02  # 2% stop loss
TAKE_PROFIT_PCT = 0.02  # 2% take profit

# Backtest Naming
BACKTEST_NAME = "5min_full_backtest"  # Creates results/5min_full_backtest/ folder
```

### 2. Run Backtesting

```bash
# Simple way
python run_backtest.py

# Or directly
python backtesting.py
```

### 3. View Results

Results are saved to the `results/` directory in a named subfolder:

- `results/your_backtest_name/pattern_summary.csv`: Performance summary for each pattern
- `results/your_backtest_name/detailed_trades.csv`: Minute-by-minute trade analysis
- `results/your_backtest_name/backtest_config.csv`: Configuration used for this backtest

## Backtest Naming Examples

You can organize your backtests by using descriptive names:

```python
# Different naming strategies
BACKTEST_NAME = "5min_full_2021_2025"     # Full period analysis
BACKTEST_NAME = "1min_recent_2024"        # Recent data analysis
BACKTEST_NAME = "conservative_2pct_sl"    # Risk management test
BACKTEST_NAME = "pattern_optimization_v1"  # Pattern optimization
BACKTEST_NAME = "high_capital_test"       # High capital scenario
```

## Configuration Options

### Available CSV Files

- `ichimoku_adx_wilder_signals_1min.csv`
- `ichimoku_adx_wilder_signals_5min.csv`
- `ichimoku_adx_wilder_signals_10min.csv`
- `ichimoku_adx_wilder_signals_15min.csv`

### Key Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `TIMEFRAME` | Source signal timeframe | `"5min"` |
| `CSV_PATH` | Path to signals CSV | `"data/signals_5min.csv"` |
| `BACKTEST_NAME` | Name for this backtest run | `"5min_full_backtest"` |
| `START_DATE` | Analysis start date | `"2021-01-01"` |
| `END_DATE` | Analysis end date | `"2025-06-30"` |
| `INITIAL_CAPITAL` | Starting capital (₹) | `100000` |
| `POSITION_SIZE` | Position size (fraction) | `0.1` (10%) |
| `STOP_LOSS_PCT` | Stop loss percentage | `0.02` (2%) |
| `TAKE_PROFIT_PCT` | Take profit percentage | `0.02` (2%) |
| `MAX_HOLDING_MINUTES` | Max analysis period | `60` minutes |

## Signal Time Adjustment

The system automatically adjusts signal timing based on timeframe:

- **5min signals**: Signal at 9:45 → Executed at 9:50 (candle close)
- **10min signals**: Signal at 9:40 → Executed at 9:50 (candle close)
- **15min signals**: Signal at 9:45 → Executed at 10:00 (candle close)

## Pattern Analysis

The system analyzes 10 different Ichimoku-ADX patterns:

| Pattern | Description |
|---------|-------------|
| 0 | Price-Tenkan Crossover |
| 1 | Tenkan-Kijun Crossover |
| 2 | Price-Senkou A Crossover |
| 3 | Senkou A-B Crossover (Cloud) |
| 4 | Chikou Span Confirmation |
| 5 | Price Bounce/Rejection at Tenkan |
| 6 | Price Crossing Kijun |
| 7 | Price Bounce/Rejection at Senkou B |
| 8 | Price Above/Below Cloud |
| 9 | Additional Pattern |

## Output Metrics

### Pattern Summary
- Total signals generated
- Win rate percentage
- Average profit/loss
- Maximum single trade profit/loss
- Average holding period

### Detailed Trades
- Entry/exit times and prices
- Minute-by-minute P&L tracking
- Stop loss/take profit triggers
- Profitable vs losing minutes

## Requirements

- Python 3.8+
- pandas
- numpy
- clickhouse-connect
- python-dotenv

## ClickHouse Setup

Ensure your `.env` file contains:
```env
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=your_password
```

## Example Usage

### Test Recent Data with Conservative Settings
```python
TIMEFRAME = "5min"
START_DATE = "2024-01-01" 
END_DATE = "2024-12-31"
INITIAL_CAPITAL = 500000
POSITION_SIZE = 0.05  # 5%
STOP_LOSS_PCT = 0.01  # 1%
```

### Test All Historical Data
```python
TIMEFRAME = "5min"
START_DATE = "2021-01-01"
END_DATE = "2025-06-30"
INITIAL_CAPITAL = 100000
POSITION_SIZE = 0.1  # 10%
```

## Troubleshooting

### Common Issues

1. **ClickHouse Connection Error**
   - Check `.env` file configuration
   - Verify ClickHouse server is running
   - Test connection with `test_clickhouse.py`

2. **CSV File Not Found**
   - Verify CSV path in `config_backtesting.py`
   - Check if file exists in `data/` directory

3. **No Data Returned**
   - Check date ranges
   - Verify symbol name (usually "NIFTY")
   - Ensure ClickHouse has data for the period

### Performance Tips

- Use smaller date ranges for faster testing
- Reduce `MAX_HOLDING_MINUTES` for quicker analysis
- Test individual patterns by modifying the code

## Contributing

Feel free to enhance the backtesting system by:
- Adding new pattern analysis
- Implementing additional risk management
- Creating visualization features
- Optimizing performance
