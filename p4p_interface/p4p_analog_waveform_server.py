#!/usr/bin/env python3
"""Publish one TekHSI analog waveform as two P4P array PVs."""

from threading import Thread

import numpy as np

from p4p.nt import NTScalar
from p4p.server import Server
from p4p.server.thread import SharedPV
from tm_data_types import AnalogWaveform

from tekhsi import TekHSIConnect

SCOPE_ADDRESS = "192.168.2.194:5000"
SOURCE_NAME = "ch1"
PV_PREFIX = "mso44b"

PV_X_NAME = f"{PV_PREFIX}:x"
PV_Y_NAME = f"{PV_PREFIX}:y"

# "ad" means "array of doubles".
pv_x = SharedPV(nt=NTScalar("ad"), initial=np.array([], dtype=np.float64))
pv_y = SharedPV(nt=NTScalar("ad"), initial=np.array([], dtype=np.float64))

pvs = {
    PV_X_NAME: pv_x,
    PV_Y_NAME: pv_y,
}


def updater() -> None:
    """Read a waveform from the scope and publish x/y arrays."""
    with TekHSIConnect(SCOPE_ADDRESS) as connection:
        while True:
            with connection.access_data():
                waveform: AnalogWaveform | None = connection.get_data(SOURCE_NAME)

            if waveform is None:
                msg = f"Scope did not return waveform {SOURCE_NAME!r}"
                raise RuntimeError(msg)

            x_values = np.asarray(waveform.normalized_horizontal_values, dtype=np.float64)
            y_values = np.asarray(waveform.normalized_vertical_values, dtype=np.float64)

            pv_x.post(x_values)
            pv_y.post(y_values)


if __name__ == "__main__":
    print("Starting TekHSI P4P server...")
    print(f"Reading {SOURCE_NAME} from {SCOPE_ADDRESS}")
    print("Publishing PVs:")
    for name in pvs:
        print(f"  {name}")

    worker = Thread(target=updater, daemon=True)
    worker.start()

    Server.forever(providers=[pvs])
