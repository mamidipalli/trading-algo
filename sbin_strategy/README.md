# SBIN EMA/RSI Crossover Trading Strategy

This script is a trading assistant that backtests a specific long-only swing trading strategy on SBIN (State Bank of India) stock data.

## Strategy Logic

The script identifies buying opportunities based on a combination of EMA, RSI, and Volume indicators.

### Indicators Used
- **EMA (50):** 50-day Exponential Moving Average.
- **RSI (14):** 14-day Relative Strength Index.
- **Volume SMA (5):** 5-period Simple Moving Average of Volume.

### Entry Conditions
A buy signal is generated when all of the following conditions are met on a daily candle:
1. The previous candle's close was below the EMA(50).
2. The current candle's close is above the EMA(50).
3. The EMA(50) is currently rising.
4. The previous candle's RSI(14) was between 35 and 50.
5. The current candle's close is higher than the previous candle's high.
6. The current candle's volume is at least 5% greater than the 5-period Volume SMA.

### Exit Conditions
Once a trade is entered, it is exited based on one of the following conditions, whichever occurs first:
- **Stop Loss:** 1.2% below the entry price.
- **Target Profit:** 5.7% above the entry price.
- **Universal Exit:** After 7 days have passed since the entry.

## Setup and Installation

### 1. Dependencies
The script requires several Python libraries. You can install them using the provided `requirements.txt` file:
```bash
pip install -r sbin_strategy/requirements.txt
```

### 2. Historical Data
You must provide your own historical data for SBIN stock in the `SBIN_data.csv` file. The file must have the following columns: `Date,Open,High,Low,Close,Volume`.

**Important:** For the indicators to calculate correctly, you should provide at least 100 days of historical data. The script will show a warning if there is insufficient data.

### 3. Sound Alerts
The script will attempt to play `entry.wav` and `exit.wav` when trades are opened and closed. These are currently empty placeholder files. You can replace them with your own `.wav` files to enable audio alerts.

## How to Run
Once the setup is complete, you can run the backtest from your terminal:
```bash
python sbin_strategy/main.py
```
The script will load the data, run the backtest, and print a summary of all the trades it executed. The detailed trade log will be saved to `trades.csv`.
