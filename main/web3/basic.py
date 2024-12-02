import requests
import json
import os
from dotenv import load_dotenv
from solana.rpc.api import Client
from solana.rpc.async_api import AsyncClient
from solders.system_program import TransferParams, transfer
from solana.transaction import Transaction as SolanaTransaction
from solana.rpc.types import TokenAccountOpts
from solana.rpc.commitment import Confirmed
from solders.keypair import Keypair  # type: ignore
from solders.pubkey import Pubkey  # type: ignore

from solders.compute_budget import set_compute_unit_price,set_compute_unit_limit # type: ignore
from web3.dexscreener import get_symbol

from state import WSOL, USDT, USDC, TOKEN_MAPPING, TRANSFER_MIN_SOL_LIMIT, TOKEN_PROGRAM_ID, TOKEN_2022_PROGRAM_ID, PURCHASED_RPC


def get_wallet_pubkey(hex_priv_key: str):
    try:
        keypair = Keypair.from_base58_string(hex_priv_key)
        return keypair.pubkey()
    except:
        return ''


def get_solfare_wallet_pubkey(json_priv_key: str):
    try:
        keypair = Keypair.from_json(json_priv_key)
        return keypair.pubkey(), keypair.__str__()
    except Exception as e:
        print(e)
        return ''


def get_rpc() -> str:
    our_rpc = "http://185.26.8.223:8899"
    alternative_rpc = PURCHASED_RPC
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getHealth"
    }
    try:
        response = requests.post(alternative_rpc, headers=headers, data=json.dumps(payload))
        return alternative_rpc
    except Exception as e2:
        print("RPC is not available: ", e2)
        return ''


def get_client():
    return Client(get_rpc(), "confirmed")


def get_async_client():
    return AsyncClient(get_rpc(), "confirmed")


def get_token_information(token_address: str):
    url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
    try:
        response = requests.get(url).json()
        if response['pairs'] is not None:
            for pair in response["pairs"]:
                base_symbol = pair['baseToken']['symbol']
                quote_symbol = pair['quoteToken']['symbol']
                base_name = pair['baseToken']['name']
                quote_name = pair['quoteToken']['name']
                pair_address = pair['pairAddress']
                price_change = pair['priceChange']
                image_url = pair.get('info', {}).get('imageUrl', '')

                # Check if either token is SOL or USDC
                if "SOL" in [base_symbol, quote_symbol] or "USDC" in [base_symbol, quote_symbol] or "USDT" in [base_symbol, quote_symbol]:

                    # Try to get liquidity in USD, handle if key is missing or invalid
                    token_liquidity = pair.get('liquidity', {}).get('usd', 0)
                    market_cap = pair.get('marketCap', {})

                    if token_address in [WSOL, USDT, USDC]:
                        token_symbol = TOKEN_MAPPING[token_address]['symbol']
                        token_name = TOKEN_MAPPING[token_address]['name']
                    else:
                        token_symbol = base_symbol if base_symbol not in ["SOL", "USDC", "USDT"] else quote_symbol
                        token_name = base_name if base_symbol not in ["SOL", "USDC", "USDT"] else quote_name
                    return token_symbol, token_name, pair_address, pair['priceUsd'], token_liquidity, market_cap, price_change, image_url
        else:
            print("The token address is not in Dexscreener")
            return 0
    except requests.exceptions.RequestException as e:
        print("Error in get token info: ", e)
        return 0


async def get_token_authority(token_address: str):
    solana_client = get_client()
    amm_id = Pubkey.from_string(token_address)
    account_json_info = solana_client.get_account_info_json_parsed(amm_id)
    amm_data = account_json_info.value.data.parsed["info"]
    mut = str(amm_data["isInitialized"])

    status_mint = False
    status_freeze = False

    if amm_data["mintAuthority"] is None:
        status_mint = True
    else:
        status_mint = False

    if amm_data["freezeAuthority"] is None:
        status_freeze = True
    else:
        status_freeze = False

    return mut, status_mint, status_freeze


def get_token_balance(my_wallet, my_token):
    try:
        url = get_rpc()  # Fetch the URL from environment variable
        headers = {
            "accept": "application/json",
            "content-type": "application/json"
        }

        payload = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "getTokenAccountsByOwner",
            "params": [
                my_wallet,
                {"mint": my_token},
                {
                    "encoding": "jsonParsed",
                    "commitment": "confirmed"
                }

            ],
        }

        response = requests.post(url, json=payload, headers=headers)
        balance = response.json()["result"]["value"][0]["account"]["data"]["parsed"]["info"]["tokenAmount"]["uiAmount"]
        return balance 
    except Exception as e:
        print(e)
        return 0


def get_validation_address(address: str) -> str:
    try:
        Pubkey.from_string(address)
        return True
    except ValueError:
        return False


def get_token_metadata(Token):
    url = "https://api.mainnet-beta.solana.com"
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "method": "getAsset",
        "params": [f"{Token}"],
        "id": 0
    }

    headers_4 = {"Content-Type": "application/json"}
    payload_4 = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenSupply",
        "params": [f"{Token}"]
    }

    try:
        # Get asset metadata
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        asset_data = response.json()
        # print(asset_data)
        try:
            name = asset_data['result']['content']['metadata']['name']
            symbol = asset_data['result']['content']['metadata']['symbol']
        except:
            info = get_symbol(str(Token))
            name = str(info[0])
            symbol = str(info[2])
    except requests.exceptions.RequestException as e:
        print("Error fetching asset metadata metaplex:", e)
        return None, None, None, None, None, None

    try:
        # Get token supply
        response_4 = requests.post(url, headers=headers_4, json=payload_4)
        response_4.raise_for_status()
        supply_data = response_4.json()
        total_supply = float(supply_data['result']['value']['uiAmountString'])
        decimals = supply_data['result']['value']['decimals']
    except requests.exceptions.RequestException as e:
        print("Error fetching token supply in metaplex:", e)
        return name, symbol, None, None, None, None

    try:
        # Get token price
        price = get_token_information(str(Token))[3]

    except requests.exceptions.RequestException as e:
        # print("Error fetching token price:", e)
        return name, symbol, None, total_supply, None, decimals

    # Calculate market cap
    market_cap = float(price) * float(total_supply)

    return name, symbol, price, total_supply, market_cap, decimals


def transfer_sol(from_secrect_key:str, to_pubkey:str, percentage: int) :
    try:
        solana_client = get_client()
        sender_keypair = Keypair.from_base58_string(from_secrect_key)
        receiver = Pubkey.from_string(to_pubkey)
        balance = solana_client.get_balance(sender_keypair.pubkey(),"confirmed")

        if balance.value <= TRANSFER_MIN_SOL_LIMIT:
            return False, 'low balance'

        lamports = int((balance.value - 5100) / 100 * percentage)
        transfer_ix = transfer(TransferParams(from_pubkey=sender_keypair.pubkey(), to_pubkey=receiver, lamports=lamports))
        txn = SolanaTransaction().add(transfer_ix)

        txn.add(set_compute_unit_price(10000))
        txn.add(set_compute_unit_limit(10000))
        
        tx = solana_client.send_transaction(txn, sender_keypair)
        confirm_result = solana_client.confirm_transaction(tx.value, Confirmed)

        if confirm_result.value[0].err == None:
            return True, tx.value
        else:
            return False, 'tx failed'

    except Exception as e:
        print('error in transfer_sol', e)
        return False, e


def reward_sol(from_secrect_key:str, to_pubkey:str, amount: int) :
    try:
        solana_client = get_client()
        sender_keypair = Keypair.from_base58_string(from_secrect_key)
        receiver = Pubkey.from_string(to_pubkey)
        balance = solana_client.get_balance(sender_keypair.pubkey(),"confirmed")

        if balance.value <= TRANSFER_MIN_SOL_LIMIT:
            return False, 'low balance in treasury wallet'

        transfer_ix = transfer(TransferParams(from_pubkey=sender_keypair.pubkey(), to_pubkey=receiver, lamports=amount))
        txn = SolanaTransaction().add(transfer_ix)

        txn.add(set_compute_unit_price(10000))
        txn.add(set_compute_unit_limit(10000))
        
        tx = solana_client.send_transaction(txn, sender_keypair)
        confirm_result = solana_client.confirm_transaction(tx.value, Confirmed)

        if confirm_result.value[0].err == None:
            return True, tx.value
        else:
            return False, 'tx failed'

    except Exception as e:
        print('error in transfer_sol', e)
        return False, e


def format_number(n):
 try:    
    if n >= 1_000_000_000:
        return f'{n / 1_000_000_000:.1f}B'
    elif n >= 1_000_000:
        return f'{n / 1_000_000:.1f}M'
    elif n >= 1_000:
        return f'{n / 1_000:.1f}K'
    else:
        return f'{n:,.4f}'
 except Exception as e:
    print("Format number has err",e)


def get_token_portfolio(pubkey):
    solana_client = get_client()
    accounts = solana_client.get_token_accounts_by_owner_json_parsed(pubkey, TokenAccountOpts(program_id=Pubkey.from_string(TOKEN_PROGRAM_ID))).value
    accounts2022 = solana_client.get_token_accounts_by_owner_json_parsed(pubkey, TokenAccountOpts(program_id=Pubkey.from_string(TOKEN_2022_PROGRAM_ID))).value

    list = []
    
    for account in accounts:
        token_address = account.account.data.parsed['info']['mint']
        amount_in = int(account.account.data.parsed['info']['tokenAmount']['amount'])
        decimals = int(account.account.data.parsed['info']['tokenAmount']['decimals'])
        if amount_in > 0:
            deciaml_value = "1e" + str(decimals)
            list.append({"token_address": token_address, "token_balance": float(amount_in) / float(deciaml_value), "decimals": decimals})

    for account in accounts2022:
        token_address = account.account.data.parsed['info']['mint']
        amount_in = int(account.account.data.parsed['info']['tokenAmount']['amount'])
        decimals = int(account.account.data.parsed['info']['tokenAmount']['decimals'])
        if amount_in > 0:
            deciaml_value = "1e" + str(decimals)
            list.append({"token_address": token_address, "token_balance": float(amount_in) / float(deciaml_value), "decimals": decimals})

    filtered_token_list = [
        token for token in list if get_token_information(token["token_address"]) != 0
    ]

    return sorted(filtered_token_list, key=lambda x: x['token_address'])