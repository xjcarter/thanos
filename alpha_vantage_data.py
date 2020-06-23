from alpha_vantage.timeseries import TimeSeries
import pandas
import os.path

# standard functions to grab and save ticker data from alpha_advantange
# pip install alpha-vantage
# look at alpha_advantange_data_test.py for example usage

# fetch data for a symbol
# mode='full' = full available data set 
# mode='compact' = most current data (last 100 days) 

COMPACT = 'compact'
FULL = 'full'
 
def fetch_data(symbol, mode=FULL):

    ts = TimeSeries(key='WQOAD0XM0NKFICV2', output_format='pandas')
    data, meta_data = ts.get_daily_adjusted(symbol=symbol,outputsize=mode)
    print('fetching ' + symbol + '...')
    data = data.reset_index()
    data.columns = "date,open,high,low,close,adjusted_close,volume,dividend_amount,split_coefficient".split(",")
    return data, meta_data


def cvt_timestamp(ts):
    if isinstance(ts,str):
        return ts
    return ts.strftime("%Y-%m-%d")

# takes a current file built by this library and concats the new data

def update_data(symbol, csv_history_file):

    h, new_df = None, None
    

    fetch_mode = COMPACT 

    try:
        if os.path.isfile(csv_history_file): 
            h = pandas.read_csv(csv_history_file)
        else:
            # grab new data
            fetch_mode = FULL 
    except:
        print(f'ERROR: could not read {csv_history_file}.')
        return 

    try:
        new_data, _ = fetch_data(symbol, mode=fetch_mode)
        new_data['date'] = new_data['date'].map(cvt_timestamp)
    except Exception as e:
        print(f'ERROR: could not fetch new data for {symbol}.')
        print(e)
        return 

    try:
        if h is not None:
            new_df = pandas.concat([h,new_data])
            new_df = new_df.sort_values(by=['date'],ascending=[1])
            new_df = new_df.drop_duplicates(['date'],keep='last')
        else:
            new_df = new_data.sort_values(by=['date'],ascending=[1])
    except:
        print(f'ERROR: merge for {symbol} to {csv_history_file} failed.')
        return

    new_df = new_df.reset_index(drop=True)

    try:
        if h is not None:
            h.to_csv(f'{csv_history_file}.prev',index=False)
        new_df.to_csv(csv_history_file,index=False)
    except:
        print(f'ERROR: update to {csv_history_file} failed.')
        return

    return new_df



if __name__ == "__main__":
    fetch_mode = FULL 
    data, meta = fetch_data('SPY',fetch_mode)

    print(data.tail(5))
    print(f'spy_{fetch_mode}.csv written.')
    data.to_csv(f'spy_{fetch_mode}.csv',index=False)

