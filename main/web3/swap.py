import threading
import asyncio
import math
import base64
from solana.rpc.commitment import Confirmed
from solders.transaction import VersionedTransaction  # type: ignore
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from solders.keypair import Keypair  # type: ignore
from solders import message
from time import sleep
from solana.rpc.types import TxOpts
from jupiter_python_sdk.jupiter import Jupiter

from postgre_sql import get_priv_key
from web3.basic import get_async_client, get_token_information
from web3.jupiter import get_quote, get_swap_data

from state import user_data, LAMPORTS_PER_SOL, WSOL

async def buy_token(bot, chat_id, token, amount):
    try:
        value_to_sell = int(amount * LAMPORTS_PER_SOL)
        hex_priv_key = get_priv_key(chat_id)
        keypair = Keypair.from_base58_string(hex_priv_key)
        async_client = get_async_client()

        quote = get_quote(WSOL, token, value_to_sell, 'ExactIn', 100)
        transaction_data = get_swap_data(quote, str(keypair.pubkey()))
        raw_transaction = VersionedTransaction.from_bytes(base64.b64decode(transaction_data))
        signature = keypair.sign_message(message.to_bytes_versioned(raw_transaction.message))
        signed_txn = VersionedTransaction.populate(raw_transaction.message, [signature])
        # blockhash = await async_client.get_latest_blockhash(Confirmed)
        # opts = TxOpts(skip_preflight=True, preflight_commitment=Confirmed, last_valid_block_height=blockhash)
        opts = TxOpts(skip_preflight=False, preflight_commitment=Confirmed)
        tx = await async_client.send_raw_transaction(txn=bytes(signed_txn), opts=opts)
        print(f'{chat_id}: buy_sig -> {tx.value}')
        keyboard = [
            [InlineKeyboardButton("🌐 Tx Hash", url=f"https://solscan.io/tx/{str(tx.value)}"), InlineKeyboardButton("⬅️ BACK",callback_data=f"EXIT_FUN_{token}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        confirm_message = bot.send_message(chat_id=chat_id, text=f"⏳ Buy transaction processed successfully. Please wait for confirmation. You will receive it within seconds, depending on the Solana Network.", reply_markup=reply_markup)

        try:
            confirm_result = await async_client.confirm_transaction(tx.value, Confirmed)
            # bot.delete_message(chat_id, message_id=confirm_message.message_id)
            if confirm_result.value[0].err == None:
                print(f"Transaction sent: https://explorer.solana.com/tx/{str(tx.value)}")

                market_cap = get_token_information(str(token))[5]
                sol_price = get_token_information(str(WSOL))[3]

                keyboard = [
                    [InlineKeyboardButton("🌐 Tx Hash", url=f"https://solscan.io/tx/{str(tx.value)}"), InlineKeyboardButton("⬅️ BACK",callback_data=f"EXIT_FUN_{token}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                sol_amount = f"{value_to_sell / LAMPORTS_PER_SOL:.8f}".rstrip('0').rstrip('.')
                total_price = f"{value_to_sell / LAMPORTS_PER_SOL * float(sol_price):.8f}".rstrip('0').rstrip('.')
                formatted_market_cap = f"{float(market_cap):,.2f}".rstrip('0').rstrip('.')
                bot.edit_message_text(chat_id=chat_id, message_id=confirm_message.message_id, text=f"✅ Buy Transaction succeeded\n💰 Purchased {sol_amount}SOL for {total_price} $\n📈 MC - {formatted_market_cap} USD", reply_markup=reply_markup)

            else:
                print(f"Buy Transaction failed with error: {confirm_result.value[0].err}")
                keyboard = [[InlineKeyboardButton("⬅️ BACK",callback_data=f"EXIT_FUN_{token}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                bot.edit_message_text(chat_id=chat_id, message_id=confirm_message.message_id, text=f"❌ Buy Transaction Expired.\nDue to high transaction volume, the Solana network is experiencing congestion, causing many nodes to be temporarily unavailable. Please try again later.", reply_markup=reply_markup)

        except Exception as e:
            # bot.delete_message(chat_id, message_id=confirm_message.message_id)
            print(f"Buy Transaction expired with error: {e}")
            keyboard = [[InlineKeyboardButton("⬅️ BACK",callback_data=f"EXIT_FUN_{token}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(chat_id=chat_id, message_id=confirm_message.message_id, text=f"❌ Buy Transaction Failed.\nPlease try again later.", reply_markup=reply_markup)

    except Exception as e:
        keyboard = [
            [InlineKeyboardButton("⬅️ BACK",callback_data=f"EXIT_FUN_{token}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id, "Token is not tradable. Must be some fault in it's trading", reply_markup=reply_markup)
        print("Buy Exchange has err", e)


def handle_buy_token(bot, chat_id, token, amount):
    def async_buy_token(bot, chat_id, token, amount):
        asyncio.run(buy_token(bot, chat_id, token, amount))
    
    buy_token_thread = threading.Thread(target=async_buy_token, args=(bot, chat_id, token, amount), daemon=True)
    buy_token_thread.start()


async def sell_token(bot, chat_id, token, amount, decimals):
    try:
        hex_priv_key = get_priv_key(chat_id)
        keypair = Keypair.from_base58_string(hex_priv_key)
        async_client = get_async_client()

        quote = get_quote(token, WSOL, amount, 'ExactIn', 100)
        transaction_data = get_swap_data(quote, str(keypair.pubkey()))
        raw_transaction = VersionedTransaction.from_bytes(base64.b64decode(transaction_data))
        signature = keypair.sign_message(message.to_bytes_versioned(raw_transaction.message))
        signed_txn = VersionedTransaction.populate(raw_transaction.message, [signature])
        # blockhash = await async_client.get_latest_blockhash(Confirmed)
        # opts = TxOpts(skip_preflight=True, preflight_commitment=Confirmed, last_valid_block_height=blockhash)
        opts = TxOpts(skip_preflight=False, preflight_commitment=Confirmed)
        tx = await async_client.send_raw_transaction(txn=bytes(signed_txn), opts=opts)
        print(f'{chat_id}: sell_sig -> {tx.value}')
        keyboard = [
            [InlineKeyboardButton("🌐 Tx Hash", url=f"https://solscan.io/tx/{str(tx.value)}"), InlineKeyboardButton("⬅️ BACK",callback_data=f"EXIT_FUN_{token}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        confirm_message = bot.send_message(chat_id=chat_id, text=f"⏳ Sell transaction processed successfully. Please wait for confirmation. You will receive it within seconds, depending on the Solana Network.", reply_markup=reply_markup)

        try:
            confirm_result = await async_client.confirm_transaction(tx.value, Confirmed)
            # bot.delete_message(chat_id, message_id=confirm_message.message_id)
            if confirm_result.value[0].err == None:
                print(f"Transaction sent: https://explorer.solana.com/tx/{str(tx.value)}")

                token_symbol, _, _, price, _, market_cap, _, _= get_token_information(str(token))

                keyboard = [
                    [InlineKeyboardButton("🌐 Tx Hash", url=f"https://solscan.io/tx/{str(tx.value)}"), InlineKeyboardButton("☰ Menu", callback_data=f"EXIT_FUN_{token}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                token_amount = f"{amount / math.pow(10,decimals):.8f}".rstrip('0').rstrip('.')
                total_price = f"{amount / math.pow(10,decimals) * float(price):.8f}".rstrip('0').rstrip('.')
                formatted_market_cap = f"{float(market_cap):,.2f}".rstrip('0').rstrip('.')
                bot.edit_message_text(chat_id=chat_id, message_id=confirm_message.message_id, text=f"✅ Sell Transaction succeeded\n💰 Purchased {token_amount}{token_symbol} for {total_price} $\n📈 MC - {formatted_market_cap} USD", reply_markup=reply_markup)

            else:
                print(f"Sell Transaction failed with error: {confirm_result.value[0].err == None}")
                keyboard = [[InlineKeyboardButton("☰ Menu", callback_data=f"EXIT_FUN_{token}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                bot.edit_message_text(chat_id=chat_id, message_id=confirm_message.message_id, text=f"❌ Sell Transaction Expired.\nDue to high transaction volume, the Solana network is experiencing congestion, causing many nodes to be temporarily unavailable. Please try again later.", reply_markup=reply_markup)

        except Exception as e:
            bot.delete_message(chat_id, message_id=confirm_message.message_id)
            print(f"Sell Transaction expired with error: {e}")
            keyboard = [[InlineKeyboardButton("☰ Menu", callback_data=f"EXIT_FUN_{token}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(chat_id=chat_id, message_id=confirm_message.message_id, text=f"❌ Sell Transaction Failed.\nPlease try again later.", reply_markup=reply_markup)

    except Exception as e:
        keyboard = [
            [InlineKeyboardButton("☰ MENU", callback_data=f"EXIT_FUN_{token}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id, "Token is not tradable. Must be some fault in it's trading", reply_markup=reply_markup)
        print("Sell Exchange has err", e)


def handle_sell_token(bot, chat_id, token, amount, decimals):
    def async_sell_token(bot, chat_id, token, amount, decimals):
        asyncio.run(sell_token(bot, chat_id, token, amount, decimals))
    
    sell_token_thread = threading.Thread(target=async_sell_token, args=(bot, chat_id, token, amount, decimals), daemon=True)
    sell_token_thread.start()


def snipe_token(bot, chat_id, token, amount):
    token_info = get_token_information(token)
    flag = False

    while token_info == 0:
        sleep(2)
        if chat_id not in user_data:
            return
        token_info = get_token_information(token)

    def async_buy_token(bot, chat_id, token, amount):
        asyncio.run(buy_token(bot, chat_id, token, amount))
    
    buy_token_thread = threading.Thread(target=async_buy_token, args=(bot, chat_id, token, amount), daemon=True)
    buy_token_thread.start()
