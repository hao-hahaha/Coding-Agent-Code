# SPDX-License-Identifier: Apache-2.0
import os
import math

MAX_PCT_CAPITAL = float(os.getenv("MAX_PCT_CAPITAL", "0.05"))  # 5 %
ACCOUNT_EQUITY = float(os.getenv("ACCOUNT_EQUITY", "100000"))  # $100k demo


def position_size(price: float) -> int:
    """Return number of shares so risk is <= MAX_PCT_CAPITAL of equity."""
    dollar_limit = MAX_PCT_CAPITAL * ACCOUNT_EQUITY
    lots = math.floor(dollar_limit / price)
    return max(1, min(lots, 100))  # cap to 100 shares for demo

