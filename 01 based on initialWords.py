import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import requests
import numpy as np

# Load the data from the URL
url = 'http://38.108.119.159:3000/closed-positions'
data = requests.get(url).json()

# Convert the JSON data into a DataFrame
df = pd.DataFrame(data)

# Remove rows with NaN 'sellReturnPerc' values
df = df.dropna(subset=['sellReturnPerc'])

# Lower case all the words
df['initialWords'] = df['initialWords'].apply(lambda words: [word.lower() for word in words])

# Filter out rows where 'initialWords' contain the term "relative"
df = df[~df['initialWords'].apply(lambda words: any('relative' in word for word in words))]

df['initialWords'] = df['initialWords'].apply(' '.join)

# Create a TfidfVectorizer object
vectorizer = TfidfVectorizer()

# Fit and transform the 'initialWords'
X = vectorizer.fit_transform(df['initialWords']).toarray()

# Get target variable
y = df['sellReturnPerc'].values

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Create Random Forest Regressor model
rf_model = RandomForestRegressor(random_state=42)

# Fit the model
rf_model.fit(X_train, y_train)

# Get feature importances
importances = rf_model.feature_importances_

# Map importances to the corresponding words
feature_to_importance = {
    word: importance
    for word, importance in zip(vectorizer.get_feature_names_out(), importances)
}

# Sort the words according to their importance
sorted_features = sorted(feature_to_importance.items(), key=lambda x: x[1], reverse=True)

# Print the sorted words along with their importance
for word, importance in sorted_features:
    print(f'{word}: {importance}')
