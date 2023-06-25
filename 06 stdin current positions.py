import sys
import json
import pandas as pd
from utils.url_builder import build_url

def scale_score(score, top_words_included, bottom_words_included):
    scaling_factor = 0.5
    word_length_effect = scaling_factor * (len(top_words_included) - len(bottom_words_included))
    return score + max(word_length_effect * score, -score / 1.5)

def calculate_score_for_words(words, all_trends):
    total_score = 0
    total_trends = 0
    top_words_included = []
    bottom_words_included = []

    for word in words:
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
    avg_score = total_score / total_trends if total_trends != 0 else 0  # Ternary operator to handle division by zero
    scaled_total_score = scale_score(total_score, top_words_included, bottom_words_included)
    scaled_avg_score = scale_score(avg_score, top_words_included, bottom_words_included)

    # Round them all
    avg_score = round(avg_score)
    scaled_avg_score = round(scaled_avg_score)
    total_score = round(total_score)
    scaled_total_score = round(scaled_total_score)

    return {
        'avgScore': avg_score,
        'scaledAvgScore': scaled_avg_score,
        'totalScore': total_score,
        'scaledTotalScore': scaled_total_score,
        'topWordsIncluded': top_words_included,
        'bottomWordsIncluded': bottom_words_included
    }

# Function to calculate the score for a position
def analyze_position(position, all_trends):
    word_categories = ['activeWords', 'interestingWords', 'initialWords']
    word_analysis = {category: {} for category in word_categories}

    for category in word_categories:
        words = position.get(category, [])
        if words:
            analysis = calculate_score_for_words(words, all_trends)
            word_analysis[category] = analysis

    # Filter categories that have analysis results
    valid_categories = [category for category, analysis in word_analysis.items() if analysis]

    # Calculate overall average and unique concatenation for valid categories
    overall_avg_score = round(sum(word_analysis[category]['avgScore'] for category in valid_categories) / len(valid_categories))
    overall_scaled_avg_score = round(sum(word_analysis[category]['scaledAvgScore'] for category in valid_categories) / len(valid_categories))
    overall_total_score = sum(word_analysis[category]['totalScore'] for category in valid_categories)
    overall_scaled_total_score = sum(word_analysis[category]['scaledTotalScore'] for category in valid_categories)
    overall_top_words_included = list(set(word for category in valid_categories for word in word_analysis[category]['topWordsIncluded']))
    overall_bottom_words_included = list(set(word for category in valid_categories for word in word_analysis[category]['bottomWordsIncluded']))

    # Add overall analysis to the word_analysis dictionary
    word_analysis['overall'] = {
        'avgScore': overall_avg_score,
        'scaledAvgScore': overall_scaled_avg_score,
        'totalScore': overall_total_score,
        'scaledTotalScore': overall_scaled_total_score,
        'topWordsIncluded': overall_top_words_included,
        'bottomWordsIncluded': overall_bottom_words_included
    }

    return word_analysis

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
position_analysis = []
for position in positions:
    ticker = position['ticker']
    analysis = analyze_position(position, all_trends)
    position_analysis.append({'ticker': ticker, **dict(analysis)})

# Output the scores and top 10 trends as JSON
output = {'positionAnalysis': position_analysis, 'topTrends': top_trends, 'bottomTrends': bottom_trends, 'wordCount': len(word_mean_trends)}
output_json = json.dumps(output)
print(output_json)