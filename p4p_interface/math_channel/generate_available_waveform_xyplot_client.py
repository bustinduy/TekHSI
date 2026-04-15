#!/usr/bin/env python3
"""Generate a Phoebus XY-plot client for visible TekHSI waveform sources."""

from __future__ import annotations

import argparse

from pathlib import Path
from xml.etree import ElementTree as ET

from tekhsi_utils import (
    DEFAULT_BOB_OUTPUT,
    DEFAULT_PV_PREFIX,
    DEFAULT_SCOPE_ADDRESS,
    available_xy_source_names,
    is_iq_source,
    pv_name,
    source_label,
    trace_color,
)

DISPLAY_WIDTH = 1280
DISPLAY_HEIGHT = 820
CONTROL_COLUMN_WIDTH = 210
PLOT_X = 245
PLOT_WIDTH = 1010
TOP_PLOT_Y = 126
TOP_PLOT_HEIGHT = 250
BOTTOM_PLOT_Y = 438
BOTTOM_PLOT_HEIGHT = 310


def add_text(parent: ET.Element, tag: str, text: str) -> ET.Element:
    """Create an XML element with text."""
    element = ET.SubElement(parent, tag)
    element.text = text
    return element


def add_color(parent: ET.Element, tag: str, rgb: tuple[int, int, int]) -> None:
    """Create a Phoebus color element."""
    color_element = ET.SubElement(parent, tag)
    ET.SubElement(
        color_element,
        "color",
        red=str(rgb[0]),
        green=str(rgb[1]),
        blue=str(rgb[2]),
    )


def add_font(
    parent: ET.Element,
    tag: str,
    name: str,
    family: str,
    style: str,
    size: float,
) -> None:
    """Create a Phoebus font element."""
    font_element = ET.SubElement(parent, tag)
    ET.SubElement(
        font_element,
        "font",
        name=name,
        family=family,
        style=style,
        size=f"{size:.1f}",
    )


def add_label_widget(
    display: ET.Element,
    *,
    name: str,
    text: str,
    x: int,
    y: int,
    width: int,
    height: int = 26,
    size: float = 14.0,
    bold: bool = False,
) -> None:
    """Add a simple label widget."""
    widget = ET.SubElement(display, "widget", type="label", version="2.0.0")
    add_text(widget, "name", name)
    add_text(widget, "text", text)
    add_text(widget, "x", str(x))
    add_text(widget, "y", str(y))
    add_text(widget, "width", str(width))
    add_text(widget, "height", str(height))
    add_font(
        widget,
        "font",
        "Header 2" if bold else "Default",
        "Liberation Sans",
        "BOLD" if bold else "REGULAR",
        size,
    )


def add_checkbox_widget(
    display: ET.Element,
    *,
    source_name: str,
    prefix: str,
    rgb: tuple[int, int, int],
    y: int,
) -> None:
    """Add one checkbox that controls whether a trace is shown."""
    widget = ET.SubElement(display, "widget", type="checkbox", version="2.0.0")
    add_text(widget, "name", f"show_{source_name}")
    add_text(widget, "x", "20")
    add_text(widget, "y", str(y))
    add_text(widget, "width", "190")
    add_text(widget, "height", "28")
    add_text(widget, "pv_name", f"pva://{pv_name(prefix, source_name, 'show')}/value")
    add_text(widget, "label", source_label(source_name))
    add_text(widget, "auto_size", "false")
    add_text(
        widget,
        "tooltip",
        f"Check to show {source_name}; uncheck to hide it from the XY plot.",
    )
    add_color(widget, "foreground_color", rgb)
    add_font(widget, "font", "Default Bold", "Liberation Sans", "BOLD", 14.0)


def add_xyplot_widget(
    display: ET.Element,
    *,
    widget_name: str,
    source_names: list[str],
    source_colors: dict[str, tuple[int, int, int]],
    prefix: str,
    y: int,
    height: int,
    x_axis_title: str,
    y_axis_title: str,
) -> None:
    """Add one multi-trace XY plot widget."""
    widget = ET.SubElement(display, "widget", type="xyplot", version="3.0.0")
    add_text(widget, "name", widget_name)
    add_text(widget, "x", str(PLOT_X))
    add_text(widget, "y", str(y))
    add_text(widget, "width", str(PLOT_WIDTH))
    add_text(widget, "height", str(height))
    add_color(widget, "foreground_color", (255, 255, 255))
    add_color(widget, "background_color", (0, 0, 0))

    x_axis = ET.SubElement(widget, "x_axis")
    add_text(x_axis, "title", x_axis_title)
    add_text(x_axis, "autoscale", "true")
    add_text(x_axis, "log_scale", "false")
    add_text(x_axis, "minimum", "0.0")
    add_text(x_axis, "maximum", "1.0")
    add_text(x_axis, "show_grid", "true")
    add_font(x_axis, "title_font", "Default Bold", "Liberation Sans", "BOLD", 14.0)
    add_font(x_axis, "scale_font", "Default", "Liberation Sans", "REGULAR", 14.0)
    add_text(x_axis, "visible", "true")

    y_axes = ET.SubElement(widget, "y_axes")
    y_axis = ET.SubElement(y_axes, "y_axis")
    add_text(y_axis, "title", y_axis_title)
    add_text(y_axis, "autoscale", "true")
    add_text(y_axis, "log_scale", "false")
    add_text(y_axis, "minimum", "-1.0")
    add_text(y_axis, "maximum", "1.0")
    add_text(y_axis, "show_grid", "true")
    add_font(y_axis, "title_font", "Default Bold", "Liberation Sans", "BOLD", 14.0)
    add_font(y_axis, "scale_font", "Default", "Liberation Sans", "REGULAR", 14.0)
    add_text(y_axis, "on_right", "false")
    add_text(y_axis, "visible", "true")
    add_color(y_axis, "color", (255, 255, 255))

    traces = ET.SubElement(widget, "traces")
    for source_name in source_names:
        rgb = source_colors[source_name]
        trace = ET.SubElement(traces, "trace")
        add_text(trace, "name", source_label(source_name))
        add_text(trace, "x_pv", f"pva://{pv_name(prefix, source_name, 'x')}/value")
        add_text(trace, "y_pv", f"pva://{pv_name(prefix, source_name, 'y')}/value")
        add_text(trace, "err_pv", "")
        add_text(trace, "axis", "0")
        add_text(trace, "trace_type", "1")
        add_color(trace, "color", rgb)
        add_text(trace, "line_width", "2")
        add_text(trace, "line_style", "0")
        add_text(trace, "point_type", "0")
        add_text(trace, "point_size", "0")
        add_text(trace, "visible", "true")


def build_display(source_names: list[str], prefix: str, scope_address: str) -> ET.Element:
    """Build the Phoebus display XML tree."""
    source_colors = {
        source_name: trace_color(index)
        for index, source_name in enumerate(source_names)
    }
    iq_source_names = [source_name for source_name in source_names if is_iq_source(source_name)]
    waveform_source_names = [
        source_name for source_name in source_names if not is_iq_source(source_name)
    ]

    display = ET.Element("display", version="2.0.0")
    add_text(display, "name", "TekHSI Available Waveforms")
    add_text(display, "width", str(DISPLAY_WIDTH))
    add_text(display, "height", str(DISPLAY_HEIGHT))

    add_label_widget(
        display,
        name="title",
        text="TekHSI Available Waveforms",
        x=20,
        y=18,
        width=420,
        height=32,
        size=18.0,
        bold=True,
    )
    add_label_widget(
        display,
        name="subtitle",
        text=(
            f"Scope {scope_address}. The top plot shows IQ/spectrum traces in frequency vs dB, "
            f"and the bottom plot shows time-domain waveforms. "
            f"pva://{prefix}:<source>:x|y and a checkbox PV at pva://{prefix}:<source>:show/value."
        ),
        x=20,
        y=50,
        width=1220,
        height=48,
        size=13.0,
    )
    add_label_widget(
        display,
        name="controls_title",
        text="Visible Sources",
        x=20,
        y=100,
        width=180,
        height=24,
        size=15.0,
        bold=True,
    )
    add_label_widget(
        display,
        name="controls_help",
        text="Uncheck a box to hide that source from its plot.",
        x=20,
        y=118,
        width=CONTROL_COLUMN_WIDTH,
        height=18,
        size=12.0,
    )
    add_label_widget(
        display,
        name="iq_plot_title",
        text="IQ / Spectrum",
        x=PLOT_X,
        y=96,
        width=260,
        height=24,
        size=15.0,
        bold=True,
    )
    add_label_widget(
        display,
        name="waveform_plot_title",
        text="Waveforms",
        x=PLOT_X,
        y=408,
        width=260,
        height=24,
        size=15.0,
        bold=True,
    )

    for index, source_name in enumerate(source_names):
        add_checkbox_widget(
            display,
            source_name=source_name,
            prefix=prefix,
            rgb=source_colors[source_name],
            y=135 + index * 34,
        )

    add_xyplot_widget(
        display,
        widget_name="iq_plot",
        source_names=iq_source_names,
        source_colors=source_colors,
        prefix=prefix,
        y=TOP_PLOT_Y,
        height=TOP_PLOT_HEIGHT,
        x_axis_title="Frequency (Hz)",
        y_axis_title="Level (dB)",
    )
    add_xyplot_widget(
        display,
        widget_name="waveform_plot",
        source_names=waveform_source_names,
        source_colors=source_colors,
        prefix=prefix,
        y=BOTTOM_PLOT_Y,
        height=BOTTOM_PLOT_HEIGHT,
        x_axis_title="Time (s)",
        y_axis_title="Voltage (V)",
    )
    return display


def indent_xml(element: ET.Element, level: int = 0) -> None:
    """Apply in-place indentation for Python versions without ET.indent()."""
    indent = "\n" + level * "  "
    if len(element):
        if not element.text or not element.text.strip():
            element.text = indent + "  "
        for child in element:
            indent_xml(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = indent
    if level and (not element.tail or not element.tail.strip()):
        element.tail = indent


def generate_display(
    source_names: list[str],
    *,
    prefix: str,
    scope_address: str,
    output_path: Path,
) -> None:
    """Generate a `.bob` file for the provided source names."""
    display = build_display(source_names, prefix, scope_address)
    indent_xml(display)
    output_path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f"<!--Generated for {', '.join(source_names)}-->\n"
        + ET.tostring(display, encoding="unicode"),
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser for the BOB generator."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate a Phoebus XY-plot client for the currently visible TekHSI waveform sources."
        )
    )
    parser.add_argument(
        "--address",
        default=DEFAULT_SCOPE_ADDRESS,
        help=f"TekHSI server address in host:port form (default: {DEFAULT_SCOPE_ADDRESS})",
    )
    parser.add_argument(
        "--prefix",
        default=DEFAULT_PV_PREFIX,
        help=f"PVA prefix to use in generated PV names (default: {DEFAULT_PV_PREFIX})",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_BOB_OUTPUT),
        help=f"Path to the output .bob file (default: {DEFAULT_BOB_OUTPUT})",
    )
    parser.add_argument(
        "sources",
        nargs="*",
        help=(
            "Optional explicit source names. If omitted, the script queries the scope "
            "with available_names()."
        ),
    )
    return parser


def main() -> int:
    """Run the command-line entry point."""
    args = build_parser().parse_args()
    source_names = args.sources or available_xy_source_names(args.address)
    if not source_names:
        print(
            f"No visible XY-plottable sources found on {args.address}. "
            "Enable one or more channels, math traces, or IQ traces, then try again."
        )
        return 1

    output_path = Path(args.output).expanduser().resolve()
    generate_display(
        source_names,
        prefix=args.prefix,
        scope_address=args.address,
        output_path=output_path,
    )
    print(f"Generated Phoebus display at {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
