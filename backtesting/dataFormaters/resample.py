import pandas as pd

def resample(df, freq='5T'):
    
    """
    Resample the DataFrame to a specified frequency.
    
    Parameters:
    df (pd.DataFrame): DataFrame with datetime index and OHLC columns.
    freq (str): Frequency to resample to (e.g., '5T','10T','1D').
    
    Returns:
    pd.DataFrame: Resampled DataFrame.
    """
    frequency= freq.upper()

    df['datetime'] = pd.to_datetime(df['datetime'])
    df.set_index('datetime', inplace=True)
    df = df.resample(frequency).agg({'open': 'first',
                                        'high': 'max', 
                                        'low': 'min', 
                                        'close': 'last', 
                                        "closest_expiry":'last'}).dropna()
    df.reset_index('datetime', inplace=True)
    return df