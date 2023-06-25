import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from scipy.stats import pearsonr
import numpy as np

from utils.url_builder import build_url

# Load the data from the URL
data = pd.read_json(build_url('/closed-positions'))

# Remove rows with NaN 'sellReturnPerc' values
data = data.dropna(subset=['sellReturnPerc'])

# Lowercase all the words
data['interestingWords'] = data['interestingWords'].apply(lambda words: [word.lower() for word in words])

# Filter out rows where 'interestingWords' contain the term "relative"
data = data[~data['interestingWords'].apply(lambda words: any('relative' in word for word in words))]

# Convert the list of words to string
data['interestingWords'] = data['interestingWords'].apply(' '.join)

# Create a TfidfVectorizer object
vectorizer = TfidfVectorizer()

# Fit and transform the 'interestingWords'
X = vectorizer.fit_transform(data['interestingWords'])

# Get target variable
y = data['sellReturnPerc']

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Calculate correlation coefficients between features and target variable
correlations = []
for i in range(X_train.shape[1]):
    corr, _ = pearsonr(X_train[:, i].toarray().flatten(), y_train)
    correlations.append(corr)

# Get feature names
feature_names = vectorizer.get_feature_names_out()

# Create a DataFrame to store feature correlations
feature_correlations = pd.DataFrame({'Word': feature_names, 'Correlation': correlations})

# Sort the words according to their correlation coefficients in descending order
sorted_features = feature_correlations.sort_values('Correlation', ascending=False)

# Print the top words with positive correlation
top_n = 10  # Define the number of top words to print
positive_correlated_words = sorted_features[sorted_features['Correlation'] > 0].head(top_n)
print("Top words with positive correlation to sellReturnPerc:")
print(positive_correlated_words)