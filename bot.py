import time

import requests
import pandas as pd
from datetime import datetime, timedelta
import nltk
from nltk.corpus import stopwords
import ssl
from textblob import TextBlob
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram import Update

# Setting up SSL context
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Download stopwords
nltk.download('stopwords')

# Replace 'your_api_key_here' with your actual NewsAPI key
api_key = 'f5fe5390fbb64c64883b26acdcadc8dc'
base_url = 'https://newsapi.org/v2/everything'

# Replace 'your_telegram_token_here' with your actual Telegram bot token
telegram_token = '7247839345:AAF1YTg3ZTio4n3vQlzgKCn0FexkpneHppI'


def fetch_crypto_news(query='BTCUSDT OR Bitcoin AND USDT', from_date=None, to_date=None, language='en'):
    if not from_date:
        from_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    if not to_date:
        to_date = datetime.now().strftime('%Y-%m-%d')

    params = {
        'q': query,
        'from': from_date,
        'to': to_date,
        'language': language,
        'apiKey': api_key,
        'pageSize': 100
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    if data['status'] != 'ok':
        raise Exception(f"Error fetching data: {data['message']}")

    return pd.DataFrame(data['articles'])


def preprocess_text(text):
    # Convert to lowercase
    text = text.lower()
    # Remove special characters, numbers, etc.
    text = ''.join([c for c in text if c.isalpha() or c.isspace()])
    # Tokenize text
    tokens = text.split()
    # Remove stopwords
    tokens = [word for word in tokens if word not in stopwords.words('english')]
    # Join tokens back to string
    return ' '.join(tokens)


def analyze_sentiment(text):
    # Create a TextBlob object and get the polarity
    return TextBlob(text).sentiment.polarity


def get_sentiment_summary(df):
    average_sentiment = df['sentiment'].mean()
    positive_articles = df[df['sentiment'] > 0].shape[0]
    negative_articles = df[df['sentiment'] < 0].shape[0]
    neutral_articles = df[df['sentiment'] == 0].shape[0]

    return {
        'average_sentiment': average_sentiment,
        'positive_articles': positive_articles,
        'negative_articles': negative_articles,
        'neutral_articles': neutral_articles,
    }


def generate_trading_signal(sentiment_summary):
    if sentiment_summary['average_sentiment'] > 0.1:
        return "BUY"
    elif sentiment_summary['average_sentiment'] < -0.1:
        return "SELL"
    else:
        return "HOLD"


# Function to send the trading signal via Telegram
def send_signal(update: Update, context: CallbackContext):
    # Fetch recent BTCUSDT news
    while True:
        news_df = fetch_crypto_news()
        news_df['cleaned_description'] = news_df['description'].apply(lambda x: preprocess_text(x) if pd.notnull(x) else '')
        news_df['sentiment'] = news_df['cleaned_description'].apply(analyze_sentiment)
        sentiment_summary = get_sentiment_summary(news_df)
        trading_signal = generate_trading_signal(sentiment_summary)

        # Send the signal to the Telegram chat
        update.message.reply_text(f"Trading Signal BTC: {trading_signal}")
        time.sleep(3600)

# Main function to set up the Telegram bot
def main():
    # Set up the updater and dispatcher
    updater = Updater(telegram_token)
    dp = updater.dispatcher

    # Add command handler to send signal when /signal command is issued
    dp.add_handler(CommandHandler("signal", send_signal))

    # Start the bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
