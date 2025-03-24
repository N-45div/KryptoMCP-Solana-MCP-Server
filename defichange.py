from typing import Any
from helius import BalancesAPI
import requests
from pythclient.pythaccounts import PythPriceAccount, PythPriceStatus
from pythclient.solana import (PYTHNET_HTTP_ENDPOINT, PYTHNET_WS_ENDPOINT,
                               SolanaClient, SolanaPublicKey)  
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import requests

import sys
import asyncio
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

mcp = FastMCP("SolMCP")

load_dotenv()


@mcp.tool()
async def wallet_balance(address: str) -> dict[str, Any] | None:
    """
    Get wallet balance of wallet address
    """
    try:
        balances_api = BalancesAPI("HELIUS_API_KEY")
        response = balances_api.get_balances(address)
        return response
    except Exception as e:
        return None

@mcp.tool()
async def get_latesttokens() -> dict[str, Any] | None:
    """
    Get latest tokens from dexscreener
    """
    try:
        response = requests.get(
            "https://api.dexscreener.com/token-profiles/latest/v1",
        )
        return response.json()
    except Exception as e:
        return None

@mcp.tool()
async def get_tokenboosts() -> dict[str, Any] | None:
    """
    Get tokens with active boosts from dexscreener
    """
    try:
        response = requests.get(
            "https://api.dexscreener.com/token-profiles/latest/v1",
        )
        return response.json()
    except Exception as e:
        return None

@mcp.tool()
async def get_price(mint_address: str):
    """
    Fetch price data for a given token mint address using the Pyth Oracle.
    :param mint_address: The mint address of the token or Pyth price feed ID.
    :return: A dictionary containing the price and confidence interval.
    """
    try:
        # Handle 0x format price feed IDs
        if mint_address.startswith("0x"):
            # Convert hex string to bytes and then use as account key
            hex_str = mint_address[2:]  # Remove '0x' prefix
            feed_bytes = bytes.fromhex(hex_str)
            account_key = SolanaPublicKey(feed_bytes)
        else:
            # For traditional Solana addresses
            account_key = SolanaPublicKey(mint_address)
            
        solana_client = SolanaClient(endpoint=PYTHNET_HTTP_ENDPOINT, ws_endpoint=PYTHNET_WS_ENDPOINT)
        price = PythPriceAccount(account_key, solana_client)
        await price.update()
        
        # Check if price object is properly initialized with required attributes
        if hasattr(price, 'aggregate_price_status') and price.aggregate_price_status is not None:
            price_status = price.aggregate_price_status
            if price_status == PythPriceStatus.TRADING:
                result = {
                    "price": price.aggregate_price,
                    "confidence_interval": price.aggregate_price_confidence_interval,
                    "status": "TRADING",
                }
            else:
                result = {
                    "status": "NOT_TRADING",
                    "message": f"Price is not valid now. Status is {price_status}",
                }
        else:
            result = {
                "status": "ERROR",
                "message": "Price data attributes not available for this feed ID"
            }
            
        await solana_client.close()
        return result
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Error fetching price: {str(e)}"
        }

@mcp.tool()
async def get_inflation() -> dict[str, Any] | None:
    """
    Get inflation rate on solana
    """
    try:
        url = "https://go.getblock.io/${API_KEY}"; 
        headers = {"Content-Type": "application/json"}
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getInflationRate"
        }
        response = requests.post(url, json=payload, headers=headers)
        return response.json()
    except Exception as e:
        print(f"Error in dex_latesttoken: {e}")
        return None

@mcp.tool()
async def get_epoch() -> dict[str, Any] | None:
    """
    Get epoch schedule on solana
    """
    try:
        url = "https://go.getblock.io/${API_KEY}"; 
        headers = {"Content-Type": "application/json"}
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getEpochSchedule"
        }
        response = requests.post(url, json=payload, headers=headers)
        res = response.json()
        return res
    except Exception as e:
        print(f"Error in dex_latesttoken: {e}")
        return None

@mcp.tool()
async def get_inflagov() -> dict[str, Any] | None:
    """
    Gets the current inflation governor settings of the Solana blockchain.
    """
    try:
        url = "https://go.getblock.io/${API_KEY}"; 
        headers = {"Content-Type": "application/json"}
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getInflationGovernor"
        }
        response = requests.post(url, json=payload, headers=headers)
        return response.json()
    except Exception as e:
        print(f"Error in dex_latesttoken: {e}")
        return None


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
