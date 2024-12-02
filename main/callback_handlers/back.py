from telegram import Update
from telegram.ext import CallbackContext

def back(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()  # Acknowledge the callback
    chat_id = update.effective_chat.id
    message_id = query.message.message_id
    context.bot.delete_message(chat_id, message_id=message_id)
