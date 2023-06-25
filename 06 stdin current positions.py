import sys
import json
import pandas as pd

def scale_score(score, top_words_included, bottom_words_included):
    scaling_factor = 0.5
    word_length_effect = scaling_factor * (len(top_words_included) - len(bottom_words_included))
    return score + max(word_length_effect * score, -score / 1.5)

# Function to calculate the score for a position
def calculate_score(position, all_trends):
    ticker = position['ticker']
    active_words = position['activeWords']
    total_score = 0
    total_trends = 0
    top_words_included = []
    bottom_words_included = []

    for word in active_words:
        for trend in all_trends:
            if word == trend['word']:
                score = trend['score']
                total_score += score
                total_trends += 1
                if trend in top_trends:
                    top_words_included.append(word)
                elif trend in bottom_trends:
                    bottom_words_included.append(word)

    # Calculate avg and scaled scores
    avg_score = total_score / total_trends
    scaled_total_score = scale_score(total_score, top_words_included, bottom_words_included)
    scaled_avg_score = scale_score(avg_score, top_words_included, bottom_words_included)

    # Round them all
    avg_score = round(avg_score)
    scaled_avg_score = round(scaled_avg_score)
    total_score = round(total_score)
    scaled_total_score = round(scaled_total_score)

    return avg_score, scaled_avg_score, total_score, scaled_total_score, top_words_included, bottom_words_included

# Load the data from the URL
data_url = 'http://38.108.119.159:3000/closed-positions'
data = pd.read_json(data_url)

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

# Calculate the mean trend for each word
word_mean_trends = {
    word: sum(trend for trend, _ in trends) / len(trends)
    for word, trends in word_trends_filtered.items()
}

# Read the positions JSON from stdin
positions_json = sys.stdin.read()

# Parse the positions JSON
positions = json.loads(positions_json)

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

# Get the top 10 and bottom 10 word_mean_trends
top_trends = all_trends[:15]
bottom_trends = all_trends[-15:]

# Calculate and store the scores and topWordsIncluded for each position
positionScores = []
for position in positions:
    ticker = position['ticker']
    avg_score, scaled_avg_score, total_score, scaled_total_score, top_words_included, bottom_words_included = calculate_score(position, all_trends)
    positionScores.append({'ticker': ticker, 'avgScore': avg_score, 'totalScore': total_score, 'scaledAvgScore': scaled_avg_score, 'scaledTotalScore': scaled_total_score, 'topWordsIncluded': top_words_included, 'bottomWordsIncluded': bottom_words_included})

# Output the scores and top 10 trends as JSON
output = {'positionScores': positionScores, 'topTrends': top_trends, 'bottomTrends': bottom_trends, 'wordCount': len(word_mean_trends)}
output_json = json.dumps(output)
print(output_json)
