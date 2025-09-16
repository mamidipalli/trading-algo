import pandas as pd
import ta
from playsound import playsound
import logging

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
DATA_FILE = 'sbin_strategy/SBIN_data.csv'
TRADES_FILE = 'sbin_strategy/trades.csv'
ENTRY_SOUND = 'sbin_strategy/entry.wav'
EXIT_SOUND = 'sbin_strategy/exit.wav'

# --- Strategy Parameters ---
STOP_LOSS_PCT = 1.2
TARGET_PROFIT_PCT = 5.7
UNIVERSAL_EXIT_DAYS = 7


def manage_trade(df, entry_index):
    """
    Manages a single trade from entry to exit.

    Args:
        df (pd.DataFrame): The main DataFrame.
        entry_index (int): The index of the candle that generated the entry signal.

    Returns:
        dict: A dictionary with the details of the completed trade.
        int: The index of the exit candle.
    """
    # Entry is at the open of the next candle
    trade_entry_index = entry_index + 1
    if trade_entry_index >= len(df):
        return None, entry_index # Not enough data to enter trade

    entry_price = df['Open'][trade_entry_index]
    entry_date = df['Date'][trade_entry_index]

    # Calculate SL and TP
    stop_loss_price = entry_price * (1 - STOP_LOSS_PCT / 100)
    target_profit_price = entry_price * (1 + TARGET_PROFIT_PCT / 100)

    logging.info(f"Entering trade on {entry_date.date()} at {entry_price:.2f} | TP: {target_profit_price:.2f}, SL: {stop_loss_price:.2f}")
    try:
        playsound(ENTRY_SOUND)
    except Exception as e:
        logging.warning(f"Could not play entry sound {ENTRY_SOUND}: {e}")

    exit_date = None
    exit_price = None
    result = None

    # Monitor for exit conditions from the entry candle onwards
    for i in range(trade_entry_index, len(df)):
        # Universal Exit after N days
        if (i - trade_entry_index) >= UNIVERSAL_EXIT_DAYS:
            exit_price = df['Close'][i]
            exit_date = df['Date'][i]
            logging.info(f"Universal exit triggered on {exit_date.date()} at {exit_price:.2f}")
            break

        # Check for SL hit
        if df['Low'][i] <= stop_loss_price:
            exit_price = stop_loss_price # Assume SL is hit at the exact price
            exit_date = df['Date'][i]
            logging.warning(f"Stop loss hit on {exit_date.date()} at {exit_price:.2f}")
            break

        # Check for TP hit
        if df['High'][i] >= target_profit_price:
            exit_price = target_profit_price # Assume TP is hit at the exact price
            exit_date = df['Date'][i]
            logging.info(f"Target profit hit on {exit_date.date()} at {exit_price:.2f}")
            break

    if exit_price is not None:
        try:
            playsound(EXIT_SOUND)
        except Exception as e:
            logging.warning(f"Could not play exit sound {EXIT_SOUND}: {e}")

        result = (exit_price - entry_price) / entry_price * 100
        trade = {
            'Entry_Date': entry_date,
            'Entry_Price': entry_price,
            'Exit_Date': exit_date,
            'Exit_Price': exit_price,
            'Result_Pct': result
        }
        return trade, i

    return None, entry_index # Trade did not exit within the dataset


def run_backtest(df):
    """
    Runs the backtest on the given DataFrame.

    Args:
        df (pd.DataFrame): DataFrame with data and indicators.
    """
    logging.info("--- Starting Backtest ---")
    trades = []
    i = 1 # Start from index 1 to look at previous candle
    while i < len(df):
        # --- Entry Conditions ---
        cond1 = df['Close'][i-1] < df['EMA_50'][i-1]      # Prev close < EMA50
        cond2 = df['Close'][i] > df['EMA_50'][i]          # Current close > EMA50
        cond3 = df['EMA_50'][i] > df['EMA_50'][i-1]      # EMA50 is rising
        cond4 = 35 < df['RSI_14'][i-1] < 50             # Prev RSI in range
        cond5 = df['Close'][i] > df['High'][i-1]         # Current close > Prev High
        cond6 = df['Volume'][i] > (1.05 * df['Vol_SMA_5'][i]) # Volume condition

        if all([cond1, cond2, cond3, cond4, cond5, cond6]):
            logging.info(f"Entry signal found on {df['Date'][i].date()}")
            trade, exit_index = manage_trade(df, i)
            if trade:
                trades.append(trade)
            i = exit_index + 1 # Continue searching for trades after the last one ended
        else:
            i += 1

    logging.info("--- Backtest Complete ---")

    if trades:
        trades_df = pd.DataFrame(trades)
        trades_df.to_csv(TRADES_FILE, index=False)
        logging.info(f"Saved {len(trades_df)} trades to {TRADES_FILE}")
        print("\n--- Trade Results ---")
        print(trades_df)
    else:
        logging.info("No trades were executed during the backtest.")


def load_data(filepath):
    """
    Loads historical stock data from a CSV file.

    Args:
        filepath (str): The path to the CSV file.

    Returns:
        pd.DataFrame: A DataFrame with the loaded data, or None if an error occurs.
    """
    try:
        df = pd.read_csv(filepath)
        # Basic data validation
        required_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_columns):
            logging.error(f"CSV file must contain the following columns: {required_columns}")
            return None
        df['Date'] = pd.to_datetime(df['Date'])
        logging.info(f"Successfully loaded {len(df)} rows from {filepath}")
        return df
    except FileNotFoundError:
        logging.error(f"Data file not found at {filepath}")
        return None
    except Exception as e:
        logging.error(f"An error occurred while loading data: {e}")
        return None

def calculate_indicators(df):
    """
    Calculates the required technical indicators and adds them to the DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame with historical stock data.

    Returns:
        pd.DataFrame: The DataFrame with added indicator columns.
    """
    if df is None:
        return None

    if len(df) < 50:
        logging.warning("Insufficient data for 50-period EMA. Need at least 50 data points.")
        return None

    # EMA (50)
    df['EMA_50'] = ta.trend.ema_indicator(df['Close'], window=50)

    # RSI (14)
    df['RSI_14'] = ta.momentum.rsi(df['Close'], window=14)

    # Volume SMA (5)
    df['Vol_SMA_5'] = ta.volume.sma_volume(df['Volume'], window=5)

    # Drop rows with NaN values resulting from indicator calculations
    df.dropna(inplace=True)
    df.reset_index(drop=True, inplace=True)

    logging.info("Successfully calculated technical indicators (EMA, RSI, Volume SMA).")
    return df

if __name__ == '__main__':
    logging.info("--- SBIN Trading Strategy Assistant ---")

    # 1. Load Data
    data_df = load_data(DATA_FILE)

    if data_df is not None:
        # 2. Calculate Indicators
        data_with_indicators = calculate_indicators(data_df)

        if data_with_indicators is not None:
            logging.info("Data and indicators are ready for strategy execution.")
            # In the next step, we will call the backtesting function here.
            run_backtest(data_with_indicators)
        else:
            logging.error("Failed to calculate indicators.")
    else:
        logging.error("Failed to load data. Exiting.")
