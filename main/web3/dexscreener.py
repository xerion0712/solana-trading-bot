import requests


def get_symbol(token):
    # usdc and usdt
    exclude = ['EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
               'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB']

    if token not in exclude:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{token}"

        Token_Symbol = ""
        Sol_symbol = ""
        Token_Name = ""
        try:
            response = requests.get(url)

            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                resp = response.json()
                for pair in resp['pairs']:
                    quoteToken = pair['quoteToken']['symbol']
                    if quoteToken == 'SOL':
                        Token_Name = pair['baseToken']['name']
                        Token_Symbol = pair['baseToken']['symbol']
                        Sol_symbol = quoteToken
                        return Token_Symbol, Sol_symbol, Token_Name

            else:
                print(f"getSymbol: Request failed with status code {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"getSymbol: error occurred: {e}")
        except:
            a = 1

        return Token_Symbol, Sol_symbol, Token_Name
    else:
        if token == 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v':
            return "USDC", "SOL"
        elif token == 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v':
            return "USDT", "SOL"
