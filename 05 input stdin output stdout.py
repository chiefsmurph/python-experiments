import sys
import json
import pandas as pd

# Function to calculate the score for a position
def calculate_score(position):
    active_words = position['activeWords']

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
                if 'relative' not in word:
                    if word in word_trends:
                        word_trends[word].append(trend)
                    else:
                        word_trends[word] = [trend]

    # Calculate the mean trend for each word
    word_mean_trends = {
        word: sum(trends) / len(trends)
        for word, trends in word_trends.items()
    }

    # Calculate the score for the active words in the position
    score = sum(word_mean_trends.get(word, 0) for word in active_words)
    
    return score

# Read the positions JSON from stdin
positions_json = sys.stdin.read()

# Parse the positions JSON
positions = json.loads(positions_json)

# Calculate and print the scores for each position
scores = []
for position in positions:
    ticker = position['ticker']
    score = calculate_score(position)
    scores.append({'ticker': ticker, 'score': score})

# Output the scores as JSON
print(json.dumps(scores))