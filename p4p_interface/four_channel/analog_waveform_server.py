#!/usr/bin/env python3
"""Publish four TekHSI analog waveforms as P4P array PVs."""

from threading import Thread

import numpy as np

from p4p.nt import NTScalar
from p4p.server import Server
from p4p.server.thread import SharedPV
from tm_data_types import AnalogWaveform

from tekhsi import TekHSIConnect

SCOPE_ADDRESS = "192.168.2.194:5000"
SOURCE_NAMES = ("ch1", "ch2", "ch3", "ch4")
PV_PREFIX = "mso44b"


def pv_name(channel: str, axis: str) -> str:
    """Build the PVA name for one channel axis."""
    return f"{PV_PREFIX}:{channel}:{axis}"


channel_pvs: dict[str, dict[str, SharedPV]] = {
    channel: {
        "x": SharedPV(nt=NTScalar("ad"), initial=np.array([], dtype=np.float64)),
        "y": SharedPV(nt=NTScalar("ad"), initial=np.array([], dtype=np.float64)),
    }
    for channel in SOURCE_NAMES
}

pvs = {
    pv_name(channel, axis): axis_pv
    for channel, axis_map in channel_pvs.items()
    for axis, axis_pv in axis_map.items()
}


def updater() -> None:
    """Read four synchronized waveforms from the scope and publish x/y arrays."""
    with TekHSIConnect(SCOPE_ADDRESS, activesymbols=list(SOURCE_NAMES)) as connection:
        while True:
            with connection.access_data():
                waveforms = {
                    source_name: connection.get_data(source_name)
                    for source_name in SOURCE_NAMES
                }

            for source_name, waveform in waveforms.items():
                if waveform is None:
                    msg = f"Scope did not return waveform {source_name!r}"
                    raise RuntimeError(msg)
                if not isinstance(waveform, AnalogWaveform):
                    msg = (
                        f"Waveform {source_name!r} is not analog: "
                        f"{type(waveform).__name__}"
                    )
                    raise TypeError(msg)

                x_values = np.asarray(
                    waveform.normalized_horizontal_values,
                    dtype=np.float64,
                )
                y_values = np.asarray(
                    waveform.normalized_vertical_values,
                    dtype=np.float64,
                )

                channel_pvs[source_name]["x"].post(x_values)
                channel_pvs[source_name]["y"].post(y_values)


if __name__ == "__main__":
    print("Starting TekHSI 4-channel P4P server...")
    print(f"Reading {', '.join(SOURCE_NAMES)} from {SCOPE_ADDRESS}")
    print("Publishing PVs:")
    for name in pvs:
        print(f"  {name}")

    worker = Thread(target=updater, daemon=True)
    worker.start()

    Server.forever(providers=[pvs])
