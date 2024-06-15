import os
import praw
import prawcore
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
import time
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

# Define the time period for the last 2 months
end_date = datetime.now()
start_date = end_date - timedelta(days=65)

# Search for posts with "Embiid" or "Joel" in the title
posts = []
for submission in reddit.subreddit('nba').search('title:Embiid OR title:Joel', sort='new', time_filter='year', limit=None):
    if datetime.fromtimestamp(submission.created_utc) > start_date:
        posts.append(submission)

# Function to fetch the top 100 comments with rate limit handling
def fetch_comments(submission, limit=100):
    comments = []
    try:
        submission.comments.replace_more(limit=0)
        for comment in submission.comments.list()[:limit]:
            comments.append(comment.body)
    except prawcore.exceptions.TooManyRequests as e:
        print(f"Rate limit exceeded. Sleeping for {e.sleep_duration} seconds.")
        time.sleep(e.sleep_duration)
        comments.extend(fetch_comments(submission, limit))
    except prawcore.exceptions.RequestException as e:
        print(f"RequestException: {e}")
    except prawcore.exceptions.ResponseException as e:
        print(f"ResponseException: {e}")
    except prawcore.exceptions.ServerError as e:
        print(f"ServerError: {e}")
    return comments

# Process posts and fetch comments
comments = []
for submission in posts:
    print(f"Processing post: {submission.title}")
    comments.extend(fetch_comments(submission))

# Combine all comments into a single string
all_comments = ' '.join(comments)

# Tokenize the comments
tokens = word_tokenize(all_comments)

# Remove stopwords and punctuation
stop_words = set(stopwords.words('english'))
custom_stop_words = {'would', 'like', 'one', 'could', 'get', 'also', 'even', 'player', 'think', 'got', 'see', 'much', 'going', 'man', 'way', 'back', 'go', 'know', 'dude', 'right', 'say', 'well', 'guys', 'want', 'getting', 'deleted', 'take', 'need', 'yeah', 'sure', 'gon', 'let'}  # Add custom stopwords here
stop_words.update(custom_stop_words)
tokens = [word.lower() for word in tokens if word.isalpha() and word.lower() not in stop_words]

# Count the frequency of each word
word_freq = Counter(tokens)

# Print the frequency of all words
all_words = word_freq.most_common(300)  # This includes the top 300 words
print(all_words)

# Define a list of blue and red shades
colors = [
    "rgb(0, 0, 255)", "rgb(0, 0, 205)", "rgb(0, 0, 153)", "rgb(0, 0, 102)", "rgb(0, 0, 51)",  # Shades of blue
    "rgb(255, 0, 0)", "rgb(205, 0, 0)", "rgb(153, 0, 0)", "rgb(102, 0, 0)", "rgb(51, 0, 0)"   # Shades of red
]

# Define a custom color function to randomly select from the list of colors
def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    return colors[random_state.randint(0, len(colors) - 1)]

# Generate a word cloud with the custom color function
wordcloud = WordCloud(width=800, height=400, background_color='white', color_func=color_func, max_font_size=100, scale=3).generate_from_frequencies(word_freq)

# Display the word cloud
plt.figure(figsize=(10, 5))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')
plt.title('Word Cloud of Top Words in Comments on Posts with "Embiid" or "Joel" in Title (Last 2 Months)')
plt.show()

# Create a DataFrame from all words
df = pd.DataFrame(all_words, columns=['Word', 'Frequency'])

# Export the DataFrame to an Excel file
output_file = 'word_frequencies.xlsx'
df.to_excel(output_file, index=False)
print(f"Word frequencies have been exported to {output_file}")
