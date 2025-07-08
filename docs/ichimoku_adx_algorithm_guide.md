# Ichimoku-ADX-Wilder Trading Algorithm Documentation

## Overview

This repository contains a sophisticated trading algorithm that combines the **Ichimoku Kinko Hyo** indicator with the **Wilder's ADX (Average Directional Index)** to generate trading signals for the NIFTY index. The algorithm implements 10 distinct signal patterns that leverage the strengths of both technical indicators for enhanced market analysis.

## Table of Contents

1. [Algorithm Components](#algorithm-components)
2. [Technical Indicators](#technical-indicators)
3. [Signal Patterns](#signal-patterns)
4. [Data Requirements](#data-requirements)
5. [Installation and Setup](#installation-and-setup)
6. [Usage Guide](#usage-guide)
7. [Algorithm Logic](#algorithm-logic)
8. [Performance Considerations](#performance-considerations)
9. [Troubleshooting](#troubleshooting)

## Algorithm Components

### Core Files
- `backtesting/signal_genetator.ipynb`: Main signal generation logic and backtesting notebook
- `backtesting/backTesting-Algo.ipynb`: Comprehensive backtesting framework
- `dashboard/algoDashboard/`: Real-time monitoring dashboard
- `requirements.txt`: Python dependencies

### Key Functions
- `ichimoku()`: Calculates Ichimoku indicator components
- `adx_wilder()`: Computes Wilder's ADX and directional indicators
- `generate_signals()`: Generates 10 distinct trading signal patterns

## Technical Indicators

### 1. Ichimoku Kinko Hyo

The Ichimoku indicator consists of five components:

#### Components
- **Tenkan-sen (Conversion Line)**: `(9-period high + 9-period low) / 2`
- **Kijun-sen (Base Line)**: `(26-period high + 26-period low) / 2`
- **Senkou Span A (Leading Span A)**: `(Tenkan-sen + Kijun-sen) / 2` shifted 26 periods forward
- **Senkou Span B (Leading Span B)**: `(52-period high + 52-period low) / 2` shifted 26 periods forward
- **Chikou Span (Lagging Span)**: Current closing price shifted 26 periods backward

#### Cloud (Kumo)
The area between Senkou Span A and Senkou Span B forms the "cloud" which represents:
- **Support/Resistance levels**
- **Trend direction** (A > B = bullish cloud, A < B = bearish cloud)
- **Market momentum**

### 2. Wilder's ADX (Average Directional Index)

ADX measures the strength of a trend without indicating direction.

#### Components
- **True Range (TR)**: Maximum of:
  - High - Low
  - |High - Previous Close|
  - |Low - Previous Close|

- **Directional Movement**:
  - **+DM**: Positive when (High - Previous High) > (Previous Low - Low) and > 0
  - **-DM**: Positive when (Previous Low - Low) > (High - Previous High) and > 0

- **Smoothed Values** (using Wilder's smoothing):
  - **+DI**: 100 × (Smoothed +DM / Smoothed TR)
  - **-DI**: 100 × (Smoothed -DM / Smoothed TR)
  - **DX**: 100 × |(+DI - -DI) / (+DI + -DI)|
  - **ADX**: Smoothed DX

#### ADX Interpretation
- **ADX < 20**: Weak trend, sideways market
- **ADX 20-25**: Emerging trend
- **ADX 25-40**: Strong trend
- **ADX > 40**: Very strong trend

## Signal Patterns

The algorithm generates 10 distinct signal patterns, each designed for specific market conditions:

### Pattern 0: Price Crosses Senkou A
**Logic**: Direct price interaction with the leading cloud boundary
- **Buy Signal**: Price crosses above Senkou A + ADX ≥ 25
- **Sell Signal**: Price crosses below Senkou A + ADX ≥ 25
- **Use Case**: Strong trend confirmation signals

### Pattern 1: Tenkan/Kijun Crossover
**Logic**: Fast line crosses slow line (momentum shift)
- **Buy Signal**: Tenkan crosses above Kijun + ADX ≥ 20
- **Sell Signal**: Tenkan crosses below Kijun + ADX ≥ 20
- **Use Case**: Early trend change detection

### Pattern 2: Senkou A/B Crossover
**Logic**: Cloud color change (future support/resistance shift)
- **Buy Signal**: Senkou A crosses above Senkou B + ADX ≥ 25
- **Sell Signal**: Senkou A crosses below Senkou B + ADX ≥ 25
- **Use Case**: Long-term trend direction changes

### Pattern 3: Bounce off Senkou A + DI Filter
**Logic**: Price bounces from cloud boundary with directional confirmation
- **Buy Signal**: Price bounces up from Senkou A + +DI > -DI + ADX ≥ 25
- **Sell Signal**: Price bounces down from Senkou A + +DI < -DI + ADX ≥ 25
- **Use Case**: Support/resistance level confirmations

### Pattern 4: Chikou vs Senkou A
**Logic**: Historical price momentum vs current cloud
- **Buy Signal**: Chikou > Senkou A + ADX ≥ 25
- **Sell Signal**: Chikou < Senkou A + ADX ≥ 25
- **Use Case**: Momentum confirmation signals

### Pattern 5: Bounce off Tenkan + DI
**Logic**: Price bounces from conversion line with directional filter
- **Buy Signal**: Price bounces up from Tenkan + +DI > -DI + ADX ≥ 25
- **Sell Signal**: Price bounces down from Tenkan + +DI < -DI + ADX ≥ 25
- **Use Case**: Short-term momentum plays

### Pattern 6: Price Crosses Kijun + DI
**Logic**: Price crosses base line with directional confirmation
- **Buy Signal**: Price crosses above Kijun + +DI > -DI + ADX ≥ 25
- **Sell Signal**: Price crosses below Kijun + +DI < -DI + ADX ≥ 25
- **Use Case**: Medium-term trend entries

### Pattern 7: Bounce off Senkou B + Cloud Check
**Logic**: Price bounces from cloud boundary with color confirmation
- **Buy Signal**: Price bounces up from Senkou B + Bullish Cloud + ADX ≥ 20
- **Sell Signal**: Price bounces down from Senkou B + Bearish Cloud + ADX ≥ 20
- **Use Case**: Strong support/resistance confirmations

### Pattern 8: Price Above/Below Cloud
**Logic**: Price position relative to entire cloud
- **Buy Signal**: Price above cloud + Bullish Cloud + ADX ≥ 25
- **Sell Signal**: Price below cloud + Bearish Cloud + ADX ≥ 25
- **Use Case**: Strong trend following signals

### Pattern 9: Chikou vs Price + Cloud
**Logic**: Historical momentum with current cloud context
- **Buy Signal**: Chikou > Senkou A + Bullish Cloud + ADX ≥ 25
- **Sell Signal**: Chikou < Senkou A + Bearish Cloud + ADX ≥ 25
- **Use Case**: Comprehensive momentum analysis

## Data Requirements

### Input Data Format
The algorithm expects minute-level OHLC data with the following columns:
```python
Required columns:
- datetime: Timestamp with timezone information
- open: Opening price
- high: Highest price
- low: Lowest price
- close: Closing price
- closest_expiry: Nearest options expiry date (optional)
```

### Data Source
- **Database**: ClickHouse database with minute-level spot data
- **Symbol**: NIFTY index
- **Timeframe**: 1-minute intervals
- **Period**: 2021 onwards (configurable)

### Data Quality Requirements
- **Completeness**: Minimal gaps in time series
- **Accuracy**: Clean OHLC data without anomalies
- **Volume**: Sufficient historical data for indicator calculations (minimum 52 periods)

## Installation and Setup

### Prerequisites
- Python 3.8 or higher
- ClickHouse database with market data
- Jupyter Notebook environment

### Environment Setup

1. **Clone the Repository**:
```bash
git clone <repository-url>
cd Ichimoku-ADX-Wilder
```

2. **Create Virtual Environment**:
```bash
python -m venv venv3.8
source venv3.8/bin/activate  # On Windows: venv3.8\Scripts\activate
```

3. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

4. **Environment Variables**:
Create a `.env` file in the root directory:
```
CLICKHOUSE_HOST=your_clickhouse_host
CLICKHOUSE_port=your_clickhouse_port
CLICKHOUSE_USER=your_username
CLICKHOUSE_PASSWORD=your_password
```

### Required Python Packages
```
pandas>=1.5.0
numpy>=1.21.0
clickhouse-connect>=0.5.0
talib>=0.4.0
python-dotenv>=0.19.0
jupyter>=1.0.0
plotly>=5.0.0
dash>=2.0.0
```

## Usage Guide

### Basic Usage

1. **Start Jupyter Notebook**:
```bash
jupyter notebook
```

2. **Open Signal Generator**:
Navigate to `backtesting/signal_genetator.ipynb`

3. **Run Signal Generation**:
```python
# Load and prepare data
df = client.query_df(query)

# Generate all signals
df_with_signals = generate_signals(df)

# Check signal patterns
signal_columns = [col for col in df_with_signals.columns if col.startswith('pattern_')]
print(df_with_signals[signal_columns].sum())
```

### Custom Signal Generation

```python
# Generate signals with custom parameters
df_signals = generate_signals(df)

# Filter for specific patterns
strong_signals = df_signals[
    (df_signals['pattern_0'] != 0) |
    (df_signals['pattern_8'] != 0)
]

# Analyze signal frequency
for i in range(10):
    pattern_col = f'pattern_{i}'
    buy_signals = (df_signals[pattern_col] == 1).sum()
    sell_signals = (df_signals[pattern_col] == -1).sum()
    print(f"Pattern {i}: {buy_signals} buys, {sell_signals} sells")
```

### Dashboard Monitoring

1. **Start Dashboard**:
```bash
cd dashboard/algoDashboard
python app.py
```

2. **Access Interface**:
Open browser to `http://localhost:8050`

## Algorithm Logic

### Signal Processing Flow

```
1. Data Ingestion
   ↓
2. Ichimoku Calculation
   ↓
3. ADX Calculation
   ↓
4. Signal Pattern Evaluation
   ↓
5. Signal Aggregation
   ↓
6. Output Generation
```

### Decision Matrix

Each signal pattern follows this evaluation structure:

```python
def pattern_logic(conditions_buy, conditions_sell, adx_threshold):
    signals = np.zeros(len(df))
    
    # Buy conditions
    buy_mask = conditions_buy & (adx >= adx_threshold)
    signals[buy_mask] = 1
    
    # Sell conditions  
    sell_mask = conditions_sell & (adx >= adx_threshold)
    signals[sell_mask] = -1
    
    return signals
```

### ADX Filtering

All patterns incorporate ADX filtering to ensure signals occur during trending markets:
- **Minimum ADX 20**: For sensitive patterns (1, 7)
- **Minimum ADX 25**: For most patterns (0, 2, 3, 4, 5, 6, 8, 9)

### Signal Encoding
- **+1**: Buy signal
- **-1**: Sell signal
- **0**: Hold/No signal

## Performance Considerations

### Computational Complexity
- **Time Complexity**: O(n) for each indicator calculation
- **Space Complexity**: O(n) for storing historical data and indicators
- **Bottlenecks**: Rolling window calculations and data retrieval

### Optimization Tips

1. **Data Preprocessing**:
```python
# Pre-calculate rolling windows
df['high_roll_max'] = df['high'].rolling(window=52).max()
df['low_roll_min'] = df['low'].rolling(window=52).min()
```

2. **Vectorization**:
```python
# Use numpy vectorized operations
conditions = (df['close'] > df['senkou_a']) & (df['adx'] >= 25)
```

3. **Memory Management**:
```python
# Process data in chunks for large datasets
chunk_size = 10000
for chunk in pd.read_sql(query, chunksize=chunk_size):
    signals = generate_signals(chunk)
```

### Scaling Considerations
- **Multi-symbol Support**: Parallel processing for multiple instruments
- **Real-time Processing**: Streaming data integration
- **Historical Analysis**: Efficient data storage and retrieval

## Troubleshooting

### Common Issues

#### 1. Column Name Mismatch
**Error**: `KeyError: 'High'`
**Solution**: Ensure DataFrame columns use lowercase names ('high', 'low', 'close')

#### 2. Insufficient Data
**Error**: Rolling window calculations fail
**Solution**: Ensure minimum 52 periods of historical data

#### 3. Database Connection Issues
**Error**: `clickhouse_connect.driver.exceptions.DatabaseError`
**Solution**: Verify environment variables and database connectivity

#### 4. Memory Issues with Large Datasets
**Error**: `MemoryError`
**Solution**: Process data in smaller chunks or increase system memory

### Debugging Tips

1. **Check Data Quality**:
```python
# Verify data completeness
print(f"Data shape: {df.shape}")
print(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")
print(f"Missing values: {df.isnull().sum()}")
```

2. **Validate Indicators**:
```python
# Check indicator calculations
indicators = ['tenkan_sen', 'kijun_sen', 'senkou_a', 'senkou_b', 'adx']
for indicator in indicators:
    print(f"{indicator}: {df[indicator].describe()}")
```

3. **Signal Verification**:
```python
# Analyze signal distribution
for i in range(10):
    pattern = f'pattern_{i}'
    signal_counts = df[pattern].value_counts()
    print(f"{pattern}: {signal_counts}")
```

### Performance Monitoring

```python
import time

# Monitor execution time
start_time = time.time()
df_signals = generate_signals(df)
execution_time = time.time() - start_time
print(f"Signal generation completed in {execution_time:.2f} seconds")

# Monitor memory usage
import psutil
memory_usage = psutil.Process().memory_info().rss / 1024 / 1024
print(f"Memory usage: {memory_usage:.2f} MB")
```

## Advanced Features

### Custom Pattern Development

To add new signal patterns:

1. **Define Pattern Logic**:
```python
def custom_pattern(df, adx_threshold=25):
    # Your custom logic here
    buy_condition = (df['custom_indicator'] > df['threshold'])
    sell_condition = (df['custom_indicator'] < df['threshold'])
    
    return enc(
        buy_condition & (df['adx'] >= adx_threshold),
        sell_condition & (df['adx'] >= adx_threshold)
    )
```

2. **Integrate with Main Function**:
```python
def generate_signals(df):
    # ... existing code ...
    signals['custom_pattern'] = custom_pattern(df)
    # ... rest of function ...
```

### Multi-Timeframe Analysis

```python
def multi_timeframe_signals(df, timeframes=['5T', '15T', '1H']):
    """Generate signals across multiple timeframes"""
    signals_dict = {}
    
    for tf in timeframes:
        df_resampled = df.resample(tf, on='datetime').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min', 
            'close': 'last'
        })
        
        signals_dict[tf] = generate_signals(df_resampled)
    
    return signals_dict
```

### Signal Consensus

```python
def signal_consensus(df_signals, patterns=None, threshold=0.6):
    """Generate consensus signals from multiple patterns"""
    if patterns is None:
        patterns = [f'pattern_{i}' for i in range(10)]
    
    # Calculate consensus
    buy_votes = sum(df_signals[p] == 1 for p in patterns)
    sell_votes = sum(df_signals[p] == -1 for p in patterns)
    
    consensus = np.zeros(len(df_signals))
    consensus[buy_votes >= len(patterns) * threshold] = 1
    consensus[sell_votes >= len(patterns) * threshold] = -1
    
    return consensus
```

---

## License

This project is licensed under the Apache License. See LICENSE file for details.

## Contributing

Contributions are welcome! Please read the contributing guidelines and submit pull requests for any improvements.

## Support

For technical support or questions about the algorithm:
1. Check this documentation
2. Review the troubleshooting section
3. Open an issue in the repository
4. Contact the development team

---

*Last updated: July 2025*
