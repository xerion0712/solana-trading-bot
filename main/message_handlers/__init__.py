import threading
from telegram import Update
from telegram.ext import CallbackContext, MessageHandler, Filters

from message_handlers.wallet_connection import handle_private_key_handler_phantom, handle_private_key_handler_solfare
from message_handlers.snipe import handle_snipe_token_address, handle_swap_token_amount, handle_snipe_token_amount
from message_handlers.swap import handle_buy_sell_token_address, handle_custom_buy_amount, handle_custom_sell_percentage, async_buy_sell_token_info_panel
from message_handlers.withdraw_sol import handle_withdraw_all, handle_withdraw_x, handle_withdraw_x_to_address
from message_handlers.password import handle_password, handle_buy_password, handle_sell_password, handle_withdraw_password, handle_withdraw_x_password
from web3.basic import get_validation_address

from state import user_states


def get_user_state(chat_id):
    return action_mapping.get(user_states.get(chat_id, ""), user_states.get(chat_id, {}))


action_mapping = {
    'IMPORT_NEW_ACCOUNT': handle_private_key_handler_phantom,
    'IMPORT_NEW_ACCOUNT_SOLFARE': handle_private_key_handler_solfare,
    'SNIPE_TOKEN_ADDRESS': handle_snipe_token_address,
    'SWAP_TOKEN_AMOUNT': handle_swap_token_amount,
    'SNIPE_TOKEN_AMOUNT': handle_snipe_token_amount,
    'BUY_SELL_TOKEN_ADDRESS': handle_buy_sell_token_address,
    'CUSTOM_BUY_AMOUNT': handle_custom_buy_amount,
    'CUSTOM_SELL_PERCENTAGE': handle_custom_sell_percentage,
    'WITHDRAW_ALL_SOL': handle_withdraw_all,
    'WITHDRAW_X_SOL': handle_withdraw_x,
    'INPUT_PASSWORD': handle_password,
    'BUY_OPTION': handle_buy_password,
    'SELL_OPTION': handle_sell_password,
    'WITHDRAW_ALL_SOL_PASSWORD': handle_withdraw_password,
    'WITHDRAW_X_SOL_PASSWORD': handle_withdraw_x_password,
}


def handle_user_message(update: Update, context: CallbackContext) -> None:
    try:
        chat_id = update.effective_chat.id
        user_input = update.message.text

        log_string = f'message: {chat_id} -> {user_input}'
        print(log_string)

        if chat_id in user_states and user_states[chat_id].startswith('WITHDRAW_SOL_TO_'):
            handle_withdraw_x_to_address(update, context)
        else:    
            user_state_action = get_user_state(chat_id)
            if user_state_action:
                print(f"State {chat_id} : {user_state_action.__name__}, Message: {user_input}")
                user_state_action(update, context)

            else:
                validation = get_validation_address(user_input)
                if validation:
                    buy_sell_token_info_panel_thread = threading.Thread(target=async_buy_sell_token_info_panel, args=(update, context), daemon=True)
                    buy_sell_token_info_panel_thread.start()
    except Exception as e:
        print(e)


def message_handler() -> MessageHandler:
    return MessageHandler(Filters.text & ~Filters.command, handle_user_message)
