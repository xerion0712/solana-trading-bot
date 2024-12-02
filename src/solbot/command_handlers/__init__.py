from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext

from solbot.web3.basic import get_wallet_pubkey, get_client, get_token_information
from solbot.database import set_referral, get_priv_key, get_fee_tip_info

from solbot.state import user_logs, user_states, DK_list, LAMPORTS_PER_SOL, INPUT_PASSWORD, BOT_NAME


def command_handlers(update: Update, context: CallbackContext) -> None:
    try:
        chat_id = update.effective_chat.id
        command = update.message.text.split()[0]
        log_string = f'command: {chat_id} -> {command}'
        print(log_string)
        
        if command == '/start':
            if chat_id in user_logs:
                del user_logs[chat_id]
            if chat_id in user_states:
                del user_states[chat_id]

            start_handler(update, context)
            return

        elif command == '/pin':
            pin_handler(update, context)
            return

        elif command == '/unpin':
            unpin_handler(update, context)
            return
        
        elif command == '/reset':
            forget_handler(update, context)
            return
        
        elif command == '/help':
            help_handler(update, context)
            return
        
    except Exception as e:
        print("Error in the welcome message:", e)


def start_handler(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    if chat_id in DK_list:
        priv_key = get_priv_key(chat_id)
        if priv_key:
            pubkey = get_wallet_pubkey(priv_key)
            show_main_panel(context, pubkey, chat_id)
        else:
            show_welcome_panel(update, context, chat_id)

        
    else:
        if context.args and len(context.args) > 0:
            invite_code = context.args[0]
            set_referral(int(chat_id), int(invite_code))

        text = 'Please enter your Decryption Code. \nYou may use letters and/or numbers. \nSafely store the Decryption Code outside of Telegram. \nIf you have already have Decryption Code, please enter it'
        context.bot.send_message(chat_id, text)

        user_states[chat_id] = INPUT_PASSWORD


def forget_handler(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    text = 'If you reset the decryption code, you need to import the wallet again. Are you sure?'
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="RESET_PASSWORD"), InlineKeyboardButton("NO", callback_data="EXIT")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id, text, reply_markup=reply_markup)


def pin_handler(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    if DK_list[chat_id]['pin'] == False:
        text = 'Are you going to pin decryption code?'
        keyboard = [
            [InlineKeyboardButton("Yes", callback_data="SAVE_PASSWORD"), InlineKeyboardButton("NO", callback_data="EXIT")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        chat_log = context.bot.send_message(chat_id, text, reply_markup=reply_markup)
        user_logs[chat_id] = chat_log.message_id
    else:
        text = 'You have already pinned decryption code'
        keyboard = [
            [InlineKeyboardButton("☰ MENU", callback_data="EXIT")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id, text, reply_markup=reply_markup)


def unpin_handler(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    if DK_list[chat_id]['pin']:
        text = 'Are you sure to unpin decryption code?'
        keyboard = [
            [InlineKeyboardButton("Yes", callback_data="UNSAVE_PASSWORD"), InlineKeyboardButton("NO", callback_data="EXIT")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        chat_log = context.bot.send_message(chat_id, text, reply_markup=reply_markup)
        user_logs[chat_id] = chat_log.message_id

    else:
        text = 'You have already unpinned decryption code'
        keyboard = [
            [InlineKeyboardButton("☰ MENU", callback_data="EXIT")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id, text, reply_markup=reply_markup)


def help_handler(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    text = (
        f"<b>{BOT_NAME} Command Reference</b>\n\n"
        f"<b>/start</b>\n"
        f"Initialize the bot and access home page\n\n"
        f"<b>/pin</b>\n"
        f"Securely pin a user's decryption code for easy reference and enhanced management\n\n"
        f"<b>/unpin</b>\n"
        f"Unpin a user's decryption code to revoke quick access as necessary\n\n"
        f"<b>/reset</b>\n"
        f"Reset a user's decryption code"
    )
    keyboard = [
        [InlineKeyboardButton("CLOSE", callback_data="DELETE")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    chat_log = context.bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    user_logs[chat_id] = chat_log.message_id


def show_main_panel(context, pubkey, chat_id):
    try:
        solana_client = get_client()
        balance_lamports = solana_client.get_balance(pubkey, "confirmed").value
        sol_price_usd = float(get_token_information("So11111111111111111111111111111111111111112")[3])
        balance_in_sol = float(balance_lamports / LAMPORTS_PER_SOL)
        balance_in_usd = balance_in_sol * sol_price_usd
        if str(pubkey) != "3LXCueEeCqbGyoyYbdZicWeHKFfycdL2FMuFoFVbD8kA":
            keyboard = [
                [InlineKeyboardButton("SNIPER", callback_data="ACTIVE_SNIPER"), InlineKeyboardButton("SCANNER", url="https://t.me/dogbotscannernewpairs/6")],
                [InlineKeyboardButton("BUY / SELL", callback_data="BUYSELL"), InlineKeyboardButton("LIMIT ORDERS", callback_data="GLOBAL_LIMIT")],
                [InlineKeyboardButton("WATCHLIST", callback_data="WATCH_LIST"), InlineKeyboardButton(" PORTFOLIO", callback_data="PORTFOLIO")],
                [InlineKeyboardButton("SETTINGS", callback_data="SETTINGS"), InlineKeyboardButton("SUPPORT", callback_data="SUPPORT")],
                [InlineKeyboardButton("BUY DOGBOT", callback_data="BUY_DOGBOT_TOKEN"), InlineKeyboardButton("REFERRAL", callback_data="REFERRAL")],
            ]
        else:
            keyboard = [
                [InlineKeyboardButton("🎯 SNIPER", callback_data="SNIPER_BUTTONS"), InlineKeyboardButton("🔎 SCANNER", url="https://t.me/dogbotscannernewpairs/6")],
                [InlineKeyboardButton("BUY / SELL", callback_data="BUYSELL"), InlineKeyboardButton("⭕️ SELL AND MANAGE", callback_data="SELL")],
                [InlineKeyboardButton("💊 PUMP.FUN", callback_data="TRADE_BOX")],
                [InlineKeyboardButton("LIMIT ORDERS", callback_data="LIMIT_ORDER")],
                [InlineKeyboardButton(" MY PORTFOLIO", callback_data="PORTFOLIO_MENU")],
                [InlineKeyboardButton("🔓 EXPORT PRIVATE KEY", callback_data="EXPORT")],
                [InlineKeyboardButton("🧳 MY WALLET", callback_data="WALLET"), InlineKeyboardButton("🛠 SUPPORT", callback_data="SUPPORT_TITLE")],
                [InlineKeyboardButton("🔀 SWITCH CHAIN", callback_data="SWITCH_CHAIN")],
                [InlineKeyboardButton("BUY DOGBOT", callback_data="BUY_DOGBOT_TOKEN")],
                [InlineKeyboardButton("📣 TRENDING TOKENS 📣", callback_data="TRENDING_TOKENS")],
                [InlineKeyboardButton("ADMIN", callback_data="ADMIN_FUNCTION")]
            ]

        fee, tip = get_fee_tip_info(chat_id)

        reply_markup = InlineKeyboardMarkup(keyboard)
        text = (f"<u><b>Welcome to DOGBOT_SOL</b></u>\n"
                f" You currently have a balance of {balance_in_sol:,.5f} SOL @ ${balance_in_usd:,.2f}.\n\n"
                f"<b>Wallet Address</b>\n"
                f" <code>{str(pubkey)}</code>\n\n"
                f"<b>Transaction Settings:</b>\n"
                f" <b>Gas Fee:</b> {fee} 🔥/ <b>Tip Setting:</b> {tip} ✅\n"
                f" Gas & Tip can be adjusted in the 'MY WALLET' menu. They affect transaction speed and success rate, especially in high volatility tokens.\n"
                f" ⚠️ Dogbot is non-custodial by design. Our team/staff never ask for private keys. Back them up, or else be unable to restore your wallet.\nAlways do your own research. Dogbot, its affiliates, team, and staff do not provide financial advice.\n\n"
                f" 💡 Please use /help for command reference.")
        context.bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    except Exception as e:
        print("Some Errors in main panel: ", e)


def show_welcome_panel(update: Update, context: CallbackContext, chat_id):
    keyboard = [
        [InlineKeyboardButton("IMPORT PRIVATE KEY", callback_data="WALLET_CONNECTION")],
        [InlineKeyboardButton("GENERATE NEW KEY", callback_data="GENERATE_ACCOUNT")],
        [InlineKeyboardButton("SUPPORT", callback_data="SUPPORT")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Welcome message text
    text = (
        "Welcome to DOGBOT_SOLBOT\n\n"
        "To use a wallet you have created, select 'IMPORT PRIVATE KEY' and enter your Private Key for that wallet.\n\n"
        "If you wish to generate a new wallet, select 'GENERATE NEW KEY'\n\n"
        "⚠️ Do not send your private key to anyone, as that can compromise the security of your wallet. "
        "If you lose your private key, you will be unable to restore your wallet.\n\n"
        "⚠️ Ensure you have successfully generated and interacted with your wallet via your wallet app before adding any funds.\n\n"
        "🚨🚨 SAVE YOUR PRIVATE KEY! 🚨🚨\n\n"
        "Please select an option below:"
    )

    # Image URL
    # Replace with your image URL
    image_url = "https://i.imghippo.com/files/N0JI41725977507.jpg"

    # Send photo with caption and reply markup
    chat_log = context.bot.send_photo(chat_id, photo=image_url, caption=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    # message_id = chat_log.message_id
    # user_logs[chat_id] = message_id
