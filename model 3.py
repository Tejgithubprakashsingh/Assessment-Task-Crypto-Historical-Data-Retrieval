import pandas as pd
import requests
from datetime import datetime
import numpy as np

def fetch_crypto_data(crypto_pair, start_date, api_key):
    # Parse the crypto_pair
    coin, currency = crypto_pair.split('/')
    
    # Convert start_date to a datetime object and calculate the number of days since start_date
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    days = (datetime.now() - start_date_obj).days
    
    # CryptoCompare endpoint for historical daily data
    url = f"https://min-api.cryptocompare.com/data/v2/histoday"
    
    # Define parameters for the API request
    params = {
        'fsym': coin.upper(),
        'tsym': currency.upper(),
        'limit': days,  # Number of days since start_date
        'toTs': int(datetime.now().timestamp()),  # To current date
        'api_key': api_key
    }
    
    # Fetch data from CryptoCompare API
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        raise Exception(f"Error fetching data: {response.status_code}, {response.text}")
    
    # Parse JSON data
    data = response.json()['Data']['Data']
    
    # Convert the data to a DataFrame
    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['time'], unit='s')
    
    # Select required columns and rename
    df = df[['Date', 'open', 'high', 'low', 'close']]
    df.columns = ['Date', 'Open', 'High', 'Low', 'Close']
    
    # Filter data from the specified start_date
    df = df[df['Date'] >= start_date]
    
    return df


def calculate_metrics(data, variable1, variable2):
    # Ensure 'Date' is the index to facilitate look-back/forward calculations
    data = data.set_index('Date').sort_index()
    
    # Historical High and Low calculations over the past {variable1} days
    data[f'High_Last_{variable1}_Days'] = data['High'].rolling(window=variable1, min_periods=1).max()
    data[f'Low_Last_{variable1}_Days'] = data['Low'].rolling(window=variable1, min_periods=1).min()
    
    # Calculate Days Since High and Low
    data[f'Days_Since_High_Last_{variable1}_Days'] = data.apply(
        lambda row: (row.name - data.loc[data['High'] == row[f'High_Last_{variable1}_Days']].index[-1]).days 
        if row[f'High_Last_{variable1}_Days'] in data['High'].values else np.nan, axis=1
    )
    
    data[f'Days_Since_Low_Last_{variable1}_Days'] = data.apply(
        lambda row: (row.name - data.loc[data['Low'] == row[f'Low_Last_{variable1}_Days']].index[-1]).days 
        if row[f'Low_Last_{variable1}_Days'] in data['Low'].values else np.nan, axis=1
    )

    # Percentage Differences from Historical High and Low
    data[f'%_Diff_From_High_Last_{variable1}_Days'] = (
        (data['Close'] - data[f'High_Last_{variable1}_Days']) / data[f'High_Last_{variable1}_Days'] * 100
    )
    data[f'%_Diff_From_Low_Last_{variable1}_Days'] = (
        (data['Close'] - data[f'Low_Last_{variable1}_Days']) / data[f'Low_Last_{variable1}_Days'] * 100
    )
    
    # Future High and Low calculations over the next {variable2} days
    data[f'High_Next_{variable2}_Days'] = data['High'].shift(-variable2).rolling(window=variable2, min_periods=1).max()
    data[f'Low_Next_{variable2}_Days'] = data['Low'].shift(-variable2).rolling(window=variable2, min_periods=1).min()
    
    # Percentage Differences from Future High and Low
    data[f'%_Diff_From_High_Next_{variable2}_Days'] = (
        (data['Close'] - data[f'High_Next_{variable2}_Days']) / data[f'High_Next_{variable2}_Days'] * 100
    )
    data[f'%_Diff_From_Low_Next_{variable2}_Days'] = (
        (data['Close'] - data[f'Low_Next_{variable2}_Days']) / data[f'Low_Next_{variable2}_Days'] * 100
    )

    # Reset the index to keep 'Date' as a column
    data = data.reset_index()
    
    return data

# Example usage:
# Example usage (replace 'YOUR_API_KEY' with your actual CryptoCompare API key)
api_key = "123d0d4d92c39b8718008f333cc712003f1ab8150795e6e1bfd5b6259350ba1b"
df = fetch_crypto_data("BTC/USD", "2023-01-01", api_key)
# print(df)

# Assuming `df` is the DataFrame with historical crypto data
variable1 = 7   # Look-back period in days
variable2 = 5   # Look-forward period in days
result_df = calculate_metrics(df, variable1, variable2)
print(result_df)