#!/usr/bin/env python3
"""Print the TekHSI source names currently exposed by the scope.

This helper is intentionally small and reusable so future P4P examples can
import `available_names()` and publish selected sources such as channels,
math traces, or measurements.
"""

from __future__ import annotations

import argparse

from collections.abc import Iterable

import grpc

from tekhsi import TekHSIConnect

DEFAULT_SCOPE_ADDRESS = "192.168.2.194:5000"


def available_names(scope_address: str) -> list[str]:
    """Return the source names currently exposed by the TekHSI server."""
    with TekHSIConnect(scope_address) as connection:
        return sorted(connection.available_symbols, key=str.lower)


def group_available_names(names: Iterable[str]) -> dict[str, list[str]]:
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


def print_available_names(scope_address: str) -> int:
    """Query the scope and print the currently available names."""
    try:
        names = available_names(scope_address)
    except grpc.RpcError as error:
        print(f"Failed to query TekHSI server at {scope_address}: {error}")
        return 1
    except Exception as error:  # noqa: BLE001
        print(f"Failed to query TekHSI server at {scope_address}: {error}")
        return 1

    if not names:
        print(f"No active TekHSI sources reported by {scope_address}.")
        return 0

    print(f"Active TekHSI sources on {scope_address}:")
    for name in names:
        print(f"  {name}")

    print("\nGrouped view:")
    for group_name, values in group_available_names(names).items():
        print(f"  {group_name}:")
        for value in values:
            print(f"    {value}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser for the discovery helper."""
    parser = argparse.ArgumentParser(
        description=(
            "Print the TekHSI source names currently exposed by the scope and "
            "group them by common prefixes."
        )
    )
    parser.add_argument(
        "--address",
        default=DEFAULT_SCOPE_ADDRESS,
        help=f"TekHSI server address in host:port form (default: {DEFAULT_SCOPE_ADDRESS})",
    )
    return parser


def main() -> int:
    """Run the command-line entry point."""
    args = build_parser().parse_args()
    return print_available_names(args.address)


if __name__ == "__main__":
    raise SystemExit(main())
