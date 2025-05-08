from flask import Flask,request, render_template, jsonify
import requests
from bs4 import BeautifulSoup
import time
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# Initialize Flask app
app = Flask(__name__)

# Download VADER lexicon for sentiment analysis
nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()

# product_url = "https://www.flipkart.com/poco-c75-5g-aqua-bliss-64-gb/product-reviews/itm10b3f6f1bc616?pid=MOBH7443MMBCWPPG&lid=LSTMOBH7443MMBCWPPGVOR2LC&aid=overall&certifiedBuyer=false&sortOrder=MOST_RECENT"

# Set headers to avoid getting blocked
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

def scrape_reviews(product_url, pages=5):
    reviews = []
    sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
    for page in range(1, pages + 1):
        url = f"{product_url}&page={page}"
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            continue
        soup = BeautifulSoup(response.text, 'html.parser')
        elements = soup.find_all("div", class_="ZmyHeo")
        for element in elements:
            text = element.get_text(strip=True).replace("READ MORE", "")
            sentiment_score = sia.polarity_scores(text)['compound']
            sentiment = "Positive" if sentiment_score > 0 else "Negative" if sentiment_score < 0 else "Neutral"
            reviews.append({"Review": text, "Sentiment": sentiment})
            sentiment_counts[sentiment] += 1
        time.sleep(2)  # Prevent getting blocked
    return reviews,sentiment_counts


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        product_url = request.form['product_url']
        if "flipkart.com" not in product_url:
            return render_template('index.html', error="Invalid Flipkart URL")

        reviews, sentiment_counts = scrape_reviews(product_url)
        return render_template('index.html', reviews=reviews, sentiment_counts=sentiment_counts)

    return render_template('index.html')
@app.route('/api/reviews', methods=['GET'])
def api_reviews():
    product_url = request.args.get('product_url')
    if not product_url or "flipkart.com" not in product_url:
        return jsonify({"error": "Invalid Flipkart URL"}), 400
    reviews = scrape_reviews(product_url)
    return jsonify(reviews)

if __name__ == '__main__':
    app.run(debug=True)
