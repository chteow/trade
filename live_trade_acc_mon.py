import pandas as pd
import MetaTrader5 as mt5
import time

path = "C:\\Program Files\\MetaTrader\\terminal64.exe"
symbol = "XAUUSD"

# Get the Data
if not mt5.initialize(path=path):
    print ("Failed to initail MT5, error {}".format(mt5.last_error()))
    exit()

while True:
    time.sleep(30)
    usd_positions=mt5.positions_get(group=symbol)
    if usd_positions==None:
        print("No positions with group=\"*USD*\", error code={}".format(mt5.last_error()))
    elif len(usd_positions)>0:
        df=pd.DataFrame(list(usd_positions),columns=usd_positions[0]._asdict().keys())
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.drop(['time_update', 'time_msc', 'time_update_msc', 'external_id',
                 'symbol', 'swap', 'magic', 'type', 'identifier', 'reason',
                 'price_open'],
                axis=1, inplace=True)
        print(df)
        """
        for profit in df["profit"].tolist():
           ticket = df.loc[df['profit'] == profit, 'ticket'].item()
           print ("Profit = {} , ticket = {}".format(profit, ticket))
           #if profit > 3.0:
           #    mt5.Close(symbol, ticket=ticket)
        """
