import os
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from pymongo import MongoClient

# Initialize MongoDB Client
mongo_client = MongoClient(os.getenv("MONGODB_URI"))
db = mongo_client['telegram_bot_db']
posts_collection = db['posts']

# Start Command
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Hello! I'm your assistant bot. Send me a file or video to rename, or type a message to create a post.")

# Forward Message
def forward_message(update: Update, context: CallbackContext):
    target_channel_id = "@your_target_channel"  # Replace with your target channel ID
    message = update.message.text or update.message.caption
    context.bot.send_message(chat_id=target_channel_id, text=message)

# Handle File or Video Renaming
def handle_file(update: Update, context: CallbackContext):
    file = update.message.document or update.message.video
    new_name = " ".join(context.args) if context.args else "renamed_file"
    file.download(custom_path=new_name)
    
    with open(new_name, "rb") as f:
        context.bot.send_document(chat_id=update.message.chat_id, document=InputFile(f))

# Create or Edit a Telegram Post
def create_post(update: Update, context: CallbackContext):
    message = " ".join(context.args)
    post_format = posts_collection.find_one({"chat_id": update.message.chat_id})
    post_format = post_format.get("format", "{content}") if post_format else "{content}"
    formatted_post = post_format.format(content=message)
    
    target_channel_id = "@your_target_channel"  # Replace with your target channel ID
    context.bot.send_message(chat_id=target_channel_id, text=formatted_post)

# Set or Update Post Format
def set_post_format(update: Update, context: CallbackContext):
    format_string = " ".join(context.args)
    posts_collection.update_one(
        {"chat_id": update.message.chat_id},
        {"$set": {"format": format_string}},
        upsert=True
    )
    update.message.reply_text(f"Post format set to: {format_string}")

def main():
    updater = Updater(token=os.getenv("TELEGRAM_BOT_TOKEN"), use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, forward_message))
    dp.add_handler(MessageHandler(Filters.document | Filters.video, handle_file))
    dp.add_handler(CommandHandler("createpost", create_post))
    dp.add_handler(CommandHandler("setpostformat", set_post_format))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
