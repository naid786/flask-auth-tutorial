import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from tqdm import tqdm
import yfinance as yf

def get_all_yfinance_tickers():
    """
    Scrapes tickers for all major asset classes from Yahoo Finance including:
    - Stocks
    - Cryptocurrencies
    - Commodities
    - Indices
    - Currency exchange rates
    Returns a DataFrame with symbols, names, and asset classes.
    """
    # Configuration
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    base_url = "https://finance.yahoo.com"
    delay = 1  # seconds between requests
    
    # Enhanced asset class configurations
    asset_classes = {
        'stocks': {
            'urls': [
                '/most-active', '/gainers', '/losers',
                '/trending-tickers', '/active-equities'
            ],
            'suffix': '',
            'table_id': 'yfin-list-table'
        },
        'crypto': {
            'urls': ['/cryptocurrencies'],
            'suffix': '-USD',
            'table_id': 'yfin-list-table'
        },
        'commodities': {
            'urls': ['/commodities'],
            'suffix': '=F',
            'table_id': 'yfin-list-table'
        },
        'indices': {
            'urls': ['/world-indices'],
            'suffix': '',
            'table_id': 'yfin-list-table'
        },
        'currencies': {
            'urls': ['/currencies'],
            'suffix': '',
            'table_id': 'yfin-list-table',
            'special_processing': True
        }
    }
    
    all_tickers = []
    
    for asset_class, config in asset_classes.items():
        for endpoint in config['urls']:
            url = f"{base_url}{endpoint}"
            try:
                print(f"\nScraping {asset_class} from {url}...")
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Handle currency pairs differently
                # if asset_class == 'currencies':
                #     # Currency pairs are in a different structure
                #     currency_pairs = soup.find_all('a', {'class': 'Fw(600)'})
                #     for pair in tqdm(currency_pairs, desc="Processing currencies"):
                #         symbol = pair.text.strip()
                #         name = symbol.replace('=X', '') + ' Exchange Rate'
                #         all_tickers.append({
                #             'Symbol': symbol,
                #             'Name': name,
                #             'Asset Class': 'Currency'
                #         })
                #     continue
                
                # Standard table processing for other asset classes
                table = soup.find('table', {'data-test': config['table_id']})
                if not table:
                    table = soup.find('table')  # fallback
                
                if table:
                    rows = table.find_all('tr')[1:]  # Skip header row
                    for row in tqdm(rows, desc=f"Processing {asset_class}"):
                        cols = row.find_all('td')
                        if len(cols) > 1:
                            symbol = cols[0].text.strip()
                            name = cols[1].text.strip() if len(cols) > 1 else ''
                            
                            # Add appropriate suffix if needed
                            if config['suffix'] and not symbol.endswith(config['suffix']):
                                symbol += config['suffix']
                            
                            all_tickers.append({
                                'Symbol': symbol,
                                'Name': name,
                                'Asset Class': asset_class.capitalize()
                            })
                
                time.sleep(delay)
                
            except Exception as e:
                print(f"Error scraping {url}: {str(e)}")
                continue
    
    # Add known important tickers that might be missed
    additional_tickers = [
        # Major currency pairs
        {'Symbol': 'EURUSD=X', 'Name': 'EUR/USD Exchange Rate', 'Asset Class': 'Currency'},
        {'Symbol': 'GBPUSD=X', 'Name': 'GBP/USD Exchange Rate', 'Asset Class': 'Currency'},
        {'Symbol': 'USDJPY=X', 'Name': 'USD/JPY Exchange Rate', 'Asset Class': 'Currency'},
        {'Symbol': 'AUDUSD=X', 'Name': 'AUD/USD Exchange Rate', 'Asset Class': 'Currency'},
        {'Symbol': 'USDCAD=X', 'Name': 'USD/CAD Exchange Rate', 'Asset Class': 'Currency'},
        
        # Major indices
        {'Symbol': '^GSPC', 'Name': 'S&P 500', 'Asset Class': 'Indices'},
        {'Symbol': '^DJI', 'Name': 'Dow Jones Industrial Average', 'Asset Class': 'Indices'},
        {'Symbol': '^IXIC', 'Name': 'NASDAQ Composite', 'Asset Class': 'Indices'},
        
        # Key commodities
        {'Symbol': 'CL=F', 'Name': 'Crude Oil Futures', 'Asset Class': 'Commodities'},
        {'Symbol': 'GC=F', 'Name': 'Gold Futures', 'Asset Class': 'Commodities'},
        {'Symbol': 'SI=F', 'Name': 'Silver Futures', 'Asset Class': 'Commodities'},
        {'Symbol': 'NG=F', 'Name': 'Natural Gas Futures', 'Asset Class': 'Commodities'},
        
        # Popular crypto
        {'Symbol': 'BTC-USD', 'Name': 'Bitcoin USD', 'Asset Class': 'Crypto'},
        {'Symbol': 'ETH-USD', 'Name': 'Ethereum USD', 'Asset Class': 'Crypto'},
    ]
    
    # Create DataFrame and clean data
    df = pd.DataFrame(all_tickers + additional_tickers)
    
    # Remove duplicates (keeping first occurrence)
    df = df.drop_duplicates(subset=['Symbol'], keep='first')
    
    # Add exchange information where available
    def extract_exchange(symbol):
        if '=X' in symbol:
            return 'FOREX'
        elif '=F' in symbol:
            return 'Futures'
        elif '-' in symbol and not symbol.startswith('^'):
            return 'Crypto'
        elif '.' in symbol:
            return symbol.split('.')[-1]
        elif symbol.startswith('^'):
            return 'Index'
        return 'Unknown'
    
    df['Exchange'] = df['Symbol'].apply(extract_exchange)
    
    # Clean up asset class names
    df['Asset Class'] = df['Asset Class'].replace({
        'Stocks': 'Equities',
        'Crypto': 'Cryptocurrency',
        'Commodities': 'Commodity',
        'Indices': 'Index',
        'Currencies': 'Currency'
    })
    
    return df.sort_values(by=['Asset Class', 'Symbol']).reset_index(drop=True)

    def get_historical_data(symbol, start_date, end_date):
        """
        Fetches historical OHLC (Open, High, Low, Close) data for a given symbol
        from Yahoo Finance using yfinance library.

        Parameters:
        - symbol (str): The ticker symbol of the asset.
        - start_date (str): The start date in the format 'YYYY-MM-DD'.
        - end_date (str): The end date in the format 'YYYY-MM-DD'.

        Returns:
        - DataFrame: A pandas DataFrame containing the historical OHLC data.
        """
        try:
            print(f"Fetching historical data for {symbol} from {start_date} to {end_date}...")
            data = yf.download(symbol, start=start_date, end=end_date)
            if data.empty:
                print(f"No data found for {symbol} in the given date range.")
                return pd.DataFrame()
            return data
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {str(e)}")
            return pd.DataFrame()

def get_historical_data(symbol, start_date, end_date,interval='1h'):
    """
    Fetches historical OHLC (Open, High, Low, Close) data for a given symbol
    from Yahoo Finance using yfinance library.

    Parameters:
    - symbol (str): The ticker symbol of the asset.
    - start_date (str): The start date in the format 'YYYY-MM-DD'.
    - end_date (str): The end date in the format 'YYYY-MM-DD'.

    Returns:
    - DataFrame: A pandas DataFrame containing the historical OHLC data.
    """
    try:
        print(f"Fetching historical data for {symbol} from {start_date} to {end_date}...")
        data = yf.download(symbol, start=start_date, end=end_date, interval=interval)
        if data.empty:
            print(f"No data found for {symbol} in the given date range.")
            return pd.DataFrame()
        return data
    except Exception as e:
        print(f"Error fetching historical data for {symbol}: {str(e)}")
        return pd.DataFrame()
