import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext

from web3.basic import get_validation_address, transfer_sol
from postgre_sql import get_priv_key

from state import user_states

def handle_withdraw_all(update: Update, context: CallbackContext):
    def handle_withdraw_all_feature(update: Update, context: CallbackContext):
        chat_id = update.effective_chat.id
        text = update.message.text

        validation = get_validation_address(text)
        if validation:
            confirm_message = context.bot.send_message(chat_id, 'Transfering now...')
            hex_priv_key = get_priv_key(chat_id)
            flag, res = transfer_sol(hex_priv_key, text, 100)
            context.bot.delete_message(chat_id, confirm_message.message_id)
            if flag:
                message = f'Withdraw Transaction Success to <code>{text}</code>'
                keyboard = [[InlineKeyboardButton("🌐 Tx Hash", url=f"https://solscan.io/tx/{str(res)}")], [InlineKeyboardButton("⬅️ BACK", callback_data="SETTINGS")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                context.bot.send_message(chat_id, message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

            else: 
                message = f'Withdraw Transaction Failed to <code>{text}</code>'
                keyboard = [[InlineKeyboardButton("⬅️ BACK", callback_data="SETTINGS")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                context.bot.send_message(chat_id, message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

        else: 
            message = 'Invalid address'
            keyboard = [[InlineKeyboardButton("⬅️ BACK", callback_data="SETTINGS")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            context.bot.send_message(chat_id, message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    handle_withdraw_all_thread = threading.Thread(target=handle_withdraw_all_feature, args=(update, context), daemon=True)
    handle_withdraw_all_thread.start()


def handle_withdraw_x(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text

    validation = get_validation_address(text)
    if validation:
        user_states[chat_id] = f'WITHDRAW_SOL_TO_{text}'
        message = f'Enter the Solana (%) of your balance to withdraw to {text}'
        keyboard = [[InlineKeyboardButton("⬅️ BACK", callback_data="SETTINGS")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id, message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else: 
        message = 'Invalid address'
        keyboard = [[InlineKeyboardButton("⬅️ BACK", callback_data="SETTINGS")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id, message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)


def handle_withdraw_x_to_address(update: Update, context: CallbackContext):
    def withdraw_feature(update: Update, context: CallbackContext):
        try:
            chat_id = update.effective_chat.id
            text = update.message.text

            address = user_states[chat_id].split('_')[3]
            try:
                amount = float(text)

                if 0 < amount  <= 100:
                    confirm_message = context.bot.send_message(chat_id, 'Transfering now...')
                    hex_priv_key = get_priv_key(chat_id)
                    flag, res = transfer_sol(hex_priv_key, address, float(text))
                    context.bot.delete_message(chat_id, confirm_message.message_id)
                    if flag:
                        message = f'Withdraw Transaction Success to <code>{address}</code>'
                        keyboard = [[InlineKeyboardButton("🌐 Tx Hash", url=f"https://solscan.io/tx/{str(res)}"), InlineKeyboardButton("⬅️ BACK", callback_data="SETTINGS")]]
                    else: 
                        message = f'Withdraw Transaction Failed to <code>{address}</code>'
                        keyboard = [[InlineKeyboardButton("⬅️ BACK", callback_data="SETTINGS")]]
                else:
                    message = 'Please input valid number in the range from 0 to 100'
                    keyboard = [[InlineKeyboardButton("⬅️ BACK", callback_data="SETTINGS")]]
                    
            except Exception as e:
                message = 'Please input a valid number in the range from 0 to 100'
                keyboard = [[InlineKeyboardButton("⬅️ BACK", callback_data="SETTINGS")]]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            context.bot.send_message(chat_id, message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

        except Exception as e:
            print(chat_id, 'withdraw error', e)
            keyboard = [[InlineKeyboardButton("⬅️ BACK", callback_data="SETTINGS")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            context.bot.send_message(chat_id, 'Some error occured while transfering', reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    withdraw_thread = threading.Thread(target=withdraw_feature, args=(update, context), daemon=True)
    withdraw_thread.start()

