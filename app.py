from flask import Flask, request, render_template, jsonify
import requests
from bs4 import BeautifulSoup
import time
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import os


# Initialize Flask app
app = Flask(__name__)

# Download VADER lexicon (only once)
nltk.download('vader_lexicon', quiet=True)
sia = SentimentIntensityAnalyzer()

# Set headers to avoid getting blocked
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

import re

def clean_review(text):
    # Remove URLs, emojis, and non-alphabetic characters
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^\w\s]", "", text)  # Remove punctuation
    text = re.sub(r"\s+", " ", text).strip()
    return text

def get_sentiment(text):
    score = sia.polarity_scores(text)['compound']
    if score >= 0.2:
        return "Positive"
    elif score <= -0.2:
        return "Negative"
    else:
        return "Neutral"

def scrape_reviews(product_url, pages=5):
    reviews = []
    sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
    for page in range(1, pages + 1):  # Only scrape the specified number of pages
        url = f"{product_url}&page={page}"
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code != 200:
                continue
            soup = BeautifulSoup(response.text, 'html.parser')
            elements = soup.find_all("div", class_="ZmyHeo")
            if not elements:
                break  # Stop if no more reviews
            for element in elements:
                raw_text = element.get_text(strip=True).replace("READ MORE", "")
                cleaned_text = clean_review(raw_text)
                if not cleaned_text or len(cleaned_text.split()) < 3:
                    continue  # Skip very short or empty reviews
                sentiment = get_sentiment(cleaned_text)
                reviews.append({"Review": raw_text, "Sentiment": sentiment})
                sentiment_counts[sentiment] += 1
            time.sleep(2)  # Prevent getting blocked
        except Exception as e:
            print(f"Error scraping page {page}: {e}")
            continue
    return reviews, sentiment_counts

def generate_wordclouds(reviews):
    sentiments = {"Positive": [], "Negative": [], "Neutral": []}
    for review in reviews:
        sentiments[review["Sentiment"]].append(review["Review"])

    wordcloud_paths = {}
    static_folder = os.path.join("static")
    os.makedirs(static_folder, exist_ok=True)

    for sentiment, texts in sentiments.items():
        text_blob = " ".join(texts)
        if text_blob.strip():  # Only generate if text exists
            wc = WordCloud(width=400, height=400, background_color='white').generate(text_blob)
            path = os.path.join(static_folder, f"{sentiment.lower()}_wordcloud.png")
            wc.to_file(path)
            wordcloud_paths[sentiment] = os.path.basename(path)


    return wordcloud_paths


@app.route('/', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        product_url = request.form.get('product_url', '')
        if "flipkart.com" not in product_url:
            return render_template('index.html', error="Invalid Flipkart URL")

        reviews, sentiment_counts = scrape_reviews(product_url)
        if not reviews:
            return render_template('index.html', error="No reviews found or scraping failed.")

        wordcloud_paths = generate_wordclouds(reviews)

        return render_template('index.html', reviews=reviews, sentiment_counts=sentiment_counts, wordcloud_paths=wordcloud_paths)

    return render_template('index.html')


@app.route('/api/reviews', methods=['GET'])
def api_reviews():
    product_url = request.args.get('product_url')
    if not product_url or "flipkart.com" not in product_url:
        return jsonify({"error": "Invalid Flipkart URL"}), 400
    reviews, sentiment_counts = scrape_reviews(product_url)
    return jsonify({
        "reviews": reviews,
        "sentiment_counts": sentiment_counts
    })

if __name__ == '__main__':
    app.run(debug=True)
