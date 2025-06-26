import time
import threading
import requests
import pandas as pd
from datetime import datetime, timedelta
import nltk
from nltk.corpus import stopwords
import ssl
from textblob import TextBlob
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram import Update, Bot

# SSL fix for nltk downloads
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Download NLTK stopwords
nltk.download('stopwords')

# News API setup
api_key = ''
base_url = 'https://newsapi.org/v2/everything'

# Telegram Bot Token
telegram_token = ''

# Replace with your Telegram channel username (public) or chat ID (private)
channel_id = ''  # or '-1001234567890' for private channels


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
    text = text.lower()
    text = ''.join([c for c in text if c.isalpha() or c.isspace()])
    tokens = text.split()
    tokens = [word for word in tokens if word not in stopwords.words('english')]
    return ' '.join(tokens)


def analyze_sentiment(text):
    return TextBlob(text).sentiment.polarity


def get_sentiment_summary(df):
    average_sentiment = df['sentiment'].mean()
    return {
        'average_sentiment': average_sentiment,
        'positive_articles': df[df['sentiment'] > 0].shape[0],
        'negative_articles': df[df['sentiment'] < 0].shape[0],
        'neutral_articles': df[df['sentiment'] == 0].shape[0],
    }


def generate_trading_signal(summary):
    if summary['average_sentiment'] > 0.1:
        return "BUY"
    elif summary['average_sentiment'] < -0.1:
        return "SELL"
    else:
        return "HOLD"


def send_signal_to_channel(bot: Bot):
    news_df = fetch_crypto_news()

    news_df['cleaned_description'] = news_df['description'].apply(lambda x: preprocess_text(x) if pd.notnull(x) else '')
    news_df['sentiment'] = news_df['cleaned_description'].apply(analyze_sentiment)
    summary = get_sentiment_summary(news_df)
    signal = generate_trading_signal(summary)

    # Find highly impactful articles
    impact_threshold = 0.5  # You can tune this
    impactful_articles = news_df[abs(news_df['sentiment']) >= impact_threshold]

    top_news_lines = []
    for _, row in impactful_articles.iterrows():
        polarity = row['sentiment']
        title = row['title'] or "No title"
        url = row['url'] or ""
        emoji = "🟢" if polarity > 0 else "🔴"
        line = f"{emoji} *{title.strip()}*\n[Read more]({url}) — Sentiment: {polarity:.2f}"
        top_news_lines.append(line)

    top_news_section = "\n\n🔥 *High-Impact News Detected:*\n" + "\n\n".join(top_news_lines) if top_news_lines else ""

    message = (
        f"📊 *BTCUSDT Trading Signal*\n"
        f"Signal: *{signal}*\n"
        f"Sentiment Score: {summary['average_sentiment']:.2f}\n"
        f"🟢 Positive: {summary['positive_articles']} | 🔴 Negative: {summary['negative_articles']} | ⚪ Neutral: {summary['neutral_articles']}\n"
        f"{top_news_section}"
    )

    bot.send_message(chat_id=channel_id, text=message, parse_mode="Markdown", disable_web_page_preview=False)



# Optional: /signal command for private use
def signal_command(update: Update, context: CallbackContext):
    send_signal_to_channel(context.bot)


def run_scheduled_signals(bot: Bot):
    send_signal_to_channel(bot)

    while True:
        try:
            send_signal_to_channel(bot)
        except Exception as e:
            print(f"Error sending scheduled signal: {e}")
        time.sleep(3600)  # every 1 hour
    #

def main():
    updater = Updater(telegram_token)
    bot = updater.bot

    # Start scheduled job in background
    threading.Thread(target=run_scheduled_signals, args=(bot,), daemon=True).start()

    # Handle /signal command in private chat (optional)
    updater.dispatcher.add_handler(CommandHandler("signal", signal_command))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
