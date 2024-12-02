import logging

from telegram import Update
from telegram.ext import CallbackContext

from solbot.web3.basic import get_token_information

from solbot.state import user_data, user_states, DOGBOT, SNIPE_TOKEN_AMOUNT, SWAP_TOKEN_AMOUNT

logger = logging.getLogger(__name__)

def handle_buy_dog_bot_amount(update: Update, context: CallbackContext):
    try:
        chat_id = update.effective_chat.id
        user_data.setdefault(chat_id, {})['address'] = DOGBOT

        token_info = get_token_information(DOGBOT)

        if token_info == 0:
            user_states[chat_id] = SNIPE_TOKEN_AMOUNT
        else:
            user_states[chat_id] = SWAP_TOKEN_AMOUNT

        context.bot.send_message(chat_id, "Enter the amount in SOL to purchase DOGBOT")
    except Exception as e:
        logger.exception("Failed to buy dog bot amount")
