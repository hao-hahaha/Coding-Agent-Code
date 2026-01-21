# SPDX-License-Identifier: Apache-2.0
"""Tests for web_app helpers."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

pd = pytest.importorskip("pandas")

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.interface.web_app import (
    _simulate,
    _timeline_df,
    _disruption_df,
)
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.simulation import forecast


def test_simulate_returns_trajectory() -> None:
    traj = _simulate(2, "logistic", 2, 1)
    assert len(traj) == 2
    assert isinstance(traj[0], forecast.TrajectoryPoint)


def test_dataframe_helpers() -> None:
    traj = _simulate(2, "linear", 2, 1)
    df_time = _timeline_df(traj)
    assert set(df_time.columns) == {"year", "sector", "energy", "disrupted"}
    assert len(df_time) == 4

    df_dis = _disruption_df(traj)
    assert set(df_dis.columns) == {"sector", "year"}
    assert len(df_dis) <= 2
