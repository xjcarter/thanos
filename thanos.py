
##t STOCK DEVATION TRACKER 
## Tracks the tails in the devation of price from the 200dayMA
## Charts the 50day and 200day views of price versus the 200dayMA
## Sends an email when the deviation has moved beyond the 15% or 85% percentile (on z-score)

## 06/23/2020
## modified the script to take a universe file on a string of stocks at the commmand line
## it also creates a composite file that gives all the current metrics fro the universe being analyzed.
## Usage:  python3 thanos.py <universe_file OR 'sym1,sym2,sym3'> <tag to save the file>
##         i.e.  python3 thanos.py new_universe.txt ./composites/new_univ ## composite saved to ./composites/new_univ_{date}.csv
##               python3 thanos.py 'IVV,SPY,IAU'  ## dataframes just dumped to stdout
##               python3 thanos.py 'IVV,SPY,AAPL' ./composites/mylist ## composites saved to ./composites/mylist_{date}.csv


import mail_client

import math, datetime
import pandas
import pathlib
import numpy as np
import seaborn as sns
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import scipy.stats as st
import os, sys, time
import alpha_vantage_data as avd

sns.set()

## universe file for all symbols monitored
## one symbol per line

HOME = '/home/jcarter/sandbox/trading/thanos'
UNIVERSE_FILE = f'{HOME}/universe.txt'
THANOS_DATA = f'{HOME}/thanos_data/'
THANOS_CHARTS = f'{HOME}/thanos_charts/'
THANOS_LOG = f'{HOME}/thanos_data/thanos_log.csv'      
       

## table formating
HEADER_STYLE = r'<th style="padding-top: 10px; padding-bottom: 8px; color: #D8D8D8;" align="center" bgcolor="#2F4F4F">'
ROW_STYLE = r'<td style="padding: 8px 8px 6px; border: 1px solid #4f6228; font-size: 12">'

EMAIL_HEADER = """

    This is a simple tracker of the current price deviation to the ma200 

    Where:

      Deviation = log( price/ma200 )
      Zscore    = [Current Deviation - 100dayAverage(Deviation)] / 100daySTDEV(Deviation)
    
    Downside Tails ( prob < 0.15 ): Signal good long term entry points
    Upside Tails   ( prob > 0.85 ): Signal good points to secure profits (take off % of current longs OR seek options as hedge)

"""


 
def get_data(symbol):
    
    ## sleep between data calls - only allowed 5 calls per minute and 500 calls per day.
    time.sleep(13)

    data = None 
    try:
        hist_file = THANOS_DATA + f'thanos_{symbol}.csv'
        data = avd.update_data(symbol,hist_file)
    except:
        pass
         
    return data 

def cvt_date(date_obj):
    if isinstance(date_obj, basestring):
        return dt.datetime.strptime(date_obj,"%Y-%m-%d").date()
    else:
        return date_obj.date()

def plot(symbol, dts, a, b):

    return None 

    current_date = dts.iloc[-1]

    for i,N in enumerate([50, 200],1):

        dates = dts.tail(N)
        s1 = a.tail(N)
        s2 = b.tail(N)

        plt.subplot(1,2,i)
        plt.title("%s %s: %d days" % (symbol,current_date,N))

        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m_%d'))
        #u = [dt.datetime.strptime(d,'%Y-%m-%d').date() for d in dates.tolist()]
        u = [cvt_date(d) for d in dates.tolist()]

        plt.plot(u, s1)
        plt.plot(u, s2)

        plt.gcf().autofmt_xdate()
    
    return plt
    

def send_alert(symbol,df,low_bound,high_bound):

    ## check for a significant deviation within the last 5 days
    ## if so - send an email!!


    snapshot = df.tail(5)
    current_stats = df.tail(1).iloc[0].apply(str).tolist()
    
    # initilaize log file if one does not exist 
    if not os.path.isfile(THANOS_LOG):
        with open(THANOS_LOG,'w') as f:
            header = df.columns.tolist() + ['symbol','ext']
            f.write(",".join(header)+"\n")


    vals = snapshot['prob'].tolist()
    hi_val, low_val = max(vals), min(vals)
    if low_val < low_bound or hi_val > high_bound:
        hi_idx = low_idx = -1 
        if hi_val > high_bound: hi_idx = vals.index(hi_val)
        if low_val < low_bound: low_idx = vals.index(low_val)
        side = 'BOTTOM' if low_idx > hi_idx else 'TOP'

        ffmt = "{:,.4f}".format
        table = snapshot.to_html(float_format=ffmt)
        table = table.replace('<th>',HEADER_STYLE)
        table = table.replace('<td>',ROW_STYLE)

        subj = f'{symbol} {side} Deviation!!!'
        chart_file = THANOS_CHARTS + f'thanos_{symbol}.png'
        mail_client.mail('xjcarter@gmail.com',subj,text=EMAIL_HEADER,html=table,attach=chart_file)
        #mail_client.mail('xjcarter@gmail.com',subj,text=EMAIL_HEADER,html=table)

        todays_prob = float(current_stats[-1])  
        if todays_prob < low_bound or todays_prob > high_bound:
            current_stats.append(symbol)

            # flag extension type
            side = 'BOTTOM'
            if todays_prob > high_bound:
                side = 'TOP' 
            current_stats.append(side)
                
            outs = ",".join(current_stats)
            with open(THANOS_LOG,'a') as f:
                f.write(outs + '\n')
        

def send_heartbeat(uni):

    def modification_date(filename):
        t = os.path.getmtime(filename)
        return dt.datetime.fromtimestamp(t)


    uni_list = "\nUniverse:\n" + "\n".join(uni)
    
    now = dt.datetime.now()

    try:
        most_recent = modification_date(THANOS_LOG)
        delta = (now - most_recent).days
        if delta > 0 and delta % 5 == 0:
            message = f'Most recent update = {most_recent} ({delta} days)\n' + uni_list 
            mail_client.mail('xjcarter@gmail.com','THANOS Heartbeat!',text=message)
    except:
        mail_client.mail('xjcarter@gmail.com','THANOS Heartbeat FAILURE! Check Process!',text=uni_list)


def get_universe(universe_fn):

    univ = [line.strip() for line in open(universe_fn)]
    return univ


def thanosize(symbol,df,show_charts=False):

    CLOSE = 'close'
    #CLOSE = 'adjusted_close'

    ## calc ma200

    df['ma200'] = df[CLOSE].rolling(200).mean()

    ## current deviation from moving average 

    df['dev'] = (df[CLOSE]/df['ma200']).map(math.log)

    ## calc Zscore

    df['z_score'] = (df['dev'] - df['dev'].rolling(100).mean())/df['dev'].rolling(100).std()
    df['prob'] = df['z_score'].map(st.norm.cdf)

    """
    df['prev'] = df['close'].shift(1)
    df['tr'] = df.apply(lambda x: max(x['high'] - x['low'],x['high']-x['prev'],x['prev']-x['low']),axis=1)
    df['atr'] = df['tr'].rolling(20).mean()

    df['low20'] = df['low'].rolling(20).min()
    df['stopATRs'] = (df['high'] - df['low20'])/df['atr']
    df['threeATRs'] = 3 * df['atr']
    zz = df[['date',CLOSE,'ma200','dev','z_score','prob','atr','low20','stopATRs','threeATRs']]
    """

    zz = df[['date',CLOSE,'ma200','dev','z_score','prob']]
    zfile = THANOS_DATA + f'thanos_{symbol}_ztest.csv'
    zz.to_csv(zfile,index=False)

    ## save the chart and clear it.
    chart = None
    if show_charts:
        chart_file = THANOS_CHARTS + f'thanos_{symbol}.png'
        chart = plot(symbol,zz.date,zz[CLOSE],zz.ma200)
        if chart is not None: chart.savefig(chart_file)

    return zz,chart


def evaluate(symbol):

    tagged = chart = None
    try:
        df = get_data(symbol) 

        if df is None:
            print(f'ERROR: {symbol} data fetch error.')
            return

        zz, chart = thanosize(symbol,df)
        
        ## tag each dataframe with the symbol evaluated 
        tagged = zz.copy()
        tagged['symbol'] = symbol
    except:
        print(f'ERROR: Failed to analyze {symbol}.')
        

    return tagged, chart


## created to do passive / email based monitoring

def monitor_universe(universe_fn):

    uni = get_universe(universe_fn) 
    for symbol in uni:

        df = get_data(symbol) 
        if df is None:
            print(f'ERROR: {symbol} data fetch error.')
        else:
            zz, chart = thanosize(symbol,df)
            if chart is not None: chart.clf()
            # send_alert(symbol,zz,0.15,0.85)

    # send heartbeat every 5 days since last update  
    # send_heartbeat(uni)



if __name__ == "__main__":

    ## usage: python thanos.py <optional symbol>
    ##        if no symbol given - does monitoring on all the names the universe file thanos.csv
    ##        with a symbol given - does all the analytics, dumps the output and chart the data

    symbol_list = None
    composite = list() 
    header = None
    if len(sys.argv) > 1:
        ## use a universe file
        if pathlib.Path(sys.argv[1]).is_file():
            symbol_list = get_universe(sys.argv[1])
        else:
        ## or use commna separated string
            symbol_list = sys.argv[1].split(',')

        for symbol in symbol_list:
            print(f'running thanos on: {symbol}') 
            metrics, chart = evaluate(symbol)
    
            if metrics is not None:
                if header is None: header = metrics.columns
                print(metrics.tail(10))

                if len(composite) < 500:
                    ## alpha_vantage FREE service limits you to 500 calls a day.
                    composite.append(metrics.iloc[-1].tolist())
                else:
                    print('cannot append {symbol} - 500 symbol data retrieval limit exceeded')

            #if chart is not None: chart.show()


        comp_df = pandas.DataFrame(columns=header,data=composite)
        comp_df['Composite'] = True
        comp_df = comp_df.sort_values(['z_score'])

        print("\nComposite Table:")
        print(comp_df)

        if comp_df is not None:
            ## save composite file to the desired directory
            destination= './'
            if len(sys.argv) > 2: destination = sys.argv[2] + "/" 
            curr_date = datetime.datetime.now().date().strftime("%Y%m%d")
            if not pathlib.Path(destination).exists():
                import os
                os.makedirs(destination)
            current_comp_file = f'{destination}{curr_date}.csv'
            comp_df.to_csv(current_comp_file,index=False)
