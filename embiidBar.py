import pandas as pd
import matplotlib.pyplot as plt

# Load data from an Excel file
excel_file = 'word_frequencies.xlsx'  # Replace with your actual file name
df = pd.read_excel(excel_file)

# Display the data (optional)
print(df)

# Assuming the Excel file has columns 'Word' and 'Frequency'
words = df['Word']
frequencies = df['Frequency']

# Create the bar chart
plt.figure(figsize=(12, 8))
plt.bar(words, frequencies, color='skyblue')

# Add titles and labels
plt.title('Word Frequency in NBA Reddit Posts')
plt.xlabel('Words')
plt.ylabel('Frequency')
plt.xticks(rotation=90)  # Rotate x-axis labels for better readability

# Show the plot
plt.tight_layout()  # Adjust layout to fit x-axis labels
plt.show()
