#!/usr/bin/env python3
"""Inspect likely math and FFT source names exposed by TekHSI.

This helper is meant to answer questions like:
- Is `math2` advertised by TekHSI?
- Is an FFT exposed as `ch2_iq` instead?
- What waveform type does TekHSI return for the advertised source?
"""

from __future__ import annotations

import argparse

from collections.abc import Iterable

import grpc

from tekhsi import AcqWaitOn, TekHSIConnect
from tekhsi_utils import (
    DEFAULT_SCOPE_ADDRESS,
    active_selected_source_names,
    describe_waveform,
    group_source_names,
    snapshot_waveforms,
)

DEFAULT_CANDIDATES = ("math2", "ch2_iq")


def unique_preserving_order(values: Iterable[str]) -> list[str]:
    """Return values in first-seen order, ignoring case-only duplicates."""
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def print_available_sources(names: list[str]) -> None:
    """Print the available TekHSI names in flat and grouped form."""
    if not names:
        print("No active TekHSI sources were reported.")
        return

    print("Available TekHSI sources:")
    for name in names:
        print(f"  {name}")

    print("\nGrouped view:")
    for group_name, values in group_source_names(names).items():
        print(f"  {group_name}:")
        for value in values:
            print(f"    {value}")


def inspect_sources(scope_address: str, requested_candidates: list[str]) -> int:
    """Inspect which requested names are advertised and what type they return."""
    try:
        with TekHSIConnect(scope_address) as connection:
            available_names = sorted(connection.available_symbols, key=str.lower)
            available_lookup = {name.lower(): name for name in available_names}
            print(f"TekHSI source inspection for {scope_address}\n")
            print_available_sources(available_names)

            auto_candidates = [
                name
                for name in available_names
                if name.lower().startswith("math") or "_iq" in name.lower()
            ]
            candidates = unique_preserving_order([*requested_candidates, *auto_candidates])

            print("\nDiagnostics:")
            if not candidates:
                print("  No candidate sources to inspect.")
                return 0

            available_candidates = active_selected_source_names(connection, candidates)
            waveforms: dict[str, object | None] = {}
            if available_candidates:
                connection.force_sequence()
                waveforms = {
                    source_name.lower(): waveform
                    for source_name, waveform in snapshot_waveforms(
                        connection,
                        available_candidates,
                        wait_on=AcqWaitOn.AnyAcq,
                    ).items()
                }

            for candidate in candidates:
                key = candidate.lower()
                actual_name = available_lookup.get(key)
                if actual_name is None:
                    print(f"  {candidate}: not advertised by TekHSI")
                    continue

                waveform = waveforms.get(key)
                if waveform is None:
                    print(f"  {actual_name}: advertised, but no waveform was returned")
                    continue

                print(f"  {actual_name}: advertised, {describe_waveform(waveform)}")

            if "math2" not in available_lookup:
                if "ch2_iq" in available_lookup:
                    print(
                        "\nHint: the FFT on CH2 appears to be exposed as `ch2_iq`, "
                        "not as `math2`."
                    )
                else:
                    print(
                        "\nHint: if Math2 is an FFT or Spectrum View trace, TekHSI may expose it "
                        "as `ch2_iq` instead of `math2`."
                    )

    except grpc.RpcError as error:
        print(f"Failed to query TekHSI server at {scope_address}: {error}")
        return 1
    except Exception as error:  # noqa: BLE001
        print(f"Failed to inspect TekHSI sources at {scope_address}: {error}")
        return 1

    return 0


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser for the inspection helper."""
    parser = argparse.ArgumentParser(
        description=(
            "Inspect likely math and FFT TekHSI source names such as math2 and ch2_iq."
        )
    )
    parser.add_argument(
        "--address",
        default=DEFAULT_SCOPE_ADDRESS,
        help=f"TekHSI server address in host:port form (default: {DEFAULT_SCOPE_ADDRESS})",
    )
    parser.add_argument(
        "candidates",
        nargs="*",
        default=list(DEFAULT_CANDIDATES),
        help=(
            "Optional candidate source names to inspect. "
            f"Defaults to: {', '.join(DEFAULT_CANDIDATES)}"
        ),
    )
    return parser


def main() -> int:
    """Run the command-line entry point."""
    args = build_parser().parse_args()
    return inspect_sources(args.address, args.candidates)


if __name__ == "__main__":
    raise SystemExit(main())
