#!/usr/bin/env python3
"""Publish currently visible TekHSI analog traces as P4P array PVs.

This example uses the `available_names()` discovery helper at startup to find
which visible scope traces should be published. For each discovered source it
creates:

- `{prefix}:{source}:x`
- `{prefix}:{source}:y`
- `{prefix}:{source}:show`
- `{prefix}:{source}:active`

The generated Phoebus display writes to the `show` PV. When a source is hidden
from the display, the server publishes empty arrays so the trace disappears from
the plot without needing Phoebus display rules.
"""

from __future__ import annotations

import time

from dataclasses import dataclass
from threading import Lock, Thread
from typing import Any

import numpy as np

from tm_data_types import AnalogWaveform

from tekhsi import AcqWaitOn, TekHSIConnect

from available_waveform_common import (
    DEFAULT_PV_PREFIX,
    DEFAULT_SCOPE_ADDRESS,
    available_analog_source_names,
    pv_name,
)

try:
    from p4p.nt import NTScalar
    from p4p.server import Server
    from p4p.server.thread import SharedPV
except ModuleNotFoundError as error:  # pragma: no cover - import guard for example script
    if error.name == "p4p":
        raise SystemExit(
            "This example requires `p4p` in the active environment. "
            "Activate your virtualenv and install it with `python -m pip install p4p`."
        ) from error
    raise

POLL_DELAY_SECONDS = 0.2
EMPTY_ARRAY = np.array([], dtype=np.float64)


@dataclass
class PublishedSource:
    """Hold the PVs associated with one published waveform source."""

    x: SharedPV
    y: SharedPV
    show: SharedPV
    active: SharedPV


def create_bool_pv(initial_value: bool) -> SharedPV:
    """Create a simple readback boolean PV."""
    return SharedPV(nt=NTScalar("?"), initial=initial_value)


def create_show_pv(
    source_name: str,
    show_state: dict[str, bool],
    state_lock: Lock,
) -> SharedPV:
    """Create a writable checkbox-backed visibility PV."""
    pv = SharedPV(nt=NTScalar("?"), initial=True)

    @pv.put
    def handle_put(shared_pv: SharedPV, op: Any) -> None:
        raw_value = op.value()
        scalar_value = getattr(raw_value, "value", raw_value)
        with state_lock:
            show_state[source_name] = bool(scalar_value)
            updated_value = show_state[source_name]
        shared_pv.post(updated_value)
        op.done()

    return pv


def create_published_source(
    source_name: str,
    show_state: dict[str, bool],
    state_lock: Lock,
) -> PublishedSource:
    """Create all PVs associated with one waveform source."""
    show_state[source_name] = True
    return PublishedSource(
        x=SharedPV(nt=NTScalar("ad"), initial=EMPTY_ARRAY),
        y=SharedPV(nt=NTScalar("ad"), initial=EMPTY_ARRAY),
        show=create_show_pv(source_name, show_state, state_lock),
        active=create_bool_pv(initial_value=True),
    )


def clear_trace(published_source: PublishedSource) -> None:
    """Publish empty arrays so a hidden or inactive trace disappears."""
    published_source.x.post(EMPTY_ARRAY)
    published_source.y.post(EMPTY_ARRAY)


def updater(
    scope_address: str,
    source_names: list[str],
    channel_pvs: dict[str, PublishedSource],
    show_state: dict[str, bool],
    state_lock: Lock,
) -> None:
    """Read currently visible analog waveforms and publish them as P4P PVs."""
    with TekHSIConnect(scope_address, activesymbols=list(source_names)) as connection:
        while True:
            available_lookup = {
                source_name.lower(): source_name
                for source_name in connection.available_symbols
            }
            active_source_names = [
                source_name
                for source_name in source_names
                if source_name.lower() in available_lookup
            ]

            connection.active_symbols(active_source_names)

            for source_name in source_names:
                is_active = source_name in active_source_names
                channel_pvs[source_name].active.post(is_active)
                if not is_active:
                    clear_trace(channel_pvs[source_name])

            if not active_source_names:
                time.sleep(POLL_DELAY_SECONDS)
                continue

            with connection.access_data(AcqWaitOn.NewData):
                waveforms = {
                    source_name: connection.get_data(source_name)
                    for source_name in active_source_names
                }

            with state_lock:
                current_show_state = dict(show_state)

            for source_name in source_names:
                if source_name not in active_source_names or not current_show_state[source_name]:
                    clear_trace(channel_pvs[source_name])
                    continue

                waveform = waveforms.get(source_name)
                if not isinstance(waveform, AnalogWaveform):
                    clear_trace(channel_pvs[source_name])
                    continue

                x_values = np.asarray(
                    waveform.normalized_horizontal_values,
                    dtype=np.float64,
                )
                y_values = np.asarray(
                    waveform.normalized_vertical_values,
                    dtype=np.float64,
                )

                channel_pvs[source_name].x.post(x_values)
                channel_pvs[source_name].y.post(y_values)


if __name__ == "__main__":
    source_names = available_analog_source_names(DEFAULT_SCOPE_ADDRESS)
    if not source_names:
        raise SystemExit(
            f"No visible analog sources found on {DEFAULT_SCOPE_ADDRESS}. "
            "Enable one or more channels or math traces, then try again."
        )

    state_lock = Lock()
    show_state: dict[str, bool] = {}
    channel_pvs = {
        source_name: create_published_source(source_name, show_state, state_lock)
        for source_name in source_names
    }

    pvs = {
        pv_name(DEFAULT_PV_PREFIX, source_name, axis): getattr(published_source, axis)
        for source_name, published_source in channel_pvs.items()
        for axis in ("x", "y", "show", "active")
    }
    pvs[f"{DEFAULT_PV_PREFIX}:sources"] = SharedPV(
        nt=NTScalar("s"),
        initial=", ".join(source_names),
    )

    print("Starting TekHSI available-waveform P4P server...")
    print(f"Reading {', '.join(source_names)} from {DEFAULT_SCOPE_ADDRESS}")
    print("Publishing PVs:")
    for name in sorted(pvs):
        print(f"  {name}")

    worker = Thread(
        target=updater,
        args=(DEFAULT_SCOPE_ADDRESS, source_names, channel_pvs, show_state, state_lock),
        daemon=True,
    )
    worker.start()

    Server.forever(providers=[pvs])
