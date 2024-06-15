import pandas as pd

# Load the Excel sheet into a DataFrame
df = pd.read_excel('word_frequencies.xlsx')

# Define the words of interest and their variations
words_of_interest = {
    'dirty': ['dirty'],
    'injury': ['injured', 'injury', 'injuries'],
    'foul': ['foul'],
    'ft': ['ft']
}

# Initialize a dictionary to store the total counts of each word group
word_counts = {key: 0 for key in words_of_interest}

# Calculate the counts for each word group
for key, variations in words_of_interest.items():
    word_counts[key] = df[df['Word'].isin(variations)]['Frequency'].sum()

# Calculate the total count of all words
total_count = df['Frequency'].sum()

# Calculate the percentage of each word group
word_percentages = {key: (count / total_count) * 100 for key, count in word_counts.items()}

# Print the results
print("Total word count:", total_count)
print("Word counts and percentages:")
for key, count in word_counts.items():
    print(f"{key.capitalize()}: {count} ({word_percentages[key]:.2f}%)")
