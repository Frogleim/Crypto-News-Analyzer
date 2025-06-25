import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem, QMessageBox, QHBoxLayout
)
from PyQt6.QtCore import Qt

import pandas as pd
from textblob import TextBlob
import requests
import ssl
import nltk
from nltk.corpus import stopwords

# Setup
nltk.download('stopwords')
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# API Info
api_key = 'f5fe5390fbb64c64883b26acdcadc8dc'
base_url = 'https://newsapi.org/v2/everything'

# Symbol → Keyword Mapping
symbol_to_query = {
    "SDX500-USD": '"S&P 500"',
    "NDXUSD": '"Nasdaq 100"',
    "BTCUSDT": '"Bitcoin"',
    "ETHUSDT": '"Ethereum"',
}

# --- Logic Functions ---
def fetch_crypto_news(query='S&P 500', from_date='2025-06-23', to_date='2025-06-24', language='en'):
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
        raise Exception(f"Error fetching data: {data.get('message', 'Unknown error')}")
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
    avg = df['sentiment'].mean()
    return {
        'average_sentiment': avg,
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

# --- GUI ---
class NewsSentimentApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("News Sentiment Analyzer")
        self.setGeometry(300, 150, 950, 650)
        self.layout = QVBoxLayout()

        # Top label
        self.signal_label = QLabel("")
        self.layout.addWidget(self.signal_label)

        # Buttons Row
        button_row = QHBoxLayout()
        for symbol in symbol_to_query:
            btn = QPushButton(symbol)
            btn.clicked.connect(lambda _, s=symbol: self.fetch_and_display(s))
            button_row.addWidget(btn)
        self.layout.addLayout(button_row)

        # Summary
        self.summary_output = QTextEdit()
        self.summary_output.setReadOnly(True)
        self.layout.addWidget(self.summary_output)

        # Table
        self.table = QTableWidget()
        self.layout.addWidget(self.table)

        self.setLayout(self.layout)

    def fetch_and_display(self, symbol):
        query = symbol_to_query[symbol]
        try:
            df = fetch_crypto_news(query=query)
            df['cleaned_description'] = df['description'].fillna('').apply(preprocess_text)
            df['sentiment'] = df['cleaned_description'].apply(analyze_sentiment)
            summary = get_sentiment_summary(df)
            signal = generate_trading_signal(summary)

            self.signal_label.setText(f"<h2>{symbol} → <span style='color: green'>{signal}</span></h2>")
            self.summary_output.setPlainText(
                f"Query: {query}\n"
                f"Average Sentiment: {summary['average_sentiment']:.3f}\n"
                f"Positive Articles: {summary['positive_articles']}\n"
                f"Negative Articles: {summary['negative_articles']}\n"
                f"Neutral Articles:  {summary['neutral_articles']}"
            )
            self.populate_table(df[['title', 'description', 'sentiment']])
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def populate_table(self, df):
        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(df.columns)

        for i, row in df.iterrows():
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                self.table.setItem(i, j, item)

# --- Run App ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = NewsSentimentApp()
    window.show()
    sys.exit(app.exec())