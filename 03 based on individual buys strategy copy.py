import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

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

# Sort the words according to their mean trend in descending order
sorted_words = sorted(word_mean_trends.items(), key=lambda x: x[1], reverse=True)

# Print the words and their mean trends
for word, mean_trend in sorted_words:
    print(f'Word: {word}, Mean Trend (%): {mean_trend}')