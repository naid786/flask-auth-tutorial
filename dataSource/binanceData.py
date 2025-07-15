import requests
import pandas as pd
from datetime import datetime, timedelta

def get_all_binance_symbols():
    """
    Fetches all available trading symbols from Binance API and returns them in a structured format.
    Returns a list of dictionaries with keys: Symbol, Name, Exchange
    """
    try:
        # Binance API endpoint for exchange information
        url = "https://api.binance.com/api/v3/exchangeInfo"
        
        # Make the GET request
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse the JSON response
        data = response.json()
        
        # Create structured data
        symbols_data = [
            {
                "Symbol": symbol['symbol'],
                "Name": symbol['symbol'],
                "Asset Class": "Binance"
            }
            for symbol in data['symbols']
            if symbol['status'] == 'TRADING'  # Only include active symbols
        ]
        
        # Convert to DataFrame
        df = pd.DataFrame(symbols_data)
        
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Binance API: {e}")
        return []
    
def fetch_binance_ohlc(symbol, start_date, end_date, interval='15m'):
    """
    Fetch OHLC data from Binance API for a given symbol and date range
    
    Parameters:
        symbol (str): Trading pair symbol (e.g., 'BTCUSDT')
        start_date (str/datetime): Start date in format 'YYYY-MM-DD' or datetime object
        end_date (str/datetime): End date in format 'YYYY-MM-DD' or datetime object
        interval (str): Kline interval (default '1d' - 1 day)
                       Options: '1m', '5m', '15m', '30m', '1h', '2h', '4h', 
                                '6h', '8h', '12h', '1d', '3d', '1w', '1M'
    
    Returns:
        pd.DataFrame: DataFrame with OHLC data and volume
    """
    # Convert dates to timestamp in milliseconds
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    start_ts = int(start_date.timestamp() * 1000)
    end_ts = int(end_date.timestamp() * 1000)
    
    base_url = "https://api.binance.com/api/v3/klines"
    all_data = []
    
    current_start = start_ts
    max_records_per_request = 1000  # Binance's limit
    
    try:
        while current_start < end_ts:
            # Calculate end timestamp for this batch
            current_end = min(current_start + max_records_per_request * get_interval_ms(interval), end_ts)
            
            params = {
                'symbol': symbol,
                'interval': interval,
                'startTime': current_start,
                'endTime': current_end,
                'limit': max_records_per_request
            }
            
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                break
                
            all_data.extend(data)
            
            # Move window forward
            current_start = int(data[-1][0]) + get_interval_ms(interval)
            
        # Process the data into a DataFrame
        columns = [
            'time', 'Open', 'High', 'Low', 'Close', 'Volume',
            'Close time', 'Quote asset volume', 'Number of trades',
            'Taker buy base volume', 'Taker buy quote volume', 'Ignore'
        ]
        
        df = pd.DataFrame(all_data, columns=columns)
        
        # Convert timestamp to datetime
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        df['Close time'] = pd.to_datetime(df['Close time'], unit='ms')
        
        # Convert strings to numeric values
        numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, axis=1)
        
        # Filter only the relevant columns
        df = df[['time', 'Open', 'High', 'Low', 'Close', 'Volume']]
        
        return df
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching OHLC data: {e}")
        return pd.DataFrame()

def get_interval_ms(interval):
    """Convert interval string to milliseconds"""
    unit = interval[-1]
    value = int(interval[:-1])
    
    if unit == 'm':
        return value * 60 * 1000
    elif unit == 'h':
        return value * 60 * 60 * 1000
    elif unit == 'd':
        return value * 24 * 60 * 60 * 1000
    elif unit == 'w':
        return value * 7 * 24 * 60 * 60 * 1000
    elif unit == 'M':
        return value * 30 * 24 * 60 * 60 * 1000  # Approximate
    else:
        return 0
    