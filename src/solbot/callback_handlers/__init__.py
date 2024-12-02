import logging

from telegram import Update
from telegram.ext import CallbackContext, CallbackQueryHandler

from solbot.command_handlers import start_handler

from solbot.callback_handlers.buy_sell import buy_option, buy, custom_buy_option, sell_option, sell, custom_sell_option, input_token_address, batch_buy_amount_option, batch_sell_amount_option
from solbot.callback_handlers.sniper import active_sniper, create_new_snipe
from solbot.callback_handlers.settings import settings, export_private_key, disconnect_wallet_msg, disconnect_wallet, handle_gas_fee, handle_jito_fee, handle_switch_chain, handle_withdraw_all, handle_withdraw_x
from solbot.callback_handlers.dog_bot import handle_buy_dog_bot_amount
from solbot.callback_handlers.support import support
from solbot.callback_handlers.portfolio import handle_portfolio, handle_prev_portfolio, handle_next_portfolio
from solbot.callback_handlers.wallet_connection import send_wallet_buttons, connect_phantom_wallet, connect_solflare_wallet, generate_wallet, save_new_wallet
from solbot.callback_handlers.referral import referral_view, generate_qr, claim_rewards
from solbot.callback_handlers.watch_list import handle_token_watch_panel, handle_watch_list
from solbot.callback_handlers.limit_order import limit_order_view, limit_order_list, edit_limit_order_panel, edit_limit_order, cancel_all_limit_order, cancel_order_view_panel, cancel_order, lower_buy_percentage_multi, add_lower_buy_price_percentage_panel, add_lower_buy_price_dolar_panel, higher_buy_percentage_multi, higher_buy_price_percentage_panel, higher_buy_price_dolar_panel, stop_loss_percentage_multi, stop_loss_price_percentage_panel, stop_loss_price_dolar_panel, sell_profit_percentage_multi, sell_profit_price_percentage_panel, sell_profit_price_dolar_panel, define_preset_panel, edit_preset_sell_for_profit, apply_reset_profit_loss
from solbot.callback_handlers.decryption import send_unpinned_msg

from solbot.message_handlers.swap import handle_buy_sell_token_address
from solbot.message_handlers.password import pin_message, unpin_message, reset_password, handle_swap_unpinned_password, handle_withdraw_unpinned_password, save_password, unsave_password
from solbot.database import update_fee_info, update_tip_info, get_token_order_list, add_hot_token, remove_hot_token, add_watch_list, remove_watch_list, get_watch_list

from solbot.state import user_logs, user_states, user_data, DK_list, user_token, batch_token, current_view_option, preset_list, CUSTOM_BUY_AMOUNT, CUSTOM_SELL_PERCENTAGE, PRESET_PRICE_1, PRIORITY_MAPPING, BATCH_BUY_AMOUNT, BATCH_SELL_AMOUNT

logger = logging.getLogger(__name__)

def callback_query(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    chat_id = query.message.chat.id
    message_id = query.message.message_id

    user_logs[chat_id] = message_id

    if user_states[chat_id] != 'INPUT_PASSWORD':
        user_states[chat_id] = ''

    logger.info(f"callback: {chat_id} -> {data}")

    if data == 'WALLET_CONNECTION':
        send_wallet_buttons(update, context)

    elif data == 'PIN_PASSWORD':
        pin_message(update, context)

    elif data == 'RESET_PASSWORD':
        reset_password(update, context)

    elif data == 'SAVE_PASSWORD':
        save_password(update, context)

    elif data == 'UNSAVE_PASSWORD':
        unsave_password(update, context)

    elif data == 'GENERATE_ACCOUNT':
        generate_wallet(update, context)

    elif data == 'SAVE_NEW_WALLET':
        save_new_wallet(update, context)

    elif data == 'DELETE':
        context.bot.delete_message(chat_id, message_id)

    elif data == 'UNPIN_PASSWORD':
        unpin_message(update, context)

    elif data == 'ACTIVE_SNIPER':
        if DK_list[chat_id]['pin']:
            active_sniper(chat_id, message_id, context)

        else:
            send_unpinned_msg(update, context, 'sniping')


    elif data == 'SNIPENOW':
        create_new_snipe(update, context)

    elif data == 'GENERATE_QR':
        generate_qr(update, context)

    elif data == 'BUYSELL':
        input_token_address(update, context)

    elif data == 'BACK':
        context.bot.delete_message(chat_id, message_id)
        start_handler(update, context)

    elif data == 'GLOBAL_LIMIT':
        if DK_list[chat_id]['pin']:
            limit_order_list(update, context)

        else:
            send_unpinned_msg(update, context, 'limit option')

    elif data == 'REFERRAL':
        referral_view(update, context)

    elif data == 'REFERRAL_BACK':
        context.bot.delete_message(chat_id, message_id)
        referral_view(update, context, False)

    elif data == 'PHANTOM_WALLET':
        connect_phantom_wallet(update, context)

    elif data == 'SOLFLARE_WALLET':
        connect_solflare_wallet(update, context)

    elif data == 'DELETE_SNIPE_TOKEN':
        try:
            del user_data[chat_id]
            active_sniper(chat_id, message_id, context)
        except Exception:
            logger.exception(f"Failed to execute {data}")

    elif data == 'EXIT':
        user_states[chat_id] = ""
        context.bot.delete_message(chat_id, message_id)
        start_handler(update, context)

    elif data == 'WATCH_LIST':
        handle_watch_list(update, context)

    elif data == 'SETTINGS':
        settings(update, context)

    elif data == 'EXPORT':
        export_private_key(update, context)

    elif data == 'DISCONNECT_WALLET_PANEL':
        disconnect_wallet_msg(update, context)

    elif data == 'DISCONNECT_WALLET':
        disconnect_wallet(update, context)

    elif data == 'GAS_FEE':
        handle_gas_fee(update, context)

    elif data == 'JITO_TIP':
        handle_jito_fee(update, context)

    elif data == 'SWITCH_CHAIN':
        handle_switch_chain(update, context)

    elif data == 'WITHDRAW_ALL_SOL':
        try:
            chat_id = update.effective_chat.id
            if DK_list[chat_id]['pin']:
                handle_withdraw_all(update, context)

            else:
                handle_withdraw_unpinned_password(context, update, 'WITHDRAW_ALL_SOL_PASSWORD')

        except Exception:
            logger.exception(f"Failed to execute {data}")

    elif data == 'WITHDRAW_SOL_X':
        try:
            chat_id = update.effective_chat.id
            if DK_list[chat_id]['pin']:
                handle_withdraw_x(update, context)

            else:
                handle_withdraw_unpinned_password(context, update, 'WITHDRAW_X_SOL_PASSWORD')

        except Exception:
            logger.exception(f"Failed to execute {data}")

    elif data == 'BUY_DOGBOT_TOKEN':
        handle_buy_dog_bot_amount(update, context)

    elif data == 'SUPPORT':
        support(update, context)

    elif data == 'PORTFOLIO':
        current_view_option[chat_id] = 'PORTFOLIO'
        handle_portfolio(update, context)

    elif data.startswith('EXIT_FUN_'):
        token_address = data.split('_')[2]
        handle_buy_sell_token_address(update, context, token_address)

    elif data.startswith('EDIT_ORDER_'):
        token_address = data.split('_')[2]
        edit_limit_order_panel(update, context, token_address)

    elif data.startswith('ORDERDEL_'):
        token_address = data.split('_')[1]
        id = data.split('_')[2]
        cancel_order(update, context, token_address, int(id))

    elif data.startswith('BUYOPT_'):
        try:
            token_address = data.split('_')[1]
            if DK_list[chat_id]['pin']:
                buy_option(context.bot, chat_id, message_id, token_address)

            else:
                handle_swap_unpinned_password(context, update, "BUY_OPTION", token_address)

        except Exception:
            logger.exception(f"Failed to execute {data}")

    elif data.startswith('SELLOPT_'):
        try:
            chat_id = update.effective_chat.id
            token_address = data.split('_')[1]
            if DK_list[chat_id]['pin']:
                sell_option(context.bot, chat_id, message_id, token_address)

            else:
                handle_swap_unpinned_password(context, update, "SELL_OPTION", token_address)

        except Exception:
            logger.exception(f"Failed to execute {data}")

    elif data.startswith('CLAIM_REWARDS_'):
        claimable_amount = data.split('_')[2]
        claim_rewards(update, context, claimable_amount)

    elif data.startswith('BUYX_'):
        token_address = data.split('_')[1]
        amount = data.split('_')[2]
        buy(context.bot, chat_id, token_address, float(amount))

    elif data.startswith('SELLX_'):
        token_address = data.split('_')[1]
        amount = data.split('_')[2]
        sell(context.bot, chat_id, token_address, float(amount))

    elif data.startswith('CUSTOM_BUY_AMOUNT_'):
        user_states[chat_id] = CUSTOM_BUY_AMOUNT
        token = data.split('_')[3]
        user_token[chat_id] = token
        custom_buy_option(context.bot, chat_id, message_id, token)

    elif data.startswith('CUSTOM_SELL_PERCENT_'):
        user_states[chat_id] = CUSTOM_SELL_PERCENTAGE
        token = data.split('_')[3]
        user_token[chat_id] = token
        custom_sell_option(context.bot, chat_id, message_id, token)

    elif data.startswith('BATCHBUY_'):
        user_states[chat_id] = BATCH_BUY_AMOUNT
        token = data.split('_')[1]
        batch_token[chat_id] = {'token': token}
        batch_buy_amount_option(update, context, token)

    elif data.startswith('BATCHSELL_'):
        user_states[chat_id] = BATCH_SELL_AMOUNT
        token = data.split('_')[1]
        batch_token[chat_id] = {'token': token}
        batch_sell_amount_option(update, context, token)

    elif data.startswith('ADD_WATCH_'):
        token = data.split('_')[2]

        add_watch_list(chat_id, token)

        if current_view_option[chat_id] == 'PORTFOLIO':
            handle_portfolio(update, context, token)
        elif current_view_option[chat_id] == 'WATCH_LIST':
            handle_token_watch_panel(update, context, token)
        elif current_view_option[chat_id] == 'CONTRACT':
            context.bot.delete_message(chat_id, message_id)
            handle_buy_sell_token_address(update, context, token)

    elif data.startswith('DELETE_WATCH_'):
        token = data.split('_')[2]

        remove_watch_list(chat_id, token)

        if current_view_option[chat_id] == 'PORTFOLIO':
            handle_portfolio(update, context, token)
        elif current_view_option[chat_id] == 'WATCH_LIST':
            handle_token_watch_panel(update, context, token)
        elif current_view_option[chat_id] == 'CONTRACT':
            context.bot.delete_message(chat_id, message_id)
            handle_buy_sell_token_address(update, context, token)

    elif data.startswith('PREV_'):
        token = data.split('_')[1]
        watch_list = get_watch_list(chat_id)
        if watch_list and token in watch_list:
            idx = watch_list.index(token) - 1
            if idx == -1:
                idx = len(watch_list) - 1
            target = watch_list[idx]
            handle_token_watch_panel(update, context, target)

        else:
            handle_token_watch_panel(update, context, token)

    elif data.startswith('NEXT_'):
        token = data.split('_')[1]
        watch_list = get_watch_list(chat_id)
        if watch_list and token in watch_list:
            idx = watch_list.index(token) + 1
            if idx == len(watch_list):
                idx = 0
            target = watch_list[idx]
            handle_token_watch_panel(update, context, target)

        else:
            handle_token_watch_panel(update, context, token)

    elif data.startswith('ORDER_PREV_'):
        try:
            token = data.split('_')[2]
            order_list = get_token_order_list(chat_id)
            if len(order_list):
                if token in order_list:
                    prev_order = order_list[(order_list.index(token) - 1) % len(order_list)]
                    limit_order_view(update, context, prev_order)
                else:
                    limit_order_view(update, context, order_list[0])
            else:
                limit_order_list(update, context)
        except Exception:
            logger.exception(f"Failed to execute {data}")

    elif data.startswith('ORDER_NEXT_'):
        try:
            token = data.split('_')[2]
            order_list = get_token_order_list(chat_id)
            if len(order_list):
                if token in order_list:
                    next_order = order_list[(order_list.index(token) + 1) % len(order_list)]
                    limit_order_view(update, context, next_order)
                else:
                    limit_order_view(update, context, order_list[0])
            else:
                limit_order_list(update, context)

        except Exception:
            logger.exception(f"Failed to execute {data}")

    elif data.startswith('APPLY_TOKEN_'):
        token = data.split('_')[2]
        apply_reset_profit_loss(update, context, token)

    elif data.startswith('LIMIT_ORDER_RECORD_'):
        token = data.split('_')[3]
        if DK_list[chat_id]['pin']:
            limit_order_view(update, context, token)
        else:
            send_unpinned_msg(update, context, 'limit option')

    elif data.startswith('CANCEL_EDIT_'):
        user_logs[chat_id] = ''
        user_states[chat_id] = ''
        preset_list[chat_id] = {}
        token = data.split('_')[2]
        limit_order_view(update, context, token)

    elif data.startswith('SETHOTTOKEN_'):
        token = data.split('_')[1]
        add_hot_token(chat_id, token)
        limit_order_view(update, context, token)

    elif data.startswith('REMOVEHOTTOKEN_'):
        token = data.split('_')[1]
        remove_hot_token(chat_id, token)
        limit_order_view(update, context, token)

    elif data.startswith('BOOKX_'):
        token = data.split('_')[1]
        multi = data.split('_')[2]
        order_id = data.split('_')[3]
        lower_buy_percentage_multi(update, context, token, float(multi), int(order_id))

    elif data.startswith('BXP_'):
        token = data.split('_')[1]
        order_id = data.split('_')[2]
        add_lower_buy_price_percentage_panel(update, context, token, int(order_id))

    elif data.startswith('TBOOK_DOLLAR_'):
        token = data.split('_')[2]
        order_id = data.split('_')[3]
        add_lower_buy_price_dolar_panel(update, context, token, int(order_id))

    elif data.startswith('BOOKLOSS_'):
        token = data.split('_')[1]
        multi = data.split('_')[2]
        order_id = data.split('_')[3]
        higher_buy_percentage_multi(update, context, token, float(multi), int(order_id))

    elif data.startswith('BLOSSX_'):
        token = data.split('_')[1]
        order_id = data.split('_')[2]
        higher_buy_price_percentage_panel(update, context, token, int(order_id))

    elif data.startswith('BOOK_DOLLAR_'):
        token = data.split('_')[2]
        order_id = data.split('_')[3]
        higher_buy_price_dolar_panel(update, context, token, int(order_id))

    elif data.startswith('BUYHIGHERP_'):
        token = data.split('_')[1]
        multi = data.split('_')[2]
        order_id = data.split('_')[3]
        stop_loss_percentage_multi(update, context, token, float(multi), int(order_id))

    elif data.startswith('BHIGHERX_'):
        token = data.split('_')[1]
        order_id = data.split('_')[2]
        stop_loss_price_percentage_panel(update, context, token, int(order_id))

    elif data.startswith('HIGHER_DOLLAR_'):
        token = data.split('_')[2]
        order_id = data.split('_')[3]
        stop_loss_price_dolar_panel(update, context, token, int(order_id))

    elif data.startswith('DCAPERCENTAGE_'):
        token = data.split('_')[1]
        multi = data.split('_')[2]
        order_id = data.split('_')[3]
        sell_profit_percentage_multi(update, context, token, float(multi), int(order_id))

    elif data.startswith('DCAXP_'):
        token = data.split('_')[1]
        order_id = data.split('_')[2]
        sell_profit_price_percentage_panel(update, context, token, int(order_id))

    elif data.startswith('DCA_DOLLAR_'):
        token = data.split('_')[2]
        order_id = data.split('_')[3]
        sell_profit_price_dolar_panel(update, context, token, int(order_id))

    elif data.startswith('DEFINE_TOKEN_'):
        token = data.split('_')[2]
        define_preset_panel(update, context, token)

    elif data.startswith('EDIT_PRESET_'):
        token = data.split('_')[2]
        edit_preset_sell_for_profit(update, context, token, 'RRICE', 1, PRESET_PRICE_1)

    elif data.startswith('CANCEL_ORDER_'):
        token = data.split('_')[2]
        cancel_order_view_panel(update, context, token)

    elif data.startswith('CANCEL_ALL_'):
        token = data.split('_')[2]
        cancel_all_limit_order(update, context, token)

    elif data.startswith('ORDER_EDIT_'):
        token = data.split('_')[2]
        id = int(data.split('_')[3])
        edit_limit_order(update, context, token, id)

    elif data.startswith('TOKEN_WATCH_'):
        token = data.split('_')[2]
        current_view_option[chat_id] = 'WATCH_LIST'
        handle_token_watch_panel(update, context, token)

    elif data.startswith('PORTOLIO_PREV_'):
        text = data.split('_')[2]
        handle_prev_portfolio(update, context, text)

    elif data.startswith('PORTOLIO_NEXT_'):
        text = data.split('_')[2]
        handle_next_portfolio(update, context, text)

    elif data.endswith('_FEE_GAS'):
        level = data.split('_')[0]
        update_fee_info(chat_id, PRIORITY_MAPPING[level])
        handle_gas_fee(update, context)

    elif data.endswith('_JITO_TIP'):
        level = data.split('_')[0]
        update_tip_info(chat_id, PRIORITY_MAPPING[level])
        handle_jito_fee(update, context)


def callback_query_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(callback_query)

