"""
Data fetcher for intraday OHLCV data from multiple sources
Supports NIFTYBEES.NS, DIXON.NS and other NSE stocks
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class IntradayDataFetcher:
    """Fetch and prepare intraday data for backtesting"""
    
    def __init__(self, symbol, start_date, end_date):
        """
        Initialize data fetcher
        
        Args:
            symbol: Stock symbol (e.g., 'NIFTYBEES.NS', 'DIXON.NS')
            start_date: Start date (datetime or string)
            end_date: End date (datetime or string)
        """
        self.symbol = symbol
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        
    def fetch_intraday_data(self, interval='5m'):
        """
        Fetch intraday data from yfinance
        
        Args:
            interval: Data interval ('1m', '5m', '15m', '30m', '60m')
            
        Returns:
            DataFrame: OHLCV data with datetime index
        """
        print(f"Fetching {interval} data for {self.symbol}...")
        
        # yfinance has limitations on historical intraday data
        # It only provides last ~60 days for minute data
        # For longer history, we need to fetch in chunks or use daily data
        
        all_data = []
        current_date = self.end_date
        
        # Fetch in 60-day chunks (yfinance limitation)
        while current_date > self.start_date:
            chunk_start = max(current_date - timedelta(days=59), self.start_date)
            
            try:
                data = yf.download(
                    self.symbol,
                    start=chunk_start.strftime('%Y-%m-%d'),
                    end=current_date.strftime('%Y-%m-%d'),
                    interval=interval,
                    progress=False,
                    auto_adjust=True
                )
                
                if not data.empty:
                    all_data.append(data)
                    print(f"  Fetched {len(data)} bars from {chunk_start.date()} to {current_date.date()}")
            except Exception as e:
                print(f"  Warning: Failed to fetch data for {chunk_start.date()} to {current_date.date()}: {e}")
            
            current_date = chunk_start - timedelta(days=1)
        
        if not all_data:
            print(f"Warning: No intraday data available for {self.symbol}.")
            print(f"Falling back to daily data and simulating intraday bars...")
            return self._simulate_intraday_from_daily(interval)
        
        # Combine all chunks
        data = pd.concat(all_data)
        data = data.sort_index()
        
        # Standardize column names
        data.columns = [c.capitalize() if not isinstance(c, tuple) else c[0].capitalize() 
                       for c in data.columns]
        
        # Keep only OHLCV columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        data = data[[col for col in required_cols if col in data.columns]]
        
        # Remove duplicates and NaN
        data = data[~data.index.duplicated(keep='first')]
        data = data.dropna()
        
        print(f"Total {len(data)} bars loaded for {self.symbol}")
        
        return data
    
    def _simulate_intraday_from_daily(self, interval='5m'):
        """
        Simulate intraday bars from daily data when intraday is not available
        This is a fallback method with disclosed assumptions
        
        Args:
            interval: Target interval
            
        Returns:
            DataFrame: Simulated intraday OHLCV data
        """
        print(f"Simulating {interval} intraday data from daily bars...")
        
        # Fetch daily data
        daily_data = yf.download(
            self.symbol,
            start=self.start_date.strftime('%Y-%m-%d'),
            end=self.end_date.strftime('%Y-%m-%d'),
            progress=False,
            auto_adjust=True
        )
        
        if daily_data.empty:
            raise ValueError(f"No data available for {self.symbol}")
        
        # Standardize column names
        daily_data.columns = [c.capitalize() if not isinstance(c, tuple) else c[0].capitalize() 
                             for c in daily_data.columns]
        
        # Calculate number of bars per day based on interval
        interval_minutes = int(interval.replace('m', ''))
        trading_minutes = 375  # 9:15 AM to 3:30 PM = 375 minutes
        bars_per_day = trading_minutes // interval_minutes
        
        intraday_data = []
        
        for date, row in daily_data.iterrows():
            # Simulate intraday bars using random walk with realistic constraints
            daily_open = row['Open']
            daily_high = row['High']
            daily_low = row['Low']
            daily_close = row['Close']
            daily_volume = row['Volume']
            
            # Calculate daily volatility
            daily_range = daily_high - daily_low
            intraday_vol = daily_range / daily_open
            
            # Generate intraday prices
            prices = self._generate_intraday_prices(
                daily_open, daily_high, daily_low, daily_close,
                bars_per_day, intraday_vol
            )
            
            # Generate timestamps
            base_time = pd.Timestamp(date).replace(hour=9, minute=15)
            timestamps = [base_time + timedelta(minutes=i*interval_minutes) 
                         for i in range(bars_per_day)]
            
            # Create OHLCV bars
            for i in range(bars_per_day):
                bar_start = i * len(prices) // bars_per_day
                bar_end = (i + 1) * len(prices) // bars_per_day
                bar_prices = prices[bar_start:bar_end]
                
                if len(bar_prices) == 0:
                    continue
                
                bar = {
                    'Open': bar_prices[0],
                    'High': max(bar_prices),
                    'Low': min(bar_prices),
                    'Close': bar_prices[-1],
                    'Volume': daily_volume / bars_per_day
                }
                
                intraday_data.append((timestamps[i], bar))
        
        # Create DataFrame
        df = pd.DataFrame([bar for _, bar in intraday_data],
                         index=[ts for ts, _ in intraday_data])
        
        print(f"Simulated {len(df)} intraday bars")
        print("Note: This is simulated data based on daily OHLC. Results are approximations.")
        
        return df
    
    def _generate_intraday_prices(self, open_p, high_p, low_p, close_p, bars, volatility):
        """
        Generate realistic intraday price series
        
        Args:
            open_p: Daily open
            high_p: Daily high
            low_p: Daily low
            close_p: Daily close
            bars: Number of bars to generate
            volatility: Intraday volatility
            
        Returns:
            list: Price series
        """
        # Create a path from open to close that touches high and low
        n_points = bars * 10  # More points for smoother interpolation
        
        # Random walk with mean reversion
        returns = np.random.normal(0, volatility / np.sqrt(n_points), n_points)
        prices = [open_p]
        
        for ret in returns:
            next_price = prices[-1] * (1 + ret)
            # Constrain within daily range
            next_price = max(low_p, min(high_p, next_price))
            prices.append(next_price)
        
        # Ensure we hit high and low
        high_idx = np.random.randint(n_points // 4, 3 * n_points // 4)
        low_idx = np.random.randint(n_points // 4, 3 * n_points // 4)
        prices[high_idx] = high_p
        prices[low_idx] = low_p
        
        # Adjust to close at daily close
        prices[-1] = close_p
        
        return prices
    
    def add_time_features(self, data):
        """
        Add time-based features to the data
        
        Args:
            data: DataFrame with datetime index
            
        Returns:
            DataFrame: Data with additional time features
        """
        data = data.copy()
        data['hour'] = data.index.hour
        data['minute'] = data.index.minute
        data['day_of_week'] = data.index.dayofweek
        
        # Market session (opening, mid-session, closing)
        data['session'] = 'mid'
        data.loc[data['hour'] == 9, 'session'] = 'opening'
        data.loc[(data['hour'] == 15) & (data['minute'] >= 15), 'session'] = 'closing'
        
        return data
    
    @staticmethod
    def resample_timeframe(data, target_interval):
        """
        Resample intraday data to different timeframe
        
        Args:
            data: DataFrame with OHLCV data
            target_interval: Target interval (e.g., '15T' for 15 minutes)
            
        Returns:
            DataFrame: Resampled data
        """
        resampled = data.resample(target_interval).agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
        
        return resampled
