from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, Update, InlineKeyboardButton
from telegram.ext import CallbackContext
from time import sleep 
from solders.keypair import Keypair # type: ignore

from solbot.command_handlers import start_handler
from solbot.web3.basic import get_client
from solbot.database import get_priv_key, delete_priv_key, get_fee_tip_info

from solbot.state import user_states, LAMPORTS_PER_SOL, WITHDRAW_ALL_SOL, WITHDRAW_X_SOL

def settings(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    hex_priv_key = get_priv_key(chat_id)
    message_id = update.callback_query.message.message_id

    try:
        keyboard = [
            [InlineKeyboardButton("🌐 SOLSCAN", url=f"https://solscan.io/account/{Keypair.from_base58_string(hex_priv_key).pubkey()}")],
            [InlineKeyboardButton("🔓 PRIVATE KEY", callback_data="EXPORT"),InlineKeyboardButton("📵 DISCONNECT WALLET", callback_data="DISCONNECT_WALLET_PANEL")],
            [InlineKeyboardButton("⚙️ CONFIG GAS FEE", callback_data="GAS_FEE"),InlineKeyboardButton("⚙️ CONFIG TIP FEE", callback_data="JITO_TIP")],
            [InlineKeyboardButton("🔀 SWITCH CHAIN", callback_data="SWITCH_CHAIN")],
            [InlineKeyboardButton("Withdraw All Sol", callback_data="WITHDRAW_ALL_SOL"),InlineKeyboardButton("Withdraw % Sol", callback_data="WITHDRAW_SOL_X")],
            [InlineKeyboardButton("☰ MENU", callback_data="EXIT")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        
        context.bot.edit_message_text(
            chat_id=chat_id, 
            message_id=message_id, 
            text="Choose an option:", 
            reply_markup=reply_markup
        )
        
    except Exception as e:
        print("Settings error", e)

def export_private_key(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    hex_priv_key = get_priv_key(chat_id)

    message = f'Your private key will be dissapeared automatically soon, because of security\n<code>{hex_priv_key}</code>'

    ctx = context.bot.send_message(
        chat_id=chat_id, 
        text=message, 
        parse_mode=ParseMode.HTML
    )

    sleep(5)

    context.bot.delete_message(chat_id, ctx.message_id)

def disconnect_wallet(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    message_id = update.callback_query.message.message_id
    delete_priv_key(chat_id)

    context.bot.delete_message(chat_id, message_id)
    start_handler(update, context)

def disconnect_wallet_msg(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    message_id = update.callback_query.message.message_id
    
    text = 'Are you going to disconnect wallet?'
    keyboard = [
        [InlineKeyboardButton("DISCONNECT", callback_data="DISCONNECT_WALLET"), InlineKeyboardButton("NO", callback_data="SETTINGS")],   
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup)

def handle_gas_fee(update: Update, context: CallbackContext) -> None:
    try:
        chat_id = update.effective_chat.id
        message_id = update.callback_query.message.message_id

        fee, tip = get_fee_tip_info(chat_id)
        
        message = f"Please select your desired Validator tip fee. The higher the tip fee, the faster your transaction will process along with a higher success rate.  Standard Fee is set as the default.  See below for Fee options:\n\n{'🟢' if fee == 'LOW' else '🔴'} Low Gas Fee = 0.001 SOL\n{'🟢' if fee == 'STANDARD' else '🔴'} Standard Gas Fee = 0.01 SOL\n{'🟢' if fee == 'HIGH' else '🔴'} High Gas Fee = 0.02 SOL"

        keyboard = [
            [InlineKeyboardButton("🕯️ Low Gas Fee", callback_data="LOW_FEE_GAS")],
            [InlineKeyboardButton("🔥 Standard Gas Fee", callback_data="STANDARD_FEE_GAS")],
            [InlineKeyboardButton("💥 High Gas Fee", callback_data="HIGH_FEE_GAS")],
            [InlineKeyboardButton("⬅️ BACK", callback_data="SETTINGS")],   
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=message, reply_markup=reply_markup)
    
    except Exception as e:
        print(e)

def handle_jito_fee(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    message_id = update.callback_query.message.message_id

    fee, tip = get_fee_tip_info(chat_id)

    message = f"Please select your desired Validator tip fee when using jito service. The higher the tip fee, the faster your transaction will process along with a higher success rate.  Standard Fee is set as the default.  See below for Fee options:\n\n{'🟢' if tip == 'LOW' else '🔴'} Low Tip Fee = 0.00105 SOL\n{'🟢' if tip == 'STANDARD' else '🔴'} Standard Tip Fee = 0.0105 SOL\n{'🟢' if tip == 'HIGH' else '🔴'} High Tip Fee = 0.0205 SOL"

    keyboard = [
        [InlineKeyboardButton("🕯️ Low Tip Fee", callback_data="LOW_JITO_TIP")],
        [InlineKeyboardButton("🔥 Standard Tip Fee", callback_data="STANDARD_JITO_TIP")],
        [InlineKeyboardButton("💥 High Tip Fee", callback_data="HIGH_JITO_TIP")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="SETTINGS")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=message, reply_markup=reply_markup)

def handle_switch_chain(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    message_id = update.callback_query.message.message_id
    keyboard = [
         [InlineKeyboardButton("SWITCH TO ETH", url="https://t.me/DOGBOT_ETHBOT"),InlineKeyboardButton("SWITCH TO BNB", url="https://t.me/DOGBOT_BSCBOT")],
         [InlineKeyboardButton("⬅️ BACK", callback_data="SETTINGS")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = "Choose an option:"

    context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=message, reply_markup=reply_markup)

def handle_withdraw_all(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    solana_client = get_client()
    hex_priv_key = get_priv_key(chat_id)
    balance = solana_client.get_balance(Keypair.from_base58_string(hex_priv_key).pubkey(),"confirmed")
    keyboard = [
        [InlineKeyboardButton("⬅️ BACK", callback_data="SETTINGS")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"Balance: {balance.value / LAMPORTS_PER_SOL} SOL 💰\nEnter the Recipient who will receive all sol:"
    context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
    user_states[chat_id] = WITHDRAW_ALL_SOL

def handle_withdraw_x(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    solana_client = get_client()
    hex_priv_key = get_priv_key(chat_id)
    balance = solana_client.get_balance(Keypair.from_base58_string(hex_priv_key).pubkey(),"confirmed")
    keyboard = [
        [InlineKeyboardButton("⬅️ BACK", callback_data="SETTINGS")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"Balance: {balance.value / LAMPORTS_PER_SOL} SOL 💰\nEnter the Recipient who will receive some sol:"
    context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
    user_states[chat_id] = WITHDRAW_X_SOL