import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime
# from utils.url_builder import build_url

# Example usage
def remove_outliers(trends, threshold=40):
    return [t for t in trends if abs(t) <= threshold]


stdin_payload = sys.stdin.read()

# Parse the positions JSON
input_json = json.loads(stdin_payload)
current_ticker_recs = input_json['currentTickerRecs']
all_ticker_recs = input_json['allTickerRecs']


# Convert closed_positions list to DataFrame
all_ticker_recs = pd.DataFrame(all_ticker_recs)

# Remove rows with NaN 'pickPriceToOpeningPriceNextDay' values
all_ticker_recs = all_ticker_recs.dropna(subset=['pickPriceToOpeningPriceNextDay'])

# Create a dictionary to store the words and their corresponding trends
word_trends = {}

# Iterate over each data entry
for index, entry in all_ticker_recs.iterrows():
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
# for index, (word, mean_trend, percent_positive, trend_count, score) in enumerate(sorted_words):
#     print(f'Index: {index}, Word: {word}, Mean Trend: {round(mean_trend, 2)}, Percentage of Positive Trends: {round(percent_positive)}%, Trend Count: {trend_count}, Score: {score}')
    
# print('-' * 50)


def scoreWords(words):
    overall_score = 0
    for word, mean_trend, percent_positive, trend_count, score in sorted_words:
        if word in active_words:
            overall_score += score
    return overall_score

# Analyze the performance based on the sorted_words for the words in activeWords in recent_rows
for entry in current_ticker_recs:
    entry['pythonScore'] = scoreWords(entry['activeWords'])

output_json = json.dumps(current_ticker_recs)
print(output_json)