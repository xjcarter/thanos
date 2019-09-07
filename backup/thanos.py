
## STOCK DEVATION TRACKER 
## Tracks the tails in the devation of price from the 200dayMA
## Charts the 50day and 200day views of price versus the 200dayMA
## Sends an email when the deviation has moved beyond the 15% or 85% percentile (on z-score)

import mail_client

import math
import pandas
import numpy as np
import seaborn as sns
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import scipy.stats as st
import sys, time
import alpha_vantage_data as avd

sns.set()

## universe file for all symbols monitored
## one symbol per line

HOME = '/Users/jamescarter/sandbox/thanos'
UNIVERSE_FILE = f'{HOME}/universe.txt'
THANOS_DATA = f'{HOME}/thanos_data/'
THANOS_CHARTS = f'{HOME}/thanos_charts/'

## table formating
HEADER_STYLE = r'<th style="padding-top: 10px; padding-bottom: 8px; color: #D8D8D8;" align="center" bgcolor="#2F4F4F">'
ROW_STYLE = r'<td style="padding: 8px 8px 6px; border: 1px solid #4f6228; font-size: 12">'

EMAIL_HEADER = """

    This is a simple tracker of the current price deviation to the ma200 

    Where:

      Deviation = log( [price - ma200]/ma200 )
      Zscore    = [Current Deviation - 100dayAverage(Deviation)] / 100daySTDEV(Deviation)
    
    Downside Tails ( prob < 0.15 ): Signal good long term entry points
    Upside Tails   ( prob > 0.85 ): Signal good points to secure profits (take off % of current longs OR seek options as hedge)

"""

 
def get_data(symbol):

    data = None 
    try:
        hist_file = THANOS_DATA + f'thanos_{symbol}.csv'
        data = avd.update_data(symbol,hist_file)
    except:
        pass
         
    return data 


def plot(symbol, dts, a, b):

    current_date = dts.iloc[-1]

    for i,N in enumerate([50, 200],1):

        dates = dts.tail(N)
        s1 = a.tail(N)
        s2 = b.tail(N)

        plt.subplot(1,2,i)
        plt.title("%s %s: %d days" % (symbol,current_date,N))

        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m_%d'))
        u = [dt.datetime.strptime(d,'%Y-%m-%d').date() for d in dates.tolist()]

        plt.plot(u, s1)
        plt.plot(u, s2)

        plt.gcf().autofmt_xdate()
    
    return plt
    

def email_alert(symbol,df,low_bound,high_bound):

    ## check for a significant deviation within the last 5 days
    ## if so - send an email!!

    snapshot = df.tail(5)
    vals = snapshot['prob'].tolist()
    hi_val, low_val = max(vals), min(vals)
    if low_val < low_bound or hi_val > high_bound:
        ffmt = "{:,.4f}".format
        table = snapshot.to_html(float_format=ffmt)
        table = table.replace('<th>',HEADER_STYLE)
        table = table.replace('<td>',ROW_STYLE)

        subj = f'{symbol} Deviation!!!'
        chart_file = THANOS_CHARTS + f'thanos_{symbol}.png'
        mail_client.mail('xjcarter@gmail.com',subj,text=EMAIL_HEADER,html=table,attach=chart_file)
        #mail_client.mail('xjcarter@gmail.com',subj,text=EMAIL_HEADER,html=table)
        
       
def get_universe():

    univ = [line.strip() for line in open(UNIVERSE_FILE)]
    return univ


def thanosize(symbol,df):

    CLOSE = 'close'
    #CLOSE = 'adjusted_close'

    ## calc ma200

    df['ma200'] = df[CLOSE].rolling(200).mean()

    ## current deviation from moving average 

    df['dev'] = (df[CLOSE]/df['ma200']).map(math.log)

    ## calc Zscore

    df['z_score'] = (df['dev'] - df['dev'].rolling(100).mean())/df['dev'].rolling(100).std()
    df['prob'] = df['z_score'].map(st.norm.cdf)

    zz = df[['date',CLOSE,'ma200','dev','z_score','prob']]
    zfile = THANOS_DATA + f'thanos_{symbol}_ztest.csv'
    zz.to_csv(zfile,index=False)

    ## save the chart and clear it.
    chart_file = THANOS_CHARTS + f'thanos_{symbol}.png'
    chart = plot(symbol,zz.date,zz[CLOSE],zz.ma200)
    chart.savefig(chart_file)

    return zz,chart


def evaluate(symbol):
    df = get_data(symbol) 
    if df is None:
        print(f'ERROR: {symbol} data fetch error.')
        return

    zz, chart = thanosize(symbol,df)

    print(zz.tail(10))
    chart.show()


def monitor_universe():

    for symbol in get_universe():

        df = get_data(symbol) 
        if df is None:
            print(f'ERROR: {symbol} data fetch error.')
            return

        zz, chart = thanosize(symbol,df)
        chart.clf()

        email_alert(symbol,zz,0.15,0.85)


if __name__ == "__main__":

    ## usage: python thanos.py <optional symbol>
    ##        if no symbol given - does monitoring on all the names the universe file thanos.csv
    ##        with a symbol given - does all the analytics, dumps the output and chart the data

    if len(sys.argv) > 1:
        symbol = sys.argv[1]
        print(f'running thanos on: {symbol}') 
        evaluate(symbol)
    else:
        monitor_universe() 
