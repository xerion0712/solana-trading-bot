import os
from dotenv import load_dotenv

load_dotenv()

# Env variables
TOKEN=os.getenv('TELEGRAM_BOT_TOKEN')
MORALIS_API_KEY=os.getenv('MORALIS_API_KEY')
REWARD_ACCOUNT=os.getenv('REWARD_ACCOUNT')
PURCHASED_RPC=os.getenv('PURCHASED_RPC')

# Global Constants
LAMPORTS_PER_SOL = 1e9
WSOL = 'So11111111111111111111111111111111111111112'
USDT = 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB'
USDC = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
ADMIN = "3LXCueEeCqbGyoyYbdZicWeHKFfycdL2FMuFoFVbD8kA"
TRANSFER_MIN_SOL_LIMIT = 5100
DOGBOT = '8ygQonfsFzuqS5omS45pbEnuteJVoFKobPp1hY4BT7VY'
TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
TOKEN_2022_PROGRAM_ID = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
TOKEN_MAPPING = {
    'So11111111111111111111111111111111111111112': {'name': 'Wrapped SOL', 'symbol':'SOL'},
    'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB': {'name': 'USDT', 'symbol':'USDT'},
    'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v': {'name': 'USD Coin', 'symbol':'USDC'},
}
PRIORITY_MAPPING = {
    "LOW": 1,
    1: "LOW",
    "STANDARD": 2,
    2: "STANDARD",
    "HIGH": 3,
    3: "HIGH",
}

# Global dictionary to hold user logs
user_logs = {}
user_data = {} # 
user_states = {} # Variable of storing temporarily state of each user
user_token = {} # Variable of storing token address to buy/sell for each user
watch_list = {} # Variable of storing token address list to watch for each user
portfolio_list = {} # Variable of storing portfolio depending address for each user
temp_priv_key = {}
DK_list = {}

# Global states
IMPORT_NEW_ACCOUNT = "IMPORT_NEW_ACCOUNT"
IMPORT_NEW_ACCOUNT_SOLFARE = "IMPORT_NEW_ACCOUNT_SOLFARE"
SNIPE_TOKEN_ADDRESS = "SNIPE_TOKEN_ADDRESS"
SNIPE_TOKEN_AMOUNT = "SNIPE_TOKEN_AMOUNT"
SWAP_TOKEN_AMOUNT = "SWAP_TOKEN_AMOUNT"
BUY_SELL_TOKEN_ADDRESS = "BUY_SELL_TOKEN_ADDRESS"
CUSTOM_BUY_AMOUNT = "CUSTOM_BUY_AMOUNT"
CUSTOM_SELL_PERCENTAGE = "CUSTOM_SELL_PERCENTAGE"
DELETE_SNIPE_TOKEN = "DELETE_SNIPE_TOKEN"
WITHDRAW_ALL_SOL = "WITHDRAW_ALL_SOL"
WITHDRAW_X_SOL = "WITHDRAW_X_SOL"
INPUT_PASSWORD = "INPUT_PASSWORD"
TX_PASSWORD = "TX_PASSWORD"
BUY_OPTION = "BUY_OPTION"
SELL_OPTION = "SELL_OPTION"
WITHDRAW_ALL_SOL_PASSWORD = "WITHDRAW_ALL_SOL_PASSWORD"
WITHDRAW_X_SOL_PASSWORD = "WITHDRAW_X_SOL_PASSWORD"