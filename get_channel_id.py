from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
from telegram import Update

# Replace with your actual bot token
telegram_token = '7899473852:AAFyH7S6O_Ec3zci6oVBkmw1-3e6lA7MiKw'

def show_chat_id(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message = (
        f"Chat title: {chat.title or 'Private/User Chat'}\n"
        f"Chat type: {chat.type}\n"
        f"Chat ID: `{chat.id}`"
    )
    print(message)  # Print in console
    update.message.reply_text(message, parse_mode='Markdown')

def main():
    updater = Updater(telegram_token)
    dp = updater.dispatcher

    # Handle any message to show chat ID
    dp.add_handler(MessageHandler(Filters.all, show_chat_id))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
