"""Watch-only crypto wallet integrations for balances and activity."""

from __future__ import annotations

from typing import Dict, List

import requests


def _safe_get(url: str, params: Dict[str, str] | None = None) -> Dict:
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return {}


def get_btc_wallet(address: str) -> Dict[str, float | int | str]:
    """Fetch BTC watch-only wallet stats via BlockCypher."""
    data = _safe_get(f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance")
    satoshi = float(data.get("final_balance", 0))
    return {
        "chain": "BTC",
        "address": address,
        "balance": round(satoshi / 1e8, 8),
        "tx_count": int(data.get("n_tx", 0)),
        "source": "BlockCypher",
    }


def get_eth_wallet(address: str) -> Dict[str, float | int | str]:
    """Fetch ETH watch-only wallet balance via BlockCypher proxy endpoint."""
    data = _safe_get(f"https://api.blockcypher.com/v1/eth/main/addrs/{address}/balance")
    wei = float(data.get("final_balance", 0))
    return {
        "chain": "ETH",
        "address": address,
        "balance": round(wei / 1e18, 8),
        "tx_count": int(data.get("n_tx", 0)),
        "source": "BlockCypher",
    }


def load_watch_wallets(wallets: List[Dict[str, str]]) -> List[Dict[str, float | int | str]]:
    results = []
    for wallet in wallets:
        chain = wallet.get("chain", "").upper().strip()
        address = wallet.get("address", "").strip()
        if not address:
            continue
        if chain == "BTC":
            results.append(get_btc_wallet(address))
        elif chain == "ETH":
            results.append(get_eth_wallet(address))
    return results
