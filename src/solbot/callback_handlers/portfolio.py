import logging
import asyncio
import threading

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, Update, InlineKeyboardButton
from telegram.ext import CallbackContext
from solders.keypair import Keypair # type: ignore

from solbot.web3.basic import  get_token_authority, get_token_balance, get_token_portfolio, get_client, get_token_information, format_number
from solbot.database import get_priv_key, get_watch_list

from solbot.state import WSOL, LAMPORTS_PER_SOL

logger = logging.getLogger(__name__)

async def portfolio(update: Update, context: CallbackContext, text:str):
    chat_id = update.effective_chat.id
    message_id = update.callback_query.message.message_id
    try:
        token_symbol, token_name, pairAddress, price, token_liquidity, market_cap, price_change, image_url = get_token_information(text)
        sol_price = get_token_information(WSOL)[3]
        formatted_price_change = f"5m: {price_change['m5']}%  1h: {price_change['h1']}%  6h: {price_change['h6']}%  24h: {price_change['h24']}%"

        mutable_data, mintable_data, renounce_data = await (get_token_authority(text))

        solana_client = get_client()
        hex_priv_key = get_priv_key(chat_id)
        sol_balance = solana_client.get_balance(Keypair.from_base58_string(hex_priv_key).pubkey(), "confirmed").value
        token_balance, decimal_balance = get_token_balance(str(Keypair.from_base58_string(hex_priv_key).pubkey()), text)

        message = (
            f"<b>Portfolio View</b>\n"
            f"<u><b>{token_symbol}</b></u>\n"
            f"<code>{text}</code>\n\n"
            f"Price: <b>{float(price)/float(sol_price):,.6f} SOL / ${float(price):,.6f}</b>\n"
            f"Liq: <b>{format_number(float(token_liquidity)/float(sol_price))} SOL / ${format_number(token_liquidity)}</b>\n"
            f"MCap: <b>${format_number(market_cap)}</b>\n"
            f"{formatted_price_change}\n\n"
            f"<b>IMMUTABLE METADATA:</b> {'✅' if bool(mutable_data) else '❌'}\n"
            f"<b>MINT AUTH REVOKED:</b> {'✅' if bool(mintable_data) else '❌'}\n"
            f"<b>RENOUNCED:</b> {'✅' if bool(renounce_data) else '❌'}\n\n"
            f"<u>Your Holdings</u>\n"
            f"SOL: <b>{float(sol_balance)/LAMPORTS_PER_SOL:,.4f} SOL / ${float(sol_balance)/LAMPORTS_PER_SOL * float(sol_price):,.2f}</b>\n"
            f"Token: <b>{token_balance:,.4f} / ${float(token_balance) * float(price):,.2f}</b>\n"
        )

        watch_list = get_watch_list(chat_id)
        if watch_list and text in watch_list:
            watch_button = InlineKeyboardButton("Remove from Watchlist", callback_data=f"DELETE_WATCH_{text}")
        else:
            watch_button = InlineKeyboardButton("Add to Watchlist", callback_data=f"ADD_WATCH_{text}")

        keyboard = [
            [InlineKeyboardButton("BUY", callback_data=f"BUYOPT_{text}"), InlineKeyboardButton("SELL", callback_data=f"SELLOPT_{text}")],
            [watch_button, InlineKeyboardButton("LIMIT ORDERS", callback_data=f"LIMIT_ORDER_RECORD_{text}")],
            [InlineKeyboardButton("Solscan", url=f"https://solscan.io/account/{text}"), InlineKeyboardButton("📈 CHART", url=f"https://dexscreener.com/solana/{str(text)}")],
            [InlineKeyboardButton("⬅️ Prev", callback_data=f"PORTOLIO_PREV_{text}"), InlineKeyboardButton("☰ MENU", callback_data="EXIT"), InlineKeyboardButton("Next ➡️", callback_data=f"PORTOLIO_NEXT_{text}")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    except Exception:
        logger.exception("Failed while executing portfolio")
        context.bot.send_message(chat_id, 'Some error occured')


def handle_portfolio_thread(update, context, text):
    asyncio.run(portfolio(update, context, text))


def handle_portfolio(update: Update, context: CallbackContext, token:str = ''):
    chat_id = update.effective_chat.id
    message_id = update.callback_query.message.message_id
    if token:
        portfolio_thread = threading.Thread(target=handle_portfolio_thread, args=(update, context, token), daemon=True)
        portfolio_thread.start()
    else:
        hex_priv_key = get_priv_key(chat_id)
        pubkey = Keypair.from_base58_string(hex_priv_key).pubkey()
        portfolio_list = get_token_portfolio(pubkey)
        if len(portfolio_list) > 0:
            text = portfolio_list[0]['token_address']

            portfolio_thread = threading.Thread(target=handle_portfolio_thread, args=(update, context, text), daemon=True)
            portfolio_thread.start()

        else:
            handle_no_portfolio(update, context)


def handle_no_portfolio(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    message_id = update.callback_query.message.message_id
    text = 'You have no tokens in your wallet'
    keyboard = [
        [InlineKeyboardButton("☰ MENU", callback_data="EXIT")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

def get_portfolio_index(chat_id, token):
    hex_priv_key = get_priv_key(chat_id)
    pubkey = Keypair.from_base58_string(hex_priv_key).pubkey()
    portfolio_list = get_token_portfolio(pubkey)
    return next((i for i, item in enumerate(portfolio_list) if item["token_address"] == token), -1), len(portfolio_list), portfolio_list


def handle_prev_portfolio(update: Update, context: CallbackContext, token:str):
    chat_id = update.effective_chat.id

    idx, length, portfolio_list = get_portfolio_index(chat_id, token)

    if not portfolio_list:
        handle_no_portfolio(update, context)

    else:
        idx = (idx - 1) % length if idx != -1 else 0

        portfolio_thread = threading.Thread(target=handle_portfolio_thread, args=(update, context, portfolio_list[idx]['token_address']), daemon=True)
        portfolio_thread.start()


def handle_next_portfolio(update: Update, context: CallbackContext, token:str):
    chat_id = update.effective_chat.id

    idx, length, portfolio_list = get_portfolio_index(chat_id, token)

    if not portfolio_list:
        handle_no_portfolio(update, context)

    else:
        idx = (idx + 1) % length if idx != -1 else 0

        portfolio_thread = threading.Thread(target=handle_portfolio_thread, args=(update, context, portfolio_list[idx]['token_address']), daemon=True)
        portfolio_thread.start()
