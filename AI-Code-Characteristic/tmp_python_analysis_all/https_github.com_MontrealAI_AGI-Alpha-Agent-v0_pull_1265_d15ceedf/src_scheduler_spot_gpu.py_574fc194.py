# SPDX-License-Identifier: Apache-2.0
"""AWS spot GPU allocation utilities."""

from __future__ import annotations

import logging
from typing import Callable, Mapping, Sequence

try:
    import boto3
except Exception:  # pragma: no cover - optional dep
    boto3 = None  # type: ignore


_log = logging.getLogger(__name__)

FetchFunc = Callable[[str], float]


def _fetch_spot_price(region: str = "us-east-1") -> float:
    """Return the current A10 spot price per hour in ``region``."""
    if boto3 is None:  # pragma: no cover - missing deps
        raise RuntimeError("boto3 not available")
    ec2 = boto3.client("ec2", region_name=region)
    history = ec2.describe_spot_price_history(
        InstanceTypes=["g5.2xlarge"],
        ProductDescriptions=["Linux/UNIX"],
        MaxResults=1,
    )
    price = float(history["SpotPriceHistory"][0]["SpotPrice"])
    return price


class SpotGPUAllocator:
    """Allocate A10 GPUs based on AWS spot prices and a daily budget."""

    def __init__(
        self,
        *,
        region: str = "us-east-1",
        budget_per_day: float = 200.0,
        price_fetcher: FetchFunc | None = None,
    ) -> None:
        self.region = region
        self.budget_per_day = budget_per_day
        self.price_fetcher = price_fetcher or _fetch_spot_price

    def allocate(
        self,
        top_children: Sequence[str],
        other_children: Sequence[str],
        *,
        dry_run: bool = False,
    ) -> Mapping[str, int]:
        """Return GPU allocation for ``top_children`` and ``other_children``."""
        price = self.price_fetcher(self.region)
        hourly_budget = self.budget_per_day / 24
        result: dict[str, int] = {}
        spent = 0.0
        for child in top_children:
            cost = 8 * price
            if spent + cost <= hourly_budget:
                result[child] = 8
                spent += cost
                if dry_run:
                    _log.info(
                        "Allocate 8×A10 to %s: cost %.2f/h (remaining %.2f/h)",
                        child,
                        cost,
                        hourly_budget - spent,
                    )
            else:
                if dry_run:
                    _log.info(
                        "Skip %s: need %.2f/h, remaining %.2f/h",
                        child,
                        cost,
                        hourly_budget - spent,
                    )
        for child in other_children:
            cost = price
            if spent + cost <= hourly_budget:
                result[child] = 1
                spent += cost
                if dry_run:
                    _log.info(
                        "Allocate 1×A10 to %s: cost %.2f/h (remaining %.2f/h)",
                        child,
                        cost,
                        hourly_budget - spent,
                    )
            else:
                if dry_run:
                    _log.info(
                        "Skip %s: need %.2f/h, remaining %.2f/h",
                        child,
                        cost,
                        hourly_budget - spent,
                    )
        if dry_run:
            _log.info("Total hourly cost: %.2f of %.2f", spent, hourly_budget)
        return result


__all__ = ["SpotGPUAllocator", "_fetch_spot_price"]
