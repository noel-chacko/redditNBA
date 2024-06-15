import os
import praw
import pandas as pd
from datetime import datetime, timedelta
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter
import matplotlib.pyplot as plt
import networkx as nx
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

# Generate a network graph of word co-occurrences
def create_cooccurrence_graph(tokens, top_n=20):
    top_words = [word for word, freq in most_common_words[:top_n]]
    word_pairs = [(tokens[i], tokens[i+1]) for i in range(len(tokens)-1) if tokens[i] in top_words and tokens[i+1] in top_words]
    cooccurrence_counts = Counter(word_pairs)

    G = nx.Graph()
    for (word1, word2), count in cooccurrence_counts.items():
        if count > 1:
            G.add_edge(word1, word2, weight=count)

    pos = nx.spring_layout(G, k=0.5, iterations=50)
    plt.figure(figsize=(12, 8))
    nx.draw_networkx_nodes(G, pos, node_size=2000, node_color='lightblue')
    nx.draw_networkx_edges(G, pos, width=[G[u][v]['weight'] for u,v in G.edges()])
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')
    plt.title('Network Graph of Word Co-occurrences')
    plt.show()

# Create the network graph
create_cooccurrence_graph(tokens)
