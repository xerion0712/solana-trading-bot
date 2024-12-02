import threading
from telegram import Update
from telegram.ext import CallbackContext, MessageHandler, Filters

from solbot.message_handlers.wallet_connection import handle_private_key_handler_phantom, handle_private_key_handler_solfare
from solbot.message_handlers.snipe import handle_snipe_token_address, handle_swap_token_amount, handle_snipe_token_amount
from solbot.message_handlers.swap import handle_buy_sell_token_address, handle_custom_buy_amount, handle_custom_sell_percentage, async_buy_sell_token_info_panel, handle_batch_buy_amount, handle_batch_buy_tx_count, handle_batch_buy_delay, handle_batch_sell_amount, handle_batch_sell_tx_count, handle_batch_sell_delay
from solbot.message_handlers.withdraw_sol import handle_withdraw_all, handle_withdraw_x, handle_withdraw_x_to_address
from solbot.message_handlers.password import handle_password, handle_buy_password, handle_sell_password, handle_withdraw_password, handle_withdraw_x_password
from solbot.message_handlers.limit_order import handle_lower_buy_percentage, handle_lower_buy_amount_percentage, handle_lower_buy_price_dollar, handle_higher_buy_percentage, handle_higher_buy_amount_percentage, handle_higher_buy_price_dollar, handle_stop_loss_amount_percentage, handle_stop_loss_percentage, handle_stop_loss_price_dollar, handle_sell_profit_amount_percentage, handle_sell_profit_percentage, handle_sell_profit_price_dollar
from solbot.callback_handlers.limit_order import handle_preset_value

from solbot.web3.basic import get_validation_address

from solbot.state import user_states

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
    'LOWER_BUY_AMOUNT_PERCENTAGE': handle_lower_buy_amount_percentage,
    'LOWER_BUY_PRICE_PERCENTAGE': handle_lower_buy_percentage,
    'LOWER_BUY_AMOUNT_DOLAR': handle_lower_buy_price_dollar,
    'HIGHER_BUY_AMOUNT_PERCENTAGE': handle_higher_buy_amount_percentage,
    'HIGHER_BUY_PRICE_PERCENTAGE': handle_higher_buy_percentage,
    'HIGHER_BUY_AMOUNT_DOLAR': handle_higher_buy_price_dollar,
    'STOP_LOSS_AMOUNT_PERCENTAGE': handle_stop_loss_amount_percentage,
    'STOP_LOSS_PRICE_PERCENTAGE': handle_stop_loss_percentage,
    'STOP_LOSS_AMOUNT_DOLAR': handle_stop_loss_price_dollar,
    'SELL_PROFIT_AMOUNT_PERCENTAGE': handle_sell_profit_amount_percentage,
    'SELL_PROFIT_PRICE_PERCENTAGE': handle_sell_profit_percentage,
    'SELL_PROFIT_AMOUNT_DOLAR': handle_sell_profit_price_dollar,
    'BATCH_BUY_AMOUNT': handle_batch_buy_amount,
    'BATCH_BUY_TX_COUNT': handle_batch_buy_tx_count,
    'BATCH_BUY_DELAY': handle_batch_buy_delay,
    'BATCH_SELL_AMOUNT': handle_batch_sell_amount,
    'BATCH_SELL_TX_COUNT': handle_batch_sell_tx_count,
    'BATCH_SELL_DELAY': handle_batch_sell_delay
}


def handle_user_message(update: Update, context: CallbackContext) -> None:
    try:
        chat_id = update.effective_chat.id
        user_input = update.message.text

        if chat_id in user_states and user_states[chat_id].startswith('WITHDRAW_SOL_TO_'):
            handle_withdraw_x_to_address(update, context)
        elif chat_id in user_states and user_states[chat_id].startswith('PRESET_'):
            handle_preset_value(update, context)
        else:    
            user_state_action = get_user_state(chat_id)
            if user_state_action:
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
