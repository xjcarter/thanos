
import pandas
import sys

"""
lists the symbols of a finviz export
"""

df = pandas.read_csv(sys.argv[1])
for symbol in df['Ticker'].tolist():
    print(symbol)

