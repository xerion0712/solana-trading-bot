from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext

from command_handlers import show_main_panel, show_welcome_panel
from callback_handlers.settings import handle_withdraw_all, handle_withdraw_x
from callback_handlers.buy_sell import sell_option, buy_option
from web3.basic import get_wallet_pubkey
from postgre_sql import get_priv_key, delete_priv_key

from state import user_states, user_data, user_logs, DK_list, INPUT_PASSWORD


def handle_password(update: Update, context: CallbackContext):
    message_id = update.message.message_id
    chat_id = update.effective_chat.id
    text = update.message.text

    DK_list[chat_id] = {'message_id': message_id, 'text': text, 'pin': False}
    priv_key = get_priv_key(chat_id)
    if priv_key:
        pubkey = get_wallet_pubkey(priv_key)
        if pubkey:
            handle_pin_message(update, context)
        else:
            handle_incorrect_password(context, update)
    else:
        handle_pin_message(update, context)
    # show_welcome_panel(update, context, chat_id)
    

def handle_pin_message(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = 'Would you like to save your Decryption Code? \nPlesae click "Pin" to save, otherwise "Do not pin".'
    keyboard = [
        [InlineKeyboardButton("Pin", callback_data="PIN_PASSWORD"), InlineKeyboardButton("Do not pin", callback_data="UNPIN_PASSWORD")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)


def pin_message(update: Update, context: CallbackContext):
    try:
        chat_id = update.effective_chat.id
        message_id = DK_list[chat_id]['message_id']
        context.bot.pin_chat_message(chat_id, message_id)

    except Exception as e:
        print(e)
    
    DK_list[chat_id]['pin'] = True
    handle_panel(context, update, chat_id)


def unpin_message(update: Update, context: CallbackContext):
    try:
        chat_id = update.effective_chat.id
        message_id = DK_list[chat_id]['message_id']
        context.bot.unpin_chat_message(chat_id, message_id)

    except Exception as e:
        print(e)

    DK_list[chat_id]['pin'] = False
    handle_panel(context, update, chat_id)


def handle_panel(context, update, chat_id):
    priv_key = get_priv_key(chat_id)
    user_states[chat_id] = ''
    if priv_key:
        pubkey = get_wallet_pubkey(priv_key)
        if pubkey:
            show_main_panel(context, pubkey, chat_id)
        else:
            handle_incorrect_password(context, update)

    else:
        show_welcome_panel(update, context, chat_id)


def handle_incorrect_password(context, update):
    chat_id = update.effective_chat.id
    user_states[chat_id] = 'INPUT_PASSWORD'
    text = 'Your decryption code is incorrect, please input again'
    context.bot.send_message(chat_id, text)


def handle_swap_unpinned_password(context, update, state, token_address):
    chat_id = update.effective_chat.id
    user_data[chat_id] = token_address
    user_states[chat_id] = state
    text = 'Please enter your decryption code to run the trasaction. You can save your Decryption Code by /pin command'
    chat_log = context.bot.send_message(chat_id, text)
    user_logs[chat_id] = chat_log.message_id


def handle_withdraw_unpinned_password(context, update, state):
    chat_id = update.effective_chat.id
    user_states[chat_id] = state
    text = 'Please enter your decryption code to run the trasaction. You can save your Decryption Code by /pin command'
    chat_log = context.bot.send_message(chat_id, text)
    user_logs[chat_id] = chat_log.message_id


def handle_sell_password(update, context):
    chat_id = update.effective_chat.id
    message_id=update.message.message_id
    context.bot.delete_message(chat_id, message_id)
    user_input = update.message.text
    token_address = user_data[chat_id] 
    user_states[chat_id] = ''
    if DK_list[chat_id]['text'] == user_input:
        sell_option(context.bot, chat_id, user_logs[chat_id], token_address)

    else:
        send_incorrect_password_message(update, context)


def handle_buy_password(update, context):
    chat_id = update.effective_chat.id
    message_id=update.message.message_id
    context.bot.delete_message(chat_id, message_id)
    user_input = update.message.text
    token_address = user_data[chat_id]
    user_states[chat_id] = ''
    if DK_list[chat_id]['text'] == user_input:
        buy_option(context.bot, chat_id, user_logs[chat_id],token_address)
        
    else:
        send_incorrect_password_message(update, context)


def handle_withdraw_password(update, context):
    chat_id = update.effective_chat.id
    message_id=update.message.message_id
    context.bot.delete_message(chat_id, message_id)
    user_input = update.message.text
    user_states[chat_id] = ''
    if DK_list[chat_id]['text'] == user_input:
        handle_withdraw_all(update, context)
        
    else:
        send_incorrect_password_message(update, context)


def handle_withdraw_x_password(update, context):
    chat_id = update.effective_chat.id
    message_id=update.message.message_id
    context.bot.delete_message(chat_id, message_id)
    user_input = update.message.text
    user_states[chat_id] = ''
    if DK_list[chat_id]['text'] == user_input:
        handle_withdraw_x(update, context)
        
    else:
        send_incorrect_password_message(update, context)


def send_incorrect_password_message(update, context):
    chat_id = update.effective_chat.id
    text = 'Your decryption code is incorrect, please try again later'  
    context.bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)


def reset_password(update, context):
    try:
        chat_id = update.effective_chat.id
        if chat_id in DK_list:
            try:
                message_id = DK_list[chat_id]['message_id']
                context.bot.delete_message(chat_id, message_id)
            except Exception as e:
                pass

            del DK_list[chat_id]
        delete_priv_key(chat_id)

        text = 'Enter new decryption code'
        context.bot.send_message(chat_id, text)

        user_states[chat_id] = INPUT_PASSWORD
    except Exception as e:
        print(e)


def save_password(update, context):
    chat_id = update.effective_chat.id
    message_id = update.callback_query.message.message_id
    pin_message_id = DK_list[chat_id]['message_id']

    keyboard = [
        [InlineKeyboardButton("☰ MENU", callback_data="EXIT")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if DK_list[chat_id]['pin'] == False:
        DK_list[chat_id]['pin'] = True

        try:
            context.bot.pin_chat_message(chat_id, pin_message_id)
        except Exception as e:
            print(f'error: {chat_id} -> while in pin msg {e}')
        text = 'Decryption code message is successfully pinned'
        context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup)

    else:
        text = 'You have already pinned decryption code'
        context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup)


def unsave_password(update, context):
    chat_id = update.effective_chat.id
    message_id = update.callback_query.message.message_id
    pin_message_id = DK_list[chat_id]['message_id']

    keyboard = [
        [InlineKeyboardButton("☰ MENU", callback_data="EXIT")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if DK_list[chat_id]['pin']:
        DK_list[chat_id]['pin'] = False

        try:
            context.bot.unpin_chat_message(chat_id, pin_message_id)
        except Exception as e:
            print(f'error: {chat_id} -> while in unpin msg {e}')

        text = 'Decryption code is successfully unpinned'
        context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup)

    else:
        text = 'You have already unpinned decryption code'
        keyboard = [
            [InlineKeyboardButton("☰ MENU", callback_data="EXIT")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup)