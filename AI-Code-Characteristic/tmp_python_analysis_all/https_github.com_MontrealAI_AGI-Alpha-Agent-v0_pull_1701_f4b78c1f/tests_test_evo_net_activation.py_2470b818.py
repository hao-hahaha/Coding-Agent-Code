# SPDX-License-Identifier: Apache-2.0
"""Unit tests for EvoNet activation logic."""

from __future__ import annotations

import pytest

pytest.importorskip("torch")
import torch

from alpha_factory_v1.demos.aiga_meta_evolution import meta_evolver as me


def test_evonet_no_relu_layers() -> None:
    g = me.Genome(layers=(4,), activation="tanh")
    net = me.EvoNet(2, 1, g)
    assert all(not isinstance(m, torch.nn.ReLU) for m in net.model)


def test_evonet_activation_applied_once() -> None:
    g = me.Genome(layers=(3,), activation="sigmoid")
    net = me.EvoNet(2, 1, g)
    x = torch.randn(1, 2)
    out = net(x)

    h = x
    for layer in net.model:
        h = me._ACT[g.activation](layer(h))

    assert torch.allclose(out, h)


def test_evonet_activation_call_count(monkeypatch: pytest.MonkeyPatch) -> None:
    g = me.Genome(layers=(4, 4), activation="relu")
    net = me.EvoNet(3, 2, g)

    calls = 0

    def _act(x: torch.Tensor) -> torch.Tensor:
        nonlocal calls
        calls += 1
        return x

    monkeypatch.setitem(me._ACT, "relu", _act)
    net(torch.zeros(1, 3))
    assert calls == len(net.model)
