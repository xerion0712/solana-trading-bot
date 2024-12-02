import logging
import math
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, Update
from telegram.ext import CallbackContext

from solbot.web3.basic import get_wallet_pubkey, get_token_balance, get_token_metadata, get_client
from solbot.web3.swap import handle_sell_token, handle_buy_token
from solbot.database import get_priv_key

from solbot.state import user_states, user_logs, LAMPORTS_PER_SOL, BUY_SELL_TOKEN_ADDRESS

logger = logging.getLogger(__name__)

def buy_option(bot, chat_id, message_id, token_address):
    logger.info(f'message_id {message_id}')
    try:
        keyboard = [
            [InlineKeyboardButton("0.1", callback_data=f"BUYX_{token_address}_0.1"), InlineKeyboardButton("0.2", callback_data=f"BUYX_{token_address}_0.2"), InlineKeyboardButton("0.3", callback_data=f"BUYX_{token_address}_0.3")],
            [InlineKeyboardButton("0.4", callback_data=f"BUYX_{token_address}_0.4"), InlineKeyboardButton("0.5", callback_data=f"BUYX_{token_address}_0.5"), InlineKeyboardButton("0.6", callback_data=f"BUYX_{token_address}_0.6")],
            [InlineKeyboardButton("0.7", callback_data=f"BUYX_{token_address}_0.7"), InlineKeyboardButton("0.8", callback_data=f"BUYX_{token_address}_0.8"), InlineKeyboardButton("0.9", callback_data=f"BUYX_{token_address}_0.9")],
            [InlineKeyboardButton("1", callback_data=f"BUYX_{token_address}_1"), InlineKeyboardButton("1.25", callback_data=f"BUYX_{token_address}_1.25"), InlineKeyboardButton("1.5", callback_data=f"BUYX_{token_address}_1.5")],
            [InlineKeyboardButton("1.75", callback_data=f"BUYX_{token_address}_1.75"), InlineKeyboardButton("2", callback_data=f"BUYX_{token_address}_2"), InlineKeyboardButton("3", callback_data=f"BUYX_{token_address}_3")],
            [InlineKeyboardButton("4", callback_data=f"BUYX_{token_address}_4"), InlineKeyboardButton("5", callback_data=f"BUYX_{token_address}_5"), InlineKeyboardButton("7", callback_data=f"BUYX_{token_address}_7.5")],
            [InlineKeyboardButton("10", callback_data=f"BUYX_{token_address}_10"), InlineKeyboardButton("20", callback_data=f"BUYX_{token_address}_20"), InlineKeyboardButton("X", callback_data=f"CUSTOM_BUY_AMOUNT_{token_address}")],
            [InlineKeyboardButton("RAPID FIRE BUY", callback_data=f"BATCHBUY_{token_address}"), InlineKeyboardButton("CANCEL", callback_data=f"EXIT_FUN_{token_address}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="<b>TOKEN BUY:</b> Enter the quantity of SOL that you would like to spend", reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    except Exception:
        logger.exception("Buy option error")

def sell_option(bot, chat_id, message_id, token_address):
    try:
        hex_priv_key = get_priv_key(chat_id)
        pubkey = get_wallet_pubkey(hex_priv_key)
        token_balance, decimal_balance = get_token_balance(str(pubkey),str(token_address))
        if token_balance:
            text = "<b>TOKEN SELL:</b> Select the (%) of your tokens to sell or enter a specific number of tokens "
            keyboard = [
                [InlineKeyboardButton("5", callback_data=f"SELLX_{token_address}_5"),InlineKeyboardButton("10", callback_data=f"SELLX_{token_address}_10"),InlineKeyboardButton("15", callback_data=f"SELLX_{token_address}_15")],
                [InlineKeyboardButton("20", callback_data=f"SELLX_{token_address}_20"),InlineKeyboardButton("25", callback_data=f"SELLX_{token_address}_25"),InlineKeyboardButton("30", callback_data=f"SELLX_{token_address}_30")],
                [InlineKeyboardButton("35", callback_data=f"SELLX_{token_address}_35"),InlineKeyboardButton("40", callback_data=f"SELLX_{token_address}_40"),InlineKeyboardButton("45", callback_data=f"SELLX_{token_address}_45")],
                [InlineKeyboardButton("50", callback_data=f"SELLX_{token_address}_50"),InlineKeyboardButton("55", callback_data=f"SELLX_{token_address}_55"),InlineKeyboardButton("60", callback_data=f"SELLX_{token_address}_60")],
                [InlineKeyboardButton("65", callback_data=f"SELLX_{token_address}_65"),InlineKeyboardButton("70", callback_data=f"SELLX_{token_address}_70"),InlineKeyboardButton("75", callback_data=f"SELLX_{token_address}_75")],
                [InlineKeyboardButton("80", callback_data=f"SELLX_{token_address}_80"),InlineKeyboardButton("85", callback_data=f"SELLX_{token_address}_85"),InlineKeyboardButton("90", callback_data=f"SELLX_{token_address}_90")],
                [InlineKeyboardButton("95", callback_data=f"SELLX_{token_address}_95"),InlineKeyboardButton("100", callback_data=f"SELLX_{token_address}_100"),InlineKeyboardButton("X", callback_data=f"CUSTOM_SELL_PERCENT_{token_address}")],
                [InlineKeyboardButton("RAPID FIRE SELL", callback_data=f"BATCHSELL_{token_address}"),InlineKeyboardButton("CANCEL", callback_data=f"EXIT_FUN_{token_address}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
        else:
            text = "You have zero balance token"
            keyboard = [
                [InlineKeyboardButton("MENU", callback_data=f"EXIT_FUN_{token_address}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    except Exception:
        logger.exception("Sell option error")

def buy(bot, chat_id, token_address,amount):
    solana_client = get_client()
    hex_priv_key = get_priv_key(chat_id)
    pubkey = get_wallet_pubkey(hex_priv_key)
    balance_lamports = solana_client.get_balance(pubkey, "confirmed").value

    balance = balance_lamports / LAMPORTS_PER_SOL

    if amount > 0 and amount <= float(balance):
        _, symbol, _, _, _, _ = get_token_metadata(token_address)
        formated_amount = f"{amount:.8f}".rstrip('0').rstrip('.')
        bot.send_message(chat_id, f"BUYING {formated_amount} SOL WORTH OF {symbol}\n\nRemember to check your current SOL balance for gas fees. Please wait.")

        handle_buy_token(bot, chat_id, token_address, amount)
    else:
        bot.send_message(
            chat_id, f"Invalid Value Try Again or more than your balance")
        pass

def sell(bot, chat_id, token_address,amount):
    hex_priv_key = get_priv_key(chat_id)
    pubkey = get_wallet_pubkey(hex_priv_key)
    token_balance, decimal_balance = get_token_balance(str(pubkey),str(token_address))

    if amount > 0 and amount <= 100:
        # user_data[chat_id]['amount'] = amount
        _, symbol, _, _, _, decimals = get_token_metadata(token_address)
        bot.send_message(chat_id, f"SELLING {amount}% OF YOUR SUPPLY OF {symbol},\n\nRemember to check your current SOL balance for gas fees. Please wait.")

        handle_sell_token(bot, chat_id, token_address, math.floor(amount * token_balance / 100 *  math.pow(10, decimals)),decimals)
    else:
        bot.send_message(chat_id, f"Invalid Value Try Again or more than your balance")
        pass

def custom_buy_option(bot, chat_id, message_id, address):
    keyboard = [[InlineKeyboardButton("⬅️ BACK",callback_data=f"EXIT_FUN_{address}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Enter the amount of SOL to spend: ",reply_markup=reply_markup)

def custom_sell_option(bot, chat_id, message_id, address):
    keyboard = [[InlineKeyboardButton("⬅️ BACK",callback_data=f"EXIT_FUN_{address}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Enter the token percentage to spend: ",reply_markup=reply_markup)

def input_token_address(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    message_id = update.callback_query.message.message_id
    user_states[chat_id] = BUY_SELL_TOKEN_ADDRESS
    keyboard = [
        [InlineKeyboardButton("☰ MENU", callback_data="EXIT")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    chat_log = context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Enter the token address to buy/sell:", reply_markup=reply_markup)
    user_logs[chat_id] = chat_log.message_id


def batch_buy_amount_option(update: Update, context: CallbackContext, token:str):
    chat_id = update.effective_chat.id
    message_id = update.callback_query.message.message_id
    text='<b>Enter Sol Amount to spend per transaction:</b>'
    keyboard = [[InlineKeyboardButton("⬅️ BACK",callback_data=f"BUYOPT_{token}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    chat_log = context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text,reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    user_logs[chat_id] = chat_log.message_id


def batch_sell_amount_option(update: Update, context: CallbackContext, token:str):
    chat_id = update.effective_chat.id
    message_id = update.callback_query.message.message_id
    text='<b>Enter the number of tokens to sell per transaction:</b>'
    keyboard = [[InlineKeyboardButton("⬅️ BACK",callback_data=f"SELLOPT_{token}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    chat_log = context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text,reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    user_logs[chat_id] = chat_log.message_id
