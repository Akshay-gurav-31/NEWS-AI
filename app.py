from flask import Flask, render_template
import requests
import time
from datetime import datetime

app = Flask(__name__)

NEWS_API_KEY = 'fdfd6731b3f0470982aec2feec373cab'
NEWS_ENDPOINT = 'https://newsapi.org/v2/everything'

KEYWORDS = [
    'health', 'nutrition', 'fitness', 'wellness', 'diet', 'exercise',
    'healthy food', 'medical research', 'biotechnology', 'healthcare',
    'healthy lifestyle', 'sports medicine', 'nutrition science'
]

def get_unique_articles():
    params = {
        'q': ' OR '.join(KEYWORDS),
        'language': 'en',
        'sortBy': 'publishedAt',
        'apiKey': NEWS_API_KEY,
        'pageSize': 30  # Fetch more articles to ensure we get 4 unique ones
    }

    try:
        response = requests.get(NEWS_ENDPOINT, params=params)
        response.raise_for_status()
        data = response.json()

        articles = data.get('articles', [])
        
        # Filter articles with images and remove duplicates based on title
        seen_titles = set()
        unique_articles = []
        
        for article in articles:
            if (article.get('urlToImage') and 
                article.get('title') not in seen_titles and 
                len(unique_articles) < 4):
                seen_titles.add(article.get('title'))
                unique_articles.append(article)

        return unique_articles

    except Exception as e:
        print("Error fetching health news:", e)
        if 'response' in locals():
            print("Response content:", response.text)
        return []

@app.route('/')
def show_disease_news():
    articles = get_unique_articles()
    return render_template('news.html', articles=articles)

if __name__ == '__main__':
    app.run(debug=True)
