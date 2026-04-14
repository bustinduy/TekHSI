#!/usr/bin/env python3
"""Shared helpers for publishing visible TekHSI waveforms via P4P."""

from __future__ import annotations

from pathlib import Path

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
    from list_available_names import available_names

    return [
        source_name
        for source_name in available_names(scope_address)
        if is_publishable_analog_source(source_name)
    ]


def source_label(source_name: str) -> str:
    """Return a compact display label for one TekHSI source."""
    return source_name.upper()


def pv_name(prefix: str, source_name: str, field: str) -> str:
    """Build the PVA name for one published source field."""
    return f"{prefix}:{source_name}:{field}"


def trace_color(index: int) -> tuple[int, int, int]:
    """Return a stable color for one trace index."""
    return TRACE_COLORS[index % len(TRACE_COLORS)]
