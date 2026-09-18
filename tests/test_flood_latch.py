# PadSpan HA — BLE Room-Presence Tracking for Home Assistant
# Copyright (C) 2026 Garry Broeckling
# Licensed under the GNU General Public License v3.0
"""Unit tests for custom_components.padspan_ha.flood_latch.

2026-09-18/19 incident: the listener was registered as
``hass.bus.async_listen("state_changed", lambda event: _on_state_changed(hass,
event))``. HA's real event bus decides whether to run a listener directly on
the event loop or hand it to a worker thread by checking for the ``@callback``
marker — and a bare lambda wrapping a marked function is a *different*,
unmarked function object, so HA dispatched it to a thread. Every trigger then
crashed inside `hass.async_create_task` (only legal from the event loop) with
"calls hass.async_create_task from a thread other than the event loop" — the
task, and therefore the latch write, silently never happened. Verified live:
`flood_latches` stayed `{}` in the deployed settings store despite the sensor
tripping repeatedly.

Fixed by registering ``functools.partial(_on_state_changed, hass)`` instead —
HA's dispatcher unwraps ``functools.partial`` to find the ``@callback`` marker
on the wrapped function. The stub ``homeassistant.core`` this test suite runs
against (see conftest.py) does not model that thread-vs-loop dispatch at all,
so no test here can reproduce the crash itself — what CAN be pinned down is
the actual code shape that caused it: the registered listener must be the
real function (or a `functools.partial` of it), never a lambda/closure.
test_setup_registers_a_partial_not_a_lambda below is that guard.
"""

from __future__ import annotations

import functools
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from custom_components.padspan_ha.const import DATA_SETTINGS, DOMAIN
from custom_components.padspan_ha.flood_latch import (
    ACTIVE_WINDOW_S,
    _on_state_changed,
    async_reset_latch,
    async_setup_flood_latch,
    async_stop_flood_latch,
    is_active,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _settings(flood_latches=None):
    return SimpleNamespace(
        data={"flood_latches": dict(flood_latches or {})},
        async_set=AsyncMock(),
    )


def _hass(st):
    return SimpleNamespace(
        data={DOMAIN: {DATA_SETTINGS: st}},
        bus=MagicMock(),
        async_create_task=MagicMock(),
    )


def _state_event(entity_id, state, device_class="moisture"):
    new_state = SimpleNamespace(entity_id=entity_id, state=state, attributes={"device_class": device_class})
    return SimpleNamespace(data={"new_state": new_state})


# ---------------------------------------------------------------------------
# Tests: the actual regression — how the listener is registered
# ---------------------------------------------------------------------------


def test_setup_registers_a_partial_not_a_lambda() -> None:
    """The listener passed to hass.bus.async_listen must be a functools.partial
    wrapping _on_state_changed directly — never a lambda/closure, which is
    exactly what broke live (see module docstring)."""
    hass = _hass(_settings())
    async_setup_flood_latch(hass)
    assert hass.bus.async_listen.call_count == 1
    event_name, listener = hass.bus.async_listen.call_args[0]
    assert event_name == "state_changed"
    assert isinstance(listener, functools.partial)
    assert listener.func is _on_state_changed
    assert listener.args == (hass,)


def test_setup_is_idempotent_across_reloads() -> None:
    hass = _hass(_settings())
    async_setup_flood_latch(hass)
    async_setup_flood_latch(hass)
    assert hass.bus.async_listen.call_count == 1


def test_stop_unsubscribes_and_allows_resetup() -> None:
    hass = _hass(_settings())
    async_setup_flood_latch(hass)
    async_stop_flood_latch(hass)
    async_setup_flood_latch(hass)
    assert hass.bus.async_listen.call_count == 2


# ---------------------------------------------------------------------------
# Tests: is_active
# ---------------------------------------------------------------------------


def test_is_active_false_for_non_dict() -> None:
    assert is_active(None) is False
    assert is_active("nope") is False


def test_is_active_false_for_missing_or_bad_expiry() -> None:
    assert is_active({}) is False
    assert is_active({"expires_at": "soon"}) is False
    assert is_active({"expires_at": True}) is False  # bool is an int subclass


def test_is_active_true_before_expiry_false_after() -> None:
    rec = {"triggered_at": 1000.0, "expires_at": 1000.0 + ACTIVE_WINDOW_S}
    assert is_active(rec, now_ts=1000.0 + ACTIVE_WINDOW_S - 1) is True
    assert is_active(rec, now_ts=1000.0 + ACTIVE_WINDOW_S + 1) is False


# ---------------------------------------------------------------------------
# Tests: _on_state_changed
# ---------------------------------------------------------------------------


def test_a_fresh_trigger_latches_and_persists() -> None:
    st = _settings()
    hass = _hass(st)
    _on_state_changed(hass, _state_event("binary_sensor.kitchen_leak", "on"))
    hass.async_create_task.assert_called_once()
    st.async_set.assert_called_once()
    latches = st.async_set.call_args.kwargs["flood_latches"]
    rec = latches["binary_sensor.kitchen_leak"]
    assert rec["expires_at"] - rec["triggered_at"] == ACTIVE_WINDOW_S


def test_ignores_non_on_states() -> None:
    st = _settings()
    hass = _hass(st)
    _on_state_changed(hass, _state_event("binary_sensor.kitchen_leak", "off"))
    st.async_set.assert_not_called()


def test_ignores_non_binary_sensor_domain() -> None:
    st = _settings()
    hass = _hass(st)
    _on_state_changed(hass, _state_event("sensor.kitchen_leak", "on"))
    st.async_set.assert_not_called()


def test_ignores_non_moisture_device_class() -> None:
    st = _settings()
    hass = _hass(st)
    _on_state_changed(hass, _state_event("binary_sensor.motion", "on", device_class="motion"))
    st.async_set.assert_not_called()


def test_retrigger_while_already_latched_keeps_original_time() -> None:
    """ISA-18.2: a still-active alarm keeps its ORIGINAL occurrence time —
    a chattering sensor must not push expiry out further on every flap."""
    now = time.time()
    original = {"triggered_at": now - 10, "expires_at": now - 10 + ACTIVE_WINDOW_S}
    st = _settings({"binary_sensor.kitchen_leak": original})
    hass = _hass(st)
    _on_state_changed(hass, _state_event("binary_sensor.kitchen_leak", "on"))
    st.async_set.assert_not_called()


def test_retrigger_after_expiry_starts_a_fresh_latch() -> None:
    expired = {"triggered_at": 0.0, "expires_at": 1.0}
    st = _settings({"binary_sensor.kitchen_leak": expired})
    hass = _hass(st)
    _on_state_changed(hass, _state_event("binary_sensor.kitchen_leak", "on"))
    st.async_set.assert_called_once()
    latches = st.async_set.call_args.kwargs["flood_latches"]
    assert latches["binary_sensor.kitchen_leak"] != expired


# ---------------------------------------------------------------------------
# Tests: async_reset_latch
# ---------------------------------------------------------------------------


async def test_reset_clears_an_existing_latch() -> None:
    st = _settings({"binary_sensor.kitchen_leak": {"triggered_at": 1.0, "expires_at": 2.0}})
    hass = _hass(st)
    result = await async_reset_latch(hass, "binary_sensor.kitchen_leak")
    assert result is True
    st.async_set.assert_called_once_with(flood_latches={})


async def test_reset_is_a_no_op_when_nothing_latched() -> None:
    st = _settings()
    hass = _hass(st)
    result = await async_reset_latch(hass, "binary_sensor.kitchen_leak")
    assert result is False
    st.async_set.assert_not_called()
