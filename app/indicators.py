"""Technical indicators for market analytics and trading bots."""

from __future__ import annotations

import pandas as pd


def sma(series: pd.Series, period: int = 14) -> pd.Series:
    return series.rolling(window=period, min_periods=period).mean()


def ema(series: pd.Series, period: int = 14) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    return 100 - (100 / (1 + rs))


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    macd_line = ema(series, fast) - ema(series, slow)
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return pd.DataFrame({"macd": macd_line, "signal": signal_line, "hist": hist})


def bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
    middle = sma(series, period)
    std = series.rolling(window=period, min_periods=period).std()
    return pd.DataFrame({"bb_upper": middle + std_dev * std, "bb_middle": middle, "bb_lower": middle - std_dev * std})


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(window=period, min_periods=period).mean()


def stochastic(df: pd.DataFrame, period: int = 14, smooth: int = 3) -> pd.DataFrame:
    low_min = df["low"].rolling(window=period, min_periods=period).min()
    high_max = df["high"].rolling(window=period, min_periods=period).max()
    k = 100 * (df["close"] - low_min) / (high_max - low_min).replace(0, pd.NA)
    d = k.rolling(window=smooth, min_periods=smooth).mean()
    return pd.DataFrame({"stoch_k": k, "stoch_d": d})


def obv(df: pd.DataFrame) -> pd.Series:
    direction = (df["close"].diff().fillna(0) > 0).astype(int).replace({0: -1})
    direction.iloc[0] = 0
    return (direction * df["volume"].fillna(0)).cumsum()


def vwap(df: pd.DataFrame) -> pd.Series:
    tp = (df["high"] + df["low"] + df["close"]) / 3
    cum_vol = df["volume"].cumsum().replace(0, pd.NA)
    return (tp * df["volume"]).cumsum() / cum_vol


def with_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["sma_20"] = sma(out["close"], 20)
    out["ema_20"] = ema(out["close"], 20)
    out["rsi_14"] = rsi(out["close"], 14)
    macd_df = macd(out["close"])
    out = pd.concat([out, macd_df], axis=1)
    out = pd.concat([out, bollinger_bands(out["close"])], axis=1)
    out["atr_14"] = atr(out, 14)
    out = pd.concat([out, stochastic(out)], axis=1)
    out["obv"] = obv(out)
    out["vwap"] = vwap(out)
    return out
