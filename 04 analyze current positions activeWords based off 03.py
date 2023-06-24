import pandas as pd

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
                    word_trends[word].append(trend)
                else:
                    word_trends[word] = [trend]

# Calculate the mean trend for each word
word_mean_trends = {
    word: sum(trends) / len(trends)
    for word, trends in word_trends.items()
}

# Function to calculate the score for a position
def calculate_score(position):
    ticker = position['ticker']
    active_words = position['activeWords']
    total_score = 0
    
    for word in active_words:
        if word in word_mean_trends:
            mean_trend = word_mean_trends[word]
            # Normalize the mean trend to a score between 0 and 100
            score = (mean_trend - min(word_mean_trends.values())) / (max(word_mean_trends.values()) - min(word_mean_trends.values())) * 100
            total_score += score
    
    return total_score

# Example usage
data_url = 'http://38.108.119.159:3000/cur-p'
positions = pd.read_json(data_url)

print(positions)

# Calculate and print the scores for each position
for index, position in positions.iterrows():
    ticker = position['ticker']
    score = calculate_score(position)
    print(f"Ticker: {ticker}, Score: {score}")

# Determine the desired minimum profitability or any other criteria for buying
desired_profitability = 20  # Set the desired minimum profitability in percentage

# Calculate the minimum score threshold based on the desired profitability
threshold_score = float('-inf')  # Initialize the threshold score with a very low value

for word, mean_trend in word_mean_trends.items():
    if mean_trend > 0:
        score = (mean_trend - min(word_mean_trends.values())) / (
            max(word_mean_trends.values()) - min(word_mean_trends.values())
        ) * 100
        if score >= desired_profitability:
            threshold_score = max(threshold_score, score)

# Output the threshold score
print(f"The minimum score threshold for buying positions with a desired profitability of {desired_profitability}% is: {threshold_score}")