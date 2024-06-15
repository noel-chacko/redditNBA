import os
import praw
import pandas as pd
from datetime import datetime, timedelta
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import certifi
from flask import Flask, request
import threading
import webbrowser
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set SSL certificates for NLTK download
os.environ['SSL_CERT_FILE'] = certifi.where()

# Reddit API credentials
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
user_agent = os.getenv('USER_AGENT')
redirect_uri = os.getenv('REDIRECT_URI')

# Initialize Flask app
app = Flask(__name__)
auth_code = None

@app.route('/')
def handle_redirect():
    global auth_code
    auth_code = request.args.get('code')
    return "Authorization code received! You can close this tab."

def run_flask():
    app.run(port=8080)

# Initialize PRAW
reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent, redirect_uri=redirect_uri)

# Fix the PRAW deprecation warning by using keyword arguments
auth_url = reddit.auth.url(scopes=['read'], state='uniqueKey', duration='permanent')
print(f'Opening the browser to authorize: {auth_url}')

# Start Flask in a separate thread
threading.Thread(target=run_flask).start()

# Open the authorization URL in the default browser
webbrowser.open(auth_url)

# Wait for the auth_code to be set
while auth_code is None:
    pass

# Exchange the authorization code for an access token
reddit.auth.authorize(auth_code)

# Download NLTK data
nltk.download('stopwords')
nltk.download('punkt')

# Get posts from the NBA subreddit from the past two weeks
subreddit = reddit.subreddit('nba')
end_date = datetime.now()
start_date = end_date - timedelta(days=14)

posts = []
for submission in subreddit.new(limit=1000):  # Adjust the limit based on your needs
    if datetime.fromtimestamp(submission.created_utc) > start_date:
        posts.append(submission.title)

# Convert to DataFrame
df = pd.DataFrame(posts, columns=['content'])

# Text processing
# Combine all posts into a single string
all_text = ' '.join(df['content'])

# Tokenize the text
tokens = word_tokenize(all_text)

# Remove stopwords and punctuation
stop_words = set(stopwords.words('english'))
tokens = [word.lower() for word in tokens if word.isalpha() and word.lower() not in stop_words]

# Count the frequency of each word
word_freq = Counter(tokens)

# Get the most common words
most_common_words = word_freq.most_common(20)
print(most_common_words)

# Visualize the results
# Generate word cloud
wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(word_freq)

# Display the word cloud
plt.figure(figsize=(10, 5))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')
plt.show()

# Create a bar chart for the most common words
words, counts = zip(*most_common_words)
plt.bar(words, counts)
plt.xlabel('Words')
plt.ylabel('Frequency')
plt.title('Most Popular Terms on NBA Reddit (Last 2 Weeks)')
plt.xticks(rotation=45)
plt.show()
