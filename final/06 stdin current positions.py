import sys
import json
import pandas as pd
from word_trends_based_on_closed_positions import word_trends_based_on_closed_positions

def scale_score(score, top_words_included, bottom_words_included):
    scaling_factor = 0.5
    word_length_effect = scaling_factor * (len(top_words_included) - len(bottom_words_included))
    return score + max(word_length_effect * score, -score / 1.5)

def calculate_score_for_words(words, all_word_trends):
    total_score = 0
    total_trends = 0
    top_words_included = []
    bottom_words_included = []

    for word in words:
        for trend in all_word_trends:
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
def analyze_position(position, all_word_trends):
    word_categories = ['activeWords', 'interestingWords', 'initialWords']
    word_analysis = {category: {} for category in word_categories}

    for category in word_categories:
        words = position.get(category, [])
        if words:
            analysis = calculate_score_for_words(words, all_word_trends)
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



stdin_payload = sys.stdin.read()

# Parse the positions JSON
input_json = json.loads(stdin_payload)
positions = input_json['positions']
closed_positions = input_json['closedPositions']


all_word_trends = word_trends_based_on_closed_positions(closed_positions)

# Get the top 10 and bottom 10 all_word_trends
top_trends = all_word_trends[:15]
bottom_trends = all_word_trends[-15:]


# Calculate and store the scores and topWordsIncluded for each position
position_analysis = []
for position in positions:
    ticker = position['ticker']
    analysis = analyze_position(position, all_word_trends)
    position_analysis.append({'ticker': ticker, **dict(analysis)})

# Output the scores and top 10 trends as JSON
output = {'positionAnalysis': position_analysis, 'topTrends': top_trends, 'bottomTrends': bottom_trends, 'wordCount': len(all_word_trends)}
output_json = json.dumps(output)
print(output_json)