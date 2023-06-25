
import json
import pandas as pd
import os
import sys

import sys
sys.path.append('python-experiments/utils')  # Add the parent directory to the Python path

from url_builder import build_url

def word_trends_based_on_closed_positions():

    # Load the data from the URL
    data = pd.read_json(build_url('/closed-positions'))

    # Remove rows with NaN 'sellReturnPerc' values
    data = data.dropna(subset=['sellReturnPerc'])

    # Create a dictionary to store the words and their corresponding trends
    word_trends = {}

    # Iterate over each closed position
    for index, row in data.iterrows():
        avg_sell_price = row['avgSellPrice']
        buys = row['buys']

        # Iterate over each buy in the buys
        for buy in buys:
            fill_price = buy['fillPrice']
            strategy_words = buy['strategy'].split('-')

            # Calculate the percentage gain (trend) from buy.fillPrice to parent closed position's avgSellPrice
            trend = ((avg_sell_price - fill_price) / fill_price) * 100

            # Update the word trends dictionary, excluding words containing "relative"
            for word in strategy_words:
                if 'RELATIVE' not in word:
                    if word in word_trends:
                        word_trends[word].append((trend, row['ticker']))
                    else:
                        word_trends[word] = [(trend, row['ticker'])]

    # Filter out words with tickerCount < 4
    word_trends_filtered = {word: trends for word, trends in word_trends.items() if len(set(ticker for _, ticker in trends)) >= 4}

    # Get all word_mean_trends with score property
    all_trends = []
    for word, trends in word_trends_filtered.items():
        trendCount = len(trends)
        tickerCount = len(set(ticker for _, ticker in trends))
        avgTrend = sum(trend for trend, _ in trends) / trendCount
        percUp = sum(1 for trend, _ in trends if trend > 0) / trendCount * 100
        score = avgTrend * percUp
        all_trends.append({'word': word, 'avgTrend': avgTrend, 'percUp': percUp, 'trendCount': trendCount, 'tickerCount': tickerCount, 'score': score})

    # Sort all_trends by score in descending order
    all_trends = sorted(all_trends, key=lambda x: x['score'], reverse=True)
    return all_trends