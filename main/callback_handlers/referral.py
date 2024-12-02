import io
import qrcode
import math
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from solders.keypair import Keypair # type: ignore

from web3.basic import reward_sol, get_token_information
from postgre_sql import get_priv_key, get_level_one_info, get_level_two_info

from state import WSOL, LAMPORTS_PER_SOL, REWARD_ACCOUNT

def referral_view(update, context, new=True):
    try: 
        chat_id = update.effective_chat.id
        message_id = update.callback_query.message.message_id

        claimable_amount, level_one_count, level_two_count, total_reward, last_claim_time, last_claimed_amount = calc_referral_info(chat_id=chat_id)
        sol_price = get_token_information(WSOL)[3]
        message = (
            f"<u><b>Referral Program</b></u>\n\n"
            f"<b>LEVEL 1: {level_one_count} Users</b>\n"
            f"<b>LEVEL 2: {level_two_count} Users</b>\n\n"
            f"<u><b>Rewards Overview</b></u>\n"
            f"<b>Total Rewards: {total_reward} SOL</b> (Equivalent in USD: ${float(total_reward) * float(sol_price)})\n"
            f"<b>Last Claimed Reward: {last_claimed_amount} SOL</b> (Equivalent in USD: ${float(last_claimed_amount) * float(sol_price)})\n\n"
            f"<b>Important Reminder:</b> <i>You cannot claim rewards less than 0.1 SOL.</i>\n"
            f"Ensure you claim your rewards within 30 days to avoid forfeiture.\n\n"
            f"Invite your friends and family to earn commissions! Receive 0.4% on Level 1 and 0.3% on Level 2 for each of their transactions.\n"
            f"<b>Your referral link:</b>\n"
            f"<code>https://t.me/dog_sol_test_bot?start={chat_id}</code>\n"
        )

        keyboard = [
            [InlineKeyboardButton("CLAIM REWARDS", callback_data=f"CLAIM_REWARDS_{claimable_amount}")],
            [InlineKeyboardButton("GENERATE QR",callback_data="GENERATE_QR")],
            [InlineKeyboardButton("⬅️ BACK",callback_data="EXIT")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if new:
            context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        else:
            context.bot.send_message(chat_id, text=message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    except Exception as e:
        print(e)


def calc_referral_info(chat_id:int):
    try:
        level_one_reward, level_one_count = get_level_one_info(chat_id)
        total_reward, last_claim_time, last_claimed_amount, level_two_reward, level_two_count = get_level_two_info(chat_id)

        claimable_amount = float(level_one_reward) * 0.4 + float(level_two_reward) * 0.3

        print('calc result', claimable_amount, level_one_count, level_two_count, total_reward, last_claim_time, last_claimed_amount)
        return claimable_amount, level_one_count, level_two_count, total_reward, last_claim_time, last_claimed_amount
    except Exception as e:
        print('calc_referral_info', e)


def generate_qr(update, context):
    chat_id = update.effective_chat.id
    message_id = update.callback_query.message.message_id

    data = f"https://t.me/SOL_DOGBOT?start={chat_id}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')
    img = img.convert("RGB")

    bio = io.BytesIO()
    img.save(bio, format='PNG')
    bio.seek(0)

    message = "Your <b>QR code</b> for Referral\nScan the QR code below to refer a friend! Share the benefits and enjoy exclusive rewards for each successful referral.\n\nThank you for being a valued part of our community!"
    keyboard = [
        [InlineKeyboardButton("⬅️ BACK", callback_data="REFERRAL_BACK")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.delete_message(chat_id, message_id)
    context.bot.sendPhoto(chat_id, photo=bio, caption=message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)


def claim_rewards(update, context, reward):
    chat_id = update.effective_chat.id

    if float(reward) < 0.1:
        text = "You cannot withdraw less than 0.1 SOL from the referrals"
        keyboard = [
            [InlineKeyboardButton("⬅️ BACK",callback_data="EXIT")]
        ]
    
    else:
        hex_prive_key = get_priv_key(chat_id)
        pubkey = Keypair.from_base58_string(hex_prive_key).pubkey()
        amount = math.floor(float(reward) * LAMPORTS_PER_SOL)
        confirmation_message = context.bot.send_message(chat_id, 'Claiming now...', reply_markup=reply_markup)
        flag, res = reward_sol(REWARD_ACCOUNT, str(pubkey), amount)

        context.bot.delete_message(chat_id, confirmation_message.message_id)
        if flag:
            text = 'Claim success'
            keyboard = [[
                InlineKeyboardButton("🌐 Tx Hash", url=f"https://solscan.io/tx/{str(res)}"), 
                InlineKeyboardButton("⬅️ BACK", callback_data="SETTINGS")
                ]]
        else: 
            text = 'Claim failed'
            keyboard = [[InlineKeyboardButton("⬅️ BACK", callback_data="REFERRAL")]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id, text, reply_markup=reply_markup)

    