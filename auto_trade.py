import pandas as pd
import numpy as np
import datetime
import MetaTrader5 as mt5
import time
import logging

#Library to generate technical indicators
import talib
from talib import RSI, EMA, MACD, SMA
from logging.handlers import RotatingFileHandler


path = "C:\\Program Files\\MetaTrader\\terminal64.exe"
symbol = "XAUUSD"
lot = 0.05 
logname = 'C:\\Scripts\\rsi_mon2.log'
handler = RotatingFileHandler(logname, maxBytes=10*1024*1024, backupCount=1)
handler.setLevel(logging.INFO)
log = logging.getLogger('main')
log.setLevel(logging.INFO)
log.addHandler(handler)

# Get the Data
if not mt5.initialize(path=path):
    print ("Failed to initail MT5, error {}".format(mt5.last_error()))
    exit()

def monitor_ordered():
    print ("check ordered")
    positions = mt5.positions_get(group=symbol)
    if positions==None:
        print("No positions with group=\"*USD*\", error code={}".format(mt5.last_error()))
        return False    
    elif len(positions)>0:
        df=pd.DataFrame(list(positions),columns=positions[0]._asdict().keys())
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.drop(['time_update', 'time_msc', 'time_update_msc', 'external_id'],
                axis=1, inplace=True)

        #print (df)
        if len(df) >=5:
            return True
        else:
            return False 


def get_rate_frame():
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 500)
    rates_frame = pd.DataFrame(rates)
    rates_frame['time']=pd.to_datetime(rates_frame['time'], unit='s')
    return rates_frame

def get_rsi():
    rates_frame = get_rate_frame()
    close = np.array(rates_frame['close'])
    rsi_ind = RSI(close, timeperiod=9)
    sma = SMA(close, timeperiod=9)
    array_length = len(rsi_ind)
    last_element = rsi_ind[- 1]
    last_rsi = last_element
    log.info("Rsi {}".format(last_rsi))
    print("sma {}".format(sma[-1]))
    return float(last_rsi)
        
def get_macd():
    rates_frame = get_rate_frame()
    close = np.array(rates_frame['close'])
    ema = EMA(close, 5) - EMA(close, 21)
    macd, macdsignal, macdhist = MACD(close, fastperiod=5, slowperiod=26, signalperiod=1)
    log.info("macd {}, signal {} ema {}".format(macd[-1], macdsignal[-1], ema[-1]))
    if ema[-1] > 1: #macdsignal[-1]:
        return macdsignal[-1], macd[-1], "BUY"
    elif ema[-1] < 1: #macdsignal[-1]:
        return macdsignal[-1], macd[-1], "SELL"

def get_lvar():
    rates_frame = get_rate_frame()
    rates_frame['variation'] = rates_frame['close'] - rates_frame['open']
    variations = rates_frame['variation']
    l_var = variations[99]
    print("lvar {}".format(l_var))


deviation = 20
#Decission Taking and Send Order

while True:
    signal, macd, status = get_macd()
    get_lvar()
    rate = mt5.symbol_info_tick(symbol).ask
    rsi = get_rsi()
    print ("current rate {} vs signal {}".format(rate, signal))
    if 0.1 > macd > -1 and 40 > rsi > 29 and (float(signal) > float(rate)):
        price = mt5.symbol_info_tick(symbol).bid
        request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot,
                "type": mt5.ORDER_TYPE_SELL,
                "price": price,
                #"sl": price + 2.0,
                "tp": price - 0.5,
                "deviation": deviation,
                "magic": 202003,
                "comment": "Bot Sell",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC}
        if not monitor_ordered():
            print('SELL AT 0.01')
            result = mt5.order_send(request)
            result = mt5.order_send(request)
            print (result) 
            log.info(result)
    if macd > 0.4 and 60 < rsi and (float(rate) > float(signal)):
        price = mt5.symbol_info_tick(symbol).ask
        request = {
               "action": mt5.TRADE_ACTION_DEAL,
               "symbol": symbol,
               "volume": lot,
               "type": mt5.ORDER_TYPE_BUY,
               "price": price,
               #"sl": price - 2.0,
               "tp": price + 0.5,
               "deviation": deviation,
               "magic": 202003,
               "comment": "Bot Buy",
               "type_time": mt5.ORDER_TIME_GTC,
               "type_filling": mt5.ORDER_FILLING_IOC}
        if not monitor_ordered():
            print('But At 0.1')
            result = mt5.order_send(request)
            result = mt5.order_send(request)
            print(result)
            log.info(result)
    time.sleep(60)
