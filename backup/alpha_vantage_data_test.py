import alpha_vantage_data as avd 

def test1():

    print("\nTEST 1")

    ## create a base file 

    df, _ = avd.fetch_data('SPY','full')
    v = len(df)
    df = df.head(v - 5)
    print(f'length = {v-5}')

    df.to_csv('test_spy.csv',index=False)
    print('test_spy.csv')
    print(df.tail(5))

    ## do a second fetch and test merge of new data 

    new_df = avd.update_data('SPY','test_spy.csv')
    print('new test_spy.csv')
    v = len(new_df)
    print(f'length = {v}')
    print(new_df.tail(10))

def test2():

    print("\nTEST 2")
    ## fetch and test merge of empty file 

    new_df = avd.update_data('SPY','test_empty_spy.csv')
    print('new test_empty_spy.csv')
    v = len(new_df)
    print(f'length = {v}')
    print(new_df.tail(10))


if __name__ == "__main__":
    test1()
    test2()
