import requests
from typing import Literal


def get_quote(input_token:str, output_token:str, amount:str, swap_mode:Literal['ExactOut', 'ExactIn'], slippage:int=100):
    link = f"https://quote-api.jup.ag/v6/quote?inputMint={input_token}&outputMint={output_token}&amount={amount}&slippageBps={slippage}&swapMode={swap_mode}&maxAccounts=20"
    response = requests.get(link)
    return response.json()


def get_swap_data(quote, pubkey:str):
    try:
        url = "https://quote-api.jup.ag/v6/swap"
        headers = {
            "Content-Type": "application/json"
        }
        body = {
            "quoteResponse": quote,
            "userPublicKey": pubkey,
            "wrapAndUnwrapSol": True,
            "dynamicComputeUnitLimit": True,
            "prioritizationFeeLamports": 52000
        }

        response = requests.post(url, headers=headers, json=body)
        response_json=response.json()

        swap_transaction = response_json['swapTransaction']
        last_valid_block_height = response_json['lastValidBlockHeight']
        prioritization_fee_lamports = response_json['prioritizationFeeLamports']
        compute_unit_limit = response_json['computeUnitLimit']
        compute_budget_micro_lamports = response_json['prioritizationType']['computeBudget']['microLamports']
        compute_budget_estimated_micro_lamports = response_json['prioritizationType']['computeBudget']['estimatedMicroLamports']
        dynamic_slippage_report = response_json['dynamicSlippageReport']
        simulation_error = response_json['simulationError']
        
        # print("Swap Transaction:", swap_transaction)
        # print("Last Valid Block Height:", last_valid_block_height)
        # print("Prioritization Fee (Lamports):", prioritization_fee_lamports)
        # print("Compute Unit Limit:", compute_unit_limit)
        # print("Compute Budget MicroLamports:", compute_budget_micro_lamports)
        # print("Compute Budget Estimated MicroLamports:", compute_budget_estimated_micro_lamports)
        # print("Dynamic Slippage Report:", dynamic_slippage_report)
        # print("Simulation Error:", simulation_error)

        return swap_transaction

    except Exception as e:
        print(e)