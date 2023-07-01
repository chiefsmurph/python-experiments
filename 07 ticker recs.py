import pandas as pd
import numpy as np
from datetime import datetime
from utils.url_builder import build_url

# Example usage
def remove_outliers(trends, threshold=40):
    return [t for t in trends if abs(t) <= threshold]

# Load the data from the URL
firstdata = pd.read_json(build_url('/ticker-recs?onlyShouldBuys'))

# Remove rows with NaN 'pickPriceToOpeningPriceNextDay' values
data = firstdata.dropna(subset=['pickPriceToOpeningPriceNextDay'])

# Create a dictionary to store the words and their corresponding trends
word_trends = {}

# Iterate over each data entry
for index, entry in data.iterrows():
    active_words = entry['activeWords']
    trend = entry['pickPriceToOpeningPriceNextDay']

    # Update the word trends dictionary, excluding words containing "relative" and filtering trends
    for word in active_words:
        if 'RELATIVE' not in word:
            if abs(trend) < 40:
                if word in word_trends:
                    word_trends[word].append(trend)
                else:
                    word_trends[word] = [trend]

# Calculate the percentage of positive trends, mean trend, count of trends, and score for each word
word_scores = []
for word, trends in word_trends.items():
    positive_trends = [t for t in trends if t > 0]
    percent_positive = (len(positive_trends) / len(trends)) * 100
    mean_trend = np.mean(trends)
    score = round(mean_trend * (percent_positive / 100), 2)
    trend_count = len(trends)
    word_scores.append((word, mean_trend, percent_positive, trend_count, score))

# Sort the words by score in descending order
sorted_words = sorted(word_scores, key=lambda x: x[4], reverse=True)

# Print the words, mean trend, percentage of positive trends, trend count, and score
for word, mean_trend, percent_positive, trend_count, score in sorted_words:
    print(f'Word: {word}, Mean Trend: {round(mean_trend, 2)}, Percentage of Positive Trends: {round(percent_positive)}%, Trend Count: {trend_count}, Score: {score}')
print('-' * 50)

# Get the ten most recent rows
recent_rows = firstdata.head(10)

# Analyze the performance based on the sorted_words for the words in activeWords in recent_rows
for index, entry in recent_rows.iterrows():
    timestamp = entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
    ticker = entry['ticker']
    active_words = entry['activeWords']
    finalZScoreSum = entry['finalZScoreSum']
    myScoreBasedOnWords = entry['myScoreBasedOnWords']

    # Print the timestamp, ticker, and activeWords
    print(f'Timestamp: {timestamp}')
    print(f'Ticker: {ticker}')
    print(f'Active Words: {active_words}')
    print(f'finalZScoreSum: {finalZScoreSum}')
    print(f'myScoreBasedOnWords: {myScoreBasedOnWords}')

    # Calculate the overall score for the recent ticker recommendation based on activeWords scores
    overall_score = 0
    for word, mean_trend, percent_positive, trend_count, score in sorted_words:
        if word in active_words:
            overall_score += score

    print(f'Overall Score: {round(overall_score, 2)}')
    print('-' * 50)
