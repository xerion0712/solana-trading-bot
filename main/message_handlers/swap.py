import asyncio
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext
from solders.keypair import Keypair  # type: ignore

from web3.basic import get_validation_address, get_token_information, get_token_authority, get_token_balance, get_client, format_number
from callback_handlers.buy_sell import buy, sell
from postgre_sql import get_priv_key

from state import user_logs, watch_list, user_token, WSOL, LAMPORTS_PER_SOL

async def buy_sell_token_info_panel(update: Update, context: CallbackContext, token_address = None) -> None:
    chat_id = update.effective_chat.id
    message_id = user_logs[chat_id]
    if token_address:
        text = token_address
    else:
        text = update.message.text

    validation = get_validation_address(text)

    if validation:
        try:
            token_symbol, _, _, price, token_liquidity, market_cap, price_change, image_url = get_token_information(text)
            sol_price = get_token_information(WSOL)[3]
            formatted_price_change = f"5m: {price_change['m5']}%  1h: {price_change['h1']}%  6h: {price_change['h6']}%  24h: {price_change['h24']}%"

            mutable_data, mintable_data, renounce_data = await (get_token_authority(text))

            solana_client = get_client()
            hex_priv_key = get_priv_key(chat_id)
            sol_balance = solana_client.get_balance(Keypair.from_base58_string(hex_priv_key).pubkey(), "confirmed").value
            token_balance = get_token_balance(str(Keypair.from_base58_string(hex_priv_key).pubkey()), text)

            message = (
                f"<b>Contract Address View</b>\n"
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
            
            if chat_id in watch_list and text in watch_list[chat_id]:
                watch_button = InlineKeyboardButton("Remove from Watchlist", callback_data=f"DELETE_WATCH_{text}")
            else:
                watch_button = InlineKeyboardButton("Add to Watchlist", callback_data=f"ADD_WATCH_{text}")

            keyboard = [
                [InlineKeyboardButton("BUY", callback_data=f"BUYOPT_{text}"), InlineKeyboardButton("SELL", callback_data=f"SELLOPT_{text}")],
                [watch_button, InlineKeyboardButton("LIMIT ORDERS", callback_data=f"LIMIT_ORDER_RECORD_{text}")],
                [InlineKeyboardButton("Solscan", url=f"https://solscan.io/account/{text}"), InlineKeyboardButton("📈 CHART", url=f"https://dexscreener.com/solana/{str(text)}")],
                [InlineKeyboardButton("⬅️ Prev", callback_data=f"PREV_{text}"), InlineKeyboardButton("☰ MENU", callback_data="EXIT"), InlineKeyboardButton("Next ➡️", callback_data=f"NEXT_{text}")]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            context.bot.delete_message(chat_id, message_id)
            # if image_url:
            #     context.bot.sendPhoto(chat_id, photo=image_url, caption=message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            # else:
            context.bot.send_message(chat_id, message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

            # context.bot.edit_message_text(chat_id, message_id, message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        except Exception as e:
            print(chat_id, 'swap error', e)
            message = 'Invalid Token Address, Kindly put the right address to buy/sell'
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("☰ MENU", callback_data="EXIT")]
            ])
            context.bot.send_message(chat_id, message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    else:
        message = 'Invalid Token Address, Kindly put the right address to buy/sell'
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("☰ MENU", callback_data="EXIT")]
        ])
        context.bot.send_message(chat_id, message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

def async_buy_sell_token_info_panel(update, context, token_address = None):
    asyncio.run(buy_sell_token_info_panel(update, context, token_address))

def handle_buy_sell_token_address(update: Update, context: CallbackContext, token_address=None) -> None:
    buy_sell_token_info_panel_thread = threading.Thread(target=async_buy_sell_token_info_panel, args=(update, context, token_address), daemon=True)
    buy_sell_token_info_panel_thread.start()

def handle_custom_buy_amount(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text

    token_address = user_token[chat_id] 
    buy(context.bot, chat_id, token_address,float(text))

def handle_custom_sell_percentage(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text

    token_address = user_token[chat_id] 
    sell(context.bot, chat_id, token_address,float(text))