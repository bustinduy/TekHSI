#!/usr/bin/env python3
"""Shared TekHSI helpers for the P4P math-channel examples."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from tekhsi import AcqWaitOn, TekHSIConnect

DEFAULT_SCOPE_ADDRESS = "192.168.2.194:5000"
DEFAULT_PV_PREFIX = "mso44b"
DEFAULT_BOB_OUTPUT = Path(__file__).with_name("available_waveform_xyplot_client.bob")

TRACE_COLORS: list[tuple[int, int, int]] = [
    (255, 255, 0),
    (0, 255, 255),
    (255, 0, 255),
    (0, 255, 0),
    (255, 128, 0),
    (255, 64, 64),
    (128, 255, 128),
    (160, 160, 255),
]


def available_names(scope_address: str) -> list[str]:
    """Return the source names currently exposed by the TekHSI server."""
    with TekHSIConnect(scope_address) as connection:
        return sorted(connection.available_symbols, key=str.lower)


def group_source_names(names: Iterable[str]) -> dict[str, list[str]]:
    """Group names by common Tek scope source prefixes."""
    grouped_names = {
        "channels": [],
        "math": [],
        "measurements": [],
        "iq": [],
        "other": [],
    }

    for name in sorted(names, key=str.lower):
        lower_name = name.lower()
        if "_iq" in lower_name:
            grouped_names["iq"].append(name)
        elif lower_name.startswith("ch"):
            grouped_names["channels"].append(name)
        elif lower_name.startswith("math"):
            grouped_names["math"].append(name)
        elif lower_name.startswith(("meas", "measurement")):
            grouped_names["measurements"].append(name)
        else:
            grouped_names["other"].append(name)

    return {group: values for group, values in grouped_names.items() if values}


def is_publishable_analog_source(source_name: str) -> bool:
    """Return True for analog scope traces that fit the XY plot example."""
    lower_name = source_name.lower()
    if "_iq" in lower_name:
        return False
    if "_d" in lower_name:
        return False
    return lower_name.startswith("ch") or lower_name.startswith("math")


def available_analog_source_names(scope_address: str) -> list[str]:
    """Return visible scope traces that fit the analog XY plot example."""
    return [
        source_name
        for source_name in available_names(scope_address)
        if is_publishable_analog_source(source_name)
    ]


def active_selected_source_names(
    connection: TekHSIConnect,
    source_names: Iterable[str],
) -> list[str]:
    """Return the selected sources that are currently advertised by TekHSI."""
    available_lookup = {source_name.lower() for source_name in connection.available_symbols}
    return [
        source_name
        for source_name in source_names
        if source_name.lower() in available_lookup
    ]


def snapshot_waveforms(
    connection: TekHSIConnect,
    source_names: list[str],
    *,
    wait_on: AcqWaitOn = AcqWaitOn.NewData,
    after: float = -1,
) -> dict[str, object | None]:
    """Read one coherent acquisition for the requested source names."""
    connection.active_symbols(source_names)
    if not source_names:
        return {}

    with connection.access_data(wait_on, after):
        return {
            source_name: connection.get_data(source_name)
            for source_name in source_names
        }


def describe_waveform(waveform: object) -> str:
    """Build a short human-readable description for one waveform object."""
    parts = [f"type={type(waveform).__name__}"]

    for attr_name in ("y_axis_values", "y_axis_byte_values", "interleaved_iq_axis_values"):
        axis_values = getattr(waveform, attr_name, None)
        if axis_values is not None:
            parts.append(f"samples={len(axis_values)}")
            break

    meta_info = getattr(waveform, "meta_info", None)
    if meta_info is not None:
        fft_length = getattr(meta_info, "iq_fft_length", None)
        center_frequency = getattr(meta_info, "iq_center_frequency", None)
        resolution_bandwidth = getattr(meta_info, "iq_resolution_bandwidth", None)
        window_type = getattr(meta_info, "iq_window_type", None)

        if fft_length is not None:
            parts.append(f"fft_length={int(fft_length)}")
        if center_frequency is not None:
            parts.append(f"center_frequency={center_frequency:g}")
        if resolution_bandwidth is not None:
            parts.append(f"rbw={resolution_bandwidth:g}")
        if window_type:
            parts.append(f"window={window_type}")

    return ", ".join(parts)


def source_label(source_name: str) -> str:
    """Return a compact display label for one TekHSI source."""
    return source_name.upper()


def pv_name(prefix: str, source_name: str, field: str) -> str:
    """Build the PVA name for one published source field."""
    return f"{prefix}:{source_name}:{field}"


def trace_color(index: int) -> tuple[int, int, int]:
    """Return a stable color for one trace index."""
    return TRACE_COLORS[index % len(TRACE_COLORS)]
