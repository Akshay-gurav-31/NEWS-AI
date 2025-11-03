from flask import Flask, render_template, request, jsonify
import requests
import time
from datetime import datetime, timedelta
import re
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import os

app = Flask(__name__)

NEWS_API_KEY = '220cf0fc01744c609a262a7409b31aea'
NEWS_ENDPOINT = 'https://newsapi.org/v2/everything'

KEYWORDS = [
    'health', 'nutrition', 'fitness', 'wellness', 'diet', 'exercise',
    'healthy food', 'medical research', 'biotechnology', 'healthcare',
    'healthy lifestyle', 'sports medicine', 'nutrition science'
]

# Configure retry strategy
retry_strategy = Retry(
    total=3,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
session.mount("https://", adapter)
session.mount("http://", adapter)


def is_valid_image_url(url):
    if not url:
        return False
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
    return url.lower().endswith(image_extensions)


def get_news_articles(query=None, page=1, page_size=12):
    try:
        # Calculate date range (last 7 days to get more articles)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        # Build search query using all keywords
        if query:
            search_query = f"({query}) AND ({' OR '.join(KEYWORDS)})"
        else:
            search_query = ' OR '.join(KEYWORDS)

        params = {
            'q': search_query,
            'language': 'en',
            'sortBy': 'publishedAt',
            'apiKey': NEWS_API_KEY,
            'pageSize': 50,
            'page': page,
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d')
        }

        response = session.get(NEWS_ENDPOINT, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        articles = data.get('articles', [])
        processed_articles = []

        for article in articles:
            if (article.get('title') and 
                article.get('description') and 
                article.get('url') and 
                is_valid_image_url(article.get('urlToImage'))):

                published_at = article.get('publishedAt', '').split('T')[0]
                try:
                    date_obj = datetime.strptime(published_at, '%Y-%m-%d')
                    published_at = date_obj.strftime('%B %d, %Y')
                except:
                    pass

                processed_articles.append({
                    'title': article.get('title'),
                    'description': article.get('description'),
                    'url': article.get('url'),
                    'image_url': article.get('urlToImage'),
                    'source': article.get('source', {}).get('name', 'Unknown Source'),
                    'published_at': published_at
                })

            if len(processed_articles) >= 12:
                break

        return {
            'articles': processed_articles,
            'total_results': len(processed_articles),
            'current_page': 1,
            'total_pages': 1
        }

    except Exception as e:
        print(f"Error fetching news: {str(e)}")
        return {
            'articles': [],
            'total_results': 0,
            'current_page': 1,
            'total_pages': 1
        }


@app.route('/')
def show_disease_news():
    result = get_news_articles(page=1)
    return render_template('news.html',
                           articles=result['articles'],
                           current_page=1,
                           total_pages=1)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/search')
def search_news():
    query = request.args.get('q', '').strip()

    if not query:
        return jsonify({'error': 'Search query is required'}), 400

    result = get_news_articles(query, page=1)
    return jsonify(result)


# ✅ Production-safe server run config
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
