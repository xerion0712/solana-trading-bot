from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.ext import CallbackContext
from solders.pubkey import Pubkey # type: ignore

from web3.basic import get_token_information, format_number, get_wallet_pubkey, get_client, get_token_balance
from postgre_sql import get_token_order, get_token_order_list, get_priv_key, delete_all_orders, delete_order
from state import WSOL, LAMPORTS_PER_SOL


def limit_order_view(update: Update, context: CallbackContext, token_addr:str):
    try:
        chat_id = update.effective_chat.id
        message_id = update.callback_query.message.message_id
        result = get_token_order(chat_id, token_addr)

        token_symbol, token_name, pair_address, usd_price, token_liquidity, market_cap, price_change, image_url = get_token_information(token_addr)
        sol_price = get_token_information(WSOL)[3]
        status = "Active" # Inactive
        is_hot_token = False

        if is_hot_token == False:
            button = InlineKeyboardButton("Set as HOT TOKEN",callback_data=f"SETHOTTOKEN:{token_addr}")
        else:
            button = InlineKeyboardButton("Remove as HOT TOKEN",callback_data=f"REMOVEHOTTOKEN:{token_addr}")

        message = (
                f"<u><b>LIMIT ORDERS</b></u>\n\n"
                f"Token: {token_symbol}\n"
                f"CA: <code>{token_addr}</code>\n"
                f"Price: <b>${format_number(float(usd_price))}</b>\n"
                f"Liq: <b>{format_number(float(token_liquidity) / float(sol_price))} SOL / ${format_number(float(token_liquidity))}</b>\n"
                f"Mcap: <b>${format_number(float(market_cap))}</b>\n"
                f"Status: <b>{status}</b>\n\n"
                f"<b>Note</b> Only one token can be defined as hot token. This means that the orders will be scanned every second. All limit orders for other tokens will be scanned once per minute.\n\n<i><b>To create or change a limit order: press Edit Order button</b></i>\n\n"
                f"----------------------------------------------------\n"
                f"<b>Order 1-3 Sell For Profit</b>\n"
            )
        for idx, record in enumerate(result):
            if idx in (0, 1, 2, 4):
                price = record[1]
                amount = record[2]
                load = loading_num(usd_price, price)
                if idx in (0, 1, 2):
                    if record[0] == 0:
                        message += f"{idx + 1}: No-Order\n\n"
                    else:
                        message += f"{idx + 1}: % Higher than Current Price: <b>{load}%</b>\nSell Price in USD: <b>{price:,.6f}</b>\n% of token to Sell: <b>{amount}</b>\n\n"
                else:
                    message += "----------------------------------------------------\n"
                    message += f"<b>Order 5: Buy Higher (e.g. Breakout)</b>\n"
                    if record[0] == 0:
                        message += f"{idx + 1}: No-Order\n\n"
                    else:
                        message += f"{idx + 1}: % Higher than Current Price: <b>{load}%</b>\nBuy Price in USD: <b>{price:,.6f}</b>\nSOL to Spend: <b>{amount}</b>\n\n"


            if idx in (3, 5, 6, 7):
                if idx == 5:
                    message += "----------------------------------------------------\n"
                    message += f"<b>Order 6-8 Buy Lower (e.g. Dip)</b>\n"

                if idx == 3:
                    message += "----------------------------------------------------\n"
                    message += f"<b>Order 4: Sell For Loss (Stop Loss)</b>\n"

                if record[0] == 0:
                    message += f"{idx + 1}: No-Order\n\n"

                else:
                    price = record[1]
                    amount = record[2]
                    load = loading_negative_num(usd_price, price)

                    if idx in (6, 7, 8):
                        message += f"{idx + 1}: % Lower than Current Price: <b>{load}%</b>\nBuy Price in USD: <b>{price:,.6f}</b>\nSOL to Spend: <b>{amount}</b>\n\n"
                    else:
                        message += f"{idx + 1}: % Higher than Current Price: <b>{load}%</b>\nBuy Price in USD: <b>{price:,.6f}</b>\nSOL to Spend: <b>{amount}</b>\n\n"

        keyboard  = [
            [InlineKeyboardButton("EDIT ORDER",callback_data=f"EDIT_ORDER_{token_addr}"),InlineKeyboardButton("CANCEL ORDER",callback_data=f"CANCEL_ORDER_{token_addr}")],
            [button],
            # [InlineKeyboardButton("APPLY SELL PRESETS",callback_data=f"APPLY_TOKEN_{token_addr}"),InlineKeyboardButton("DEFINE SELL PRESETS",callback_data=f"DEFINE_TOKEN_{token_addr}")],
            [InlineKeyboardButton("REFRESH",callback_data=f"LIMIT_ORDER_RECORD_{token_addr}"),InlineKeyboardButton("CANCEL All",callback_data=f"CANCEL_ALL_{token_addr}")],
            [InlineKeyboardButton("⬅️ PREV", callback_data="PREV_ORDER"),InlineKeyboardButton("NEXT ➡️", callback_data="NEXT_ORDER")],
            [InlineKeyboardButton("☰ MENU", callback_data="EXIT"),InlineKeyboardButton("BUY / SELL", callback_data=f"EXIT_FUN_{token_addr}")] # should check
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    except Exception as e:
        print('limit_order_view: error', e)


def loading_num(current_value, target_value):
    current_value = float(current_value)
    target_value = float(target_value)
    total = (target_value / current_value * 100) -100
    return round(total, 0)


def loading_negative_num(current_value, target_value):
    current_value = float(current_value)
    target_value = float(target_value)
    total = (current_value - target_value) / current_value * 100
    return round(total, 0)


def limit_order_list(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    message_id = update.callback_query.message.message_id
    order_list = get_token_order_list(chat_id)

    keyboard = []
    text= 'Your limit order list'
    if len(order_list) == 0:
        text +=' is empty'
    
    else:
        for token in order_list:
            keyboard.append([InlineKeyboardButton(f"{token}", callback_data=f"LIMIT_ORDER_RECORD_{token}")])

    keyboard.append([InlineKeyboardButton("☰ MENU", callback_data="EXIT")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)


def edit_limit_order_panel(update: Update, context: CallbackContext, token_addr: str):
    try:
        chat_id = update.effective_chat.id
        message_id = update.callback_query.message.message_id
        result = get_token_order(chat_id, token_addr)

        token_symbol, token_name, pair_address, usd_price, token_liquidity, market_cap, price_change, image_url = get_token_information(token_addr)
        sol_price = get_token_information(WSOL)[3]
        status = "Active" # Inactive
        is_hot_token = False

        if is_hot_token == False:
            button = InlineKeyboardButton("Set as HOT TOKEN",callback_data=f"SETHOTTOKEN:{token_addr}")
        else:
            button = InlineKeyboardButton("Remove as HOT TOKEN",callback_data=f"REMOVEHOTTOKEN:{token_addr}")

        message = (
                f"<u><b>EDIT LIMIT ORDERS</b></u>\n\n"
                f"Token: {token_symbol}\n"
                f"CA: <code>{token_addr}</code>\n"
                f"Price: <b>${format_number(float(usd_price))}</b>\n"
                f"Liq: <b>{format_number(float(token_liquidity) / float(sol_price))} SOL / ${format_number(float(token_liquidity))}</b>\n"
                f"Mcap: <b>${format_number(float(market_cap))}</b>\n"
                f"Status: <b>{status}</b>\n\n"
                f"<b>Select which limit order you would like to edit</b>\n"
                f"----------------------------------------------------\n"
                f"<b>Order 1-3 Sell For Profit</b>\n"
            )
        for idx, record in enumerate(result):
            if idx in (0, 1, 2, 4):
                price = record[1]
                amount = record[2]
                load = loading_num(usd_price, price)
                if idx in (0, 1, 2):
                    if record[0] == 0:
                        message += f"{idx + 1}: No-Order\n\n"
                    else:
                        message += f"{idx + 1}: % Higher than Current Price: <b>{load}%</b>\nSell Price in USD: <b>{price:,.6f}</b>\n% of token to Sell: <b>{amount}</b>\n\n"
                else:
                    message += "----------------------------------------------------\n"
                    message += f"<b>Order 5: Buy Higher (e.g. Breakout)</b>\n"
                    if record[0] == 0:
                        message += f"{idx + 1}: No-Order\n\n"
                    else:
                        message += f"{idx + 1}: % Higher than Current Price: <b>{load}%</b>\nBuy Price in USD: <b>{price:,.6f}</b>\nSOL to Spend: <b>{amount}</b>\n\n"


            if idx in (3, 5, 6, 7):
                if idx == 5:
                    message += "----------------------------------------------------\n"
                    message += f"<b>Order 6-8 Buy Lower (e.g. Dip)</b>\n"

                if idx == 3:
                    message += "----------------------------------------------------\n"
                    message += f"<b>Order 4: Sell For Loss (Stop Loss)</b>\n"

                if record[0] == 0:
                    message += f"{idx + 1}: No-Order\n\n"

                else:
                    price = record[1]
                    amount = record[2]
                    load = loading_negative_num(usd_price, price)

                    if idx in (6, 7, 8):
                        message += f"{idx + 1}: % Lower than Current Price: <b>{load}%</b>\nBuy Price in USD: <b>{price:,.6f}</b>\nSOL to Spend: <b>{amount}</b>\n\n"
                    else:
                        message += f"{idx + 1}: % Higher than Current Price: <b>{load}%</b>\nBuy Price in USD: <b>{price:,.6f}</b>\nSOL to Spend: <b>{amount}</b>\n\n"

        keyboard  = [
            [InlineKeyboardButton("ORDER 1",callback_data=f"ORDER_EDIT_{token_addr}_1"),InlineKeyboardButton("ORDER 2",callback_data=f"ORDER_EDIT_{token_addr}_2"),InlineKeyboardButton("ORDER 3",callback_data=f"ORDER_EDIT_{token_addr}_3")],
            [InlineKeyboardButton("ORDER 4",callback_data=f"ORDER_EDIT_{token_addr}_4"),InlineKeyboardButton("ORDER 5",callback_data=f"ORDER_EDIT_{token_addr}_5")],
            [InlineKeyboardButton("ORDER 6",callback_data=f"ORDER_EDIT_{token_addr}_6"),InlineKeyboardButton("ORDER 7",callback_data=f"ORDER_EDIT_{token_addr}_7"),InlineKeyboardButton("ORDER 8",callback_data=f"ORDER_EDIT_{token_addr}_8")],
            [InlineKeyboardButton("⬅️ BACK",callback_data=f"LIMIT_ORDER_RECORD_{token_addr}"),InlineKeyboardButton("☰ MENU",callback_data="EXIT")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    except Exception as e:
        print('edit_limit_order: error', e)


def edit_limit_order(update: Update, context: CallbackContext, token_addr: str, id: int):
    chat_id = update.effective_chat.id
    priv_key = get_priv_key(chat_id)
    pubkey = get_wallet_pubkey(priv_key)

    if id > 5:
        sell_profit(update, context, token_addr, id, pubkey)
    elif id == 5:
        stop_loss(update, context, token_addr, id, pubkey)
    elif id == 4:
        higher_buy(update, context, token_addr, id, pubkey)
    else:
        lower_buy(update, context, token_addr, id, pubkey)


def sell_profit(update: Update, context: CallbackContext, token_addr: str, ORDER_ID: int, pubkey:Pubkey):
    chat_id = update.effective_chat.id
    message_id = update.callback_query.message.message_id
    token_symbol, token_name, pair_address, usd_price, token_liquidity, market_cap, price_change, image_url = get_token_information(token_addr)
    result = get_token_order(chat_id, token_addr)
    solana_client = get_client()
    balance_lamports = solana_client.get_balance(pubkey, "confirmed").value
    sol_price = get_token_information(WSOL)[3]
    token_balance = get_token_balance(str(pubkey), token_addr)
    text = (
        f"<u><b>ORDER NO: {ORDER_ID} -- Buy Lower</b></u>\n\n"
        f"<u><b>{token_symbol}</b></u>\n"
        f"<code>{token_addr}</code>\n\n"
        f"Price: <b><code>${format_number(float(usd_price))}</code></b>\n"
        f"<b>% Lower than Current Price: {loading_negative_num(usd_price, result[ORDER_ID-1][1])}</b>\n"
        f"<b>Buy Price in USD: {result[ORDER_ID-1][1]}</b>\n"
        f"<b>SOL to Spend: {result[ORDER_ID-1][2]}</b>\n\n"
        f"<u>Your Holdings</u>\n"
        f"SOL: <b>{format_number(float(balance_lamports / LAMPORTS_PER_SOL))} SOL / ${format_number(float(balance_lamports / LAMPORTS_PER_SOL* float(sol_price)))}</b>\n"
        f"Token: <b>{format_number(float(token_balance))} / ${format_number(float(token_balance) * float(usd_price))}</b>\n"
    )

    keyboard  = [
        [InlineKeyboardButton("25% Lower", callback_data=f"DCA_PERCENTAGE_{token_addr}_{25}_{ORDER_ID}"),
         InlineKeyboardButton("50% Lower", callback_data=f"DCA_PERCENTAGE_{token_addr}_{50}_{ORDER_ID}"),
         InlineKeyboardButton("75% Lower", callback_data=f"DCA_PERCENTAGE_{token_addr}_{75}_{ORDER_ID}")],
        [InlineKeyboardButton("Enter % Lower", callback_data=f"DCAXP_{token_addr}_{ORDER_ID}")],
        [InlineKeyboardButton("Enter Dollar Price", callback_data=f"DCA_DOLLAR_{token_addr}_{ORDER_ID}")],   
        [InlineKeyboardButton("⬅️ BACK", callback_data=f"EDIT_ORDER_{token_addr}"),
         InlineKeyboardButton("📈 CHART", url=f"https://dexscreener.com/solana/{str(token_addr)}")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)


def stop_loss(update: Update, context: CallbackContext, token_addr: str, ORDER_ID: int, pubkey:Pubkey):
    chat_id = update.effective_chat.id
    message_id = update.callback_query.message.message_id
    token_symbol, token_name, pair_address, usd_price, token_liquidity, market_cap, price_change, image_url = get_token_information(token_addr)
    result = get_token_order(chat_id, token_addr)
    solana_client = get_client()
    balance_lamports = solana_client.get_balance(pubkey, "confirmed").value
    sol_price = get_token_information(WSOL)[3]
    token_balance = get_token_balance(str(pubkey), token_addr)
    text = (
        f"<u><b>ORDER NO: {ORDER_ID} -- Buy Higher</b></u>\n\n"
        f"<u><b>{token_symbol}</b></u>\n"
        f"<code>{token_addr}</code>\n\n"
        f"Price: <b><code>${format_number(float(usd_price))}</code></b>\n"
        f"<b>% Higher than Current Price: {loading_num(usd_price, result[ORDER_ID-1][1])}</b>\n"
        f"<b>Buy Price in USD: {result[ORDER_ID-1][1]}</b>\n"
        f"<b>SOL to Spend: {result[ORDER_ID-1][2]}</b>\n\n"
        f"<u>Your Holdings</u>\n"
        f"SOL: <b>{format_number(float(balance_lamports / LAMPORTS_PER_SOL))} SOL / ${format_number(float(balance_lamports / LAMPORTS_PER_SOL* float(sol_price)))}</b>\n"
        f"Token: <b>{format_number(float(token_balance))} / ${format_number(float(token_balance) * float(usd_price))}</b>\n"
    )

    keyboard  = [
        [InlineKeyboardButton("25% Higher", callback_data=f"BUYHIGHERP_{token_addr}_{25}_{ORDER_ID}"),
         InlineKeyboardButton("50% Higher", callback_data=f"BUYHIGHERP_{token_addr}_{50}_{ORDER_ID}"),
         InlineKeyboardButton("75% Higher", callback_data=f"BUYHIGHERP_{token_addr}_{75}_{ORDER_ID}")],
        [InlineKeyboardButton("Enter % Higher", callback_data=f"BHIGHERX_{token_addr}_{ORDER_ID}")],
        [InlineKeyboardButton("Enter Dollar Price", callback_data=f"HIGHER_DOLLAR_{token_addr}_{ORDER_ID}")],   
        [InlineKeyboardButton("⬅️ BACK", callback_data=f"EDIT_ORDER_{token_addr}"),
         InlineKeyboardButton("📈 CHART", url=f"https://dexscreener.com/solana/{str(token_addr)}")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

 
def higher_buy(update: Update, context: CallbackContext, token_addr: str, ORDER_ID: int, pubkey:Pubkey):
    chat_id = update.effective_chat.id
    message_id = update.callback_query.message.message_id
    token_symbol, token_name, pair_address, usd_price, token_liquidity, market_cap, price_change, image_url = get_token_information(token_addr)
    result = get_token_order(chat_id, token_addr)
    solana_client = get_client()
    balance_lamports = solana_client.get_balance(pubkey, "confirmed").value
    sol_price = get_token_information(WSOL)[3]
    token_balance = get_token_balance(str(pubkey), token_addr)
    text = (
        f"<u><b>ORDER NO: {ORDER_ID} -- Sell For Loss</b></u>\n\n"
        f"<u><b>{token_symbol}</b></u>\n"
        f"<code>{token_addr}</code>\n\n"
        f"Price: <b><code>${format_number(float(usd_price))}</code></b>\n"
        f"<b>% Lower than Current Price: {loading_negative_num(usd_price, result[ORDER_ID-1][1])}</b>\n"
        f"<b>Sell Price in USD: {result[ORDER_ID-1][1]}</b>\n"
        f"<b>% of token to Sell: {result[ORDER_ID-1][2]}</b>\n\n"
        f"<u>Your Holdings</u>\n"
        f"SOL: <b>{format_number(float(balance_lamports / LAMPORTS_PER_SOL))} SOL / ${format_number(float(balance_lamports / LAMPORTS_PER_SOL* float(sol_price)))}</b>\n"
        f"Token: <b>{format_number(float(token_balance))} / ${format_number(float(token_balance) * float(usd_price))}</b>\n"
    )

    keyboard  = [
        [InlineKeyboardButton("5% Lower", callback_data=f"BOOKLOSS_{token_addr}_{5}_{ORDER_ID}"),
         InlineKeyboardButton("10% Lower", callback_data=f"BOOKLOSS_{token_addr}_{10}_{ORDER_ID}"),
         InlineKeyboardButton("20% Lower", callback_data=f"BOOKLOSS_{token_addr}_{20}_{ORDER_ID}")],
        [InlineKeyboardButton("Enter % Lower", callback_data=f"BLOSSX_{token_addr}_{ORDER_ID}")],
        [InlineKeyboardButton("Enter Dollar Price", callback_data=f"BOOK_DOLLAR_{token_addr}_{ORDER_ID}")],   
        [InlineKeyboardButton("⬅️ BACK", callback_data=f"EDIT_ORDER_{token_addr}"),
         InlineKeyboardButton("📈 CHART", url=f"https://dexscreener.com/solana/{str(token_addr)}")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

 
def lower_buy(update: Update, context: CallbackContext, token_addr: str, ORDER_ID: int, pubkey:Pubkey):
    chat_id = update.effective_chat.id
    message_id = update.callback_query.message.message_id
    token_symbol, token_name, pair_address, usd_price, token_liquidity, market_cap, price_change, image_url = get_token_information(token_addr)
    result = get_token_order(chat_id, token_addr)
    solana_client = get_client()
    balance_lamports = solana_client.get_balance(pubkey, "confirmed").value
    sol_price = get_token_information(WSOL)[3]
    token_balance = get_token_balance(str(pubkey), token_addr)
    text = (
        f"<u><b>ORDER NO: {ORDER_ID} -- Sell For Profit</b></u>\n\n"
        f"<u><b>{token_symbol}</b></u>\n"
        f"<code>{token_addr}</code>\n\n"
        f"Price: <b><code>${format_number(float(usd_price))}</code></b>\n"
        f"<b>% Higher than Current Price: {loading_num(usd_price, result[ORDER_ID-1][1])}</b>\n"
        f"<b>Sell Price in USD: {result[ORDER_ID-1][1]}</b>\n"
        f"<b>% of token to Sell: {result[ORDER_ID-1][2]}</b>\n\n"
        f"<u>Your Holdings</u>\n"
        f"SOL: <b>{format_number(float(balance_lamports / LAMPORTS_PER_SOL))} SOL / ${format_number(float(balance_lamports / LAMPORTS_PER_SOL* float(sol_price)))}</b>\n"
        f"Token: <b>{format_number(float(token_balance))} / ${format_number(float(token_balance) * float(usd_price))}</b>\n"
    )

    keyboard  = [
        [InlineKeyboardButton("2x Higher", callback_data=f"BOOKX_{token_addr}_{5}_{ORDER_ID}"),
         InlineKeyboardButton("3x Higher", callback_data=f"BOOKX_{token_addr}_{10}_{ORDER_ID}"),
         InlineKeyboardButton("5x Higher", callback_data=f"BOOKX_{token_addr}_{20}_{ORDER_ID}")],
        [InlineKeyboardButton("Enter % Higher", callback_data=f"BXP_{token_addr}_{ORDER_ID}")],
        [InlineKeyboardButton("Enter Dollar Price", callback_data=f"TBOOK_DOLLAR_{token_addr}_{ORDER_ID}")],   
        [InlineKeyboardButton("⬅️ BACK", callback_data=f"EDIT_ORDER_{token_addr}"),
         InlineKeyboardButton("📈 CHART", url=f"https://dexscreener.com/solana/{str(token_addr)}")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)


def cancel_all_limit_order(update: Update, context: CallbackContext, token_addr: str):
    chat_id = update.effective_chat.id
    message_id = update.callback_query.message.message_id
    delete_all_orders(chat_id, token_addr)
    limit_order_view(update, context, token_addr)


def cancel_order_view_panel(update: Update, context: CallbackContext, token_addr: str):
    try:
        chat_id = update.effective_chat.id
        message_id = update.callback_query.message.message_id
        result = get_token_order(chat_id, token_addr)

        token_symbol, token_name, pair_address, usd_price, token_liquidity, market_cap, price_change, image_url = get_token_information(token_addr)
        sol_price = get_token_information(WSOL)[3]
        status = "Active" # Inactive
        is_hot_token = False

        if is_hot_token == False:
            button = InlineKeyboardButton("Set as HOT TOKEN",callback_data=f"SETHOTTOKEN:{token_addr}")
        else:
            button = InlineKeyboardButton("Remove as HOT TOKEN",callback_data=f"REMOVEHOTTOKEN:{token_addr}")

        message = (
                f"<u><b>CANCEL LIMIT ORDERS</b></u>\n\n"
                f"Token: {token_symbol}\n"
                f"CA: <code>{token_addr}</code>\n"
                f"Price: <b>${format_number(float(usd_price))}</b>\n"
                f"Liq: <b>{format_number(float(token_liquidity) / float(sol_price))} SOL / ${format_number(float(token_liquidity))}</b>\n"
                f"Mcap: <b>${format_number(float(market_cap))}</b>\n"
                f"Status: <b>{status}</b>\n\n"
                f"<b>Select which order to cancel</b>\n\n"
                f"----------------------------------------------------\n"
                f"<b>Order 1-3 Sell For Profit</b>\n"
            )
        for idx, record in enumerate(result):
            if idx in (0, 1, 2, 4):
                price = record[1]
                amount = record[2]
                load = loading_num(usd_price, price)
                if idx in (0, 1, 2):
                    if record[0] == 0:
                        message += f"{idx + 1}: No-Order\n\n"
                    else:
                        message += f"{idx + 1}: % Higher than Current Price: <b>{load}%</b>\nSell Price in USD: <b>{price:,.6f}</b>\n% of token to Sell: <b>{amount}</b>\n\n"
                else:
                    message += "----------------------------------------------------\n"
                    message += f"<b>Order 5: Buy Higher (e.g. Breakout)</b>\n"
                    if record[0] == 0:
                        message += f"{idx + 1}: No-Order\n\n"
                    else:
                        message += f"{idx + 1}: % Higher than Current Price: <b>{load}%</b>\nBuy Price in USD: <b>{price:,.6f}</b>\nSOL to Spend: <b>{amount}</b>\n\n"


            if idx in (3, 5, 6, 7):
                if idx == 5:
                    message += "----------------------------------------------------\n"
                    message += f"<b>Order 6-8 Buy Lower (e.g. Dip)</b>\n"

                if idx == 3:
                    message += "----------------------------------------------------\n"
                    message += f"<b>Order 4: Sell For Loss (Stop Loss)</b>\n"

                if record[0] == 0:
                    message += f"{idx + 1}: No-Order\n\n"

                else:
                    price = record[1]
                    amount = record[2]
                    load = loading_negative_num(usd_price, price)

                    if idx in (6, 7, 8):
                        message += f"{idx + 1}: % Lower than Current Price: <b>{load}%</b>\nBuy Price in USD: <b>{price:,.6f}</b>\nSOL to Spend: <b>{amount}</b>\n\n"
                    else:
                        message += f"{idx + 1}: % Higher than Current Price: <b>{load}%</b>\nBuy Price in USD: <b>{price:,.6f}</b>\nSOL to Spend: <b>{amount}</b>\n\n"

        keyboard  = [
            [InlineKeyboardButton("ORDER 1",callback_data=f"ORDERDEL_{token_addr}_1"),InlineKeyboardButton("ORDER 2",callback_data=f"ORDERDEL_{token_addr}_2"),InlineKeyboardButton("ORDER 3",callback_data=f"ORDERDEL_{token_addr}_3")],
            [InlineKeyboardButton("ORDER 4",callback_data=f"ORDERDEL_{token_addr}_4"),InlineKeyboardButton("ORDER 5",callback_data=f"ORDERDEL_{token_addr}_5"),],
            [InlineKeyboardButton("ORDER 6",callback_data=f"ORDERDEL_{token_addr}_6"),InlineKeyboardButton("ORDER 7",callback_data=f"ORDERDEL_{token_addr}_7"),InlineKeyboardButton("ORDER 8",callback_data=f"ORDERDEL_{token_addr}_8")],
            [InlineKeyboardButton("BACK",callback_data=f"LIMIT_ORDER_RECORD_{token_addr}"),InlineKeyboardButton("☰ MENU", callback_data="EXIT")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    except Exception as e:
        print('cancel order view panel: error', e)


def cancel_order(update: Update, context: CallbackContext, token_addr: str, order_id:int):
    try:
        chat_id = update.effective_chat.id
        message_id = update.callback_query.message.message_id
        delete_order(chat_id, token_addr, int(order_id))
        cancel_order_view_panel(update, context, token_addr)

    except Exception as e:
        print('cancel_order error:', e)