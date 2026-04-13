# EPICS PVA / P4P Interface

This folder contains small `TekHSI` examples that publish scope waveforms through an EPICS PVA
server built with [`p4p`](https://epics-base.github.io/p4p/overview.html#overviewpva).

The folder is organized by example, not by file type. That keeps each Python server next to the
Phoebus display that belongs to it, which is usually the easiest structure to maintain as the
examples evolve.

![](figs/css_boy_Screenshot.png)

## Folder Layout

1. [`single_channel/`](single_channel/)
   One waveform acquisition example with its Python server and matching X-Y plot display
2. [`four_channel/`](four_channel/)
   Four-waveform synchronized acquisition example with its Python server and matching X-Y plot
   display
3. [`figs/`](figs/)
   Screenshots used by this README

## Requirements

1. A supported Tektronix scope with the High Speed Interface enabled
2. A 64-bit Python installation
3. `TekHSI`
4. `p4p`
5. Phoebus, if you want to open the `.bob` displays

`PyVISA` is not required for this workflow.

## Installation

```shell
pip install tekhsi p4p
```

## Single-Channel Example

Files:

1. [`single_channel/analog_waveform_server.py`](single_channel/analog_waveform_server.py)
2. [`single_channel/analog_waveform_xyplot_client.bob`](single_channel/analog_waveform_xyplot_client.bob)

The single-channel server publishes:

1. `mso44b:x`
2. `mso44b:y`

The corresponding Phoebus display reads:

1. `pva://mso44b:x/value`
2. `pva://mso44b:y/value`

Run it from the repository root with:

```shell
python3 p4p_interface/single_channel/analog_waveform_server.py
```

## Four-Channel Example

Files:

1. [`four_channel/analog_waveform_server.py`](four_channel/analog_waveform_server.py)
2. [`four_channel/analog_waveform_xyplot_client.bob`](four_channel/analog_waveform_xyplot_client.bob)

The four-channel server reads `ch1`, `ch2`, `ch3`, and `ch4` inside one `access_data()` block so
all four traces come from the same acquisition.

It publishes:

1. `mso44b:ch1:x` and `mso44b:ch1:y`
2. `mso44b:ch2:x` and `mso44b:ch2:y`
3. `mso44b:ch3:x` and `mso44b:ch3:y`
4. `mso44b:ch4:x` and `mso44b:ch4:y`

The corresponding Phoebus display overlays the four traces on the same X-Y plot.

Run it from the repository root with:

```shell
python3 p4p_interface/four_channel/analog_waveform_server.py
```

## Configuration

Each example keeps its own configuration constants at the top of the server script.

For the single-channel example:

```python
SCOPE_ADDRESS = "192.168.2.194:5000"
SOURCE_NAME = "ch1"
PV_PREFIX = "mso44b"
```

For the four-channel example:

```python
SCOPE_ADDRESS = "192.168.2.194:5000"
SOURCE_NAMES = ("ch1", "ch2", "ch3", "ch4")
PV_PREFIX = "mso44b"
```

If you change `PV_PREFIX`, update the matching `.bob` file in the same example folder.

## Why This Layout

Organizing by `single_channel` and `four_channel` is usually a better habit than splitting into
`python/` and `css_boy/` folders here because:

1. Each example is self-contained and easier to copy, test, and explain
2. The Python server and the `.bob` file change together, so keeping them together reduces drift
3. Adding a new example later, such as `spectral/` or `digital/`, stays straightforward

## Related Documentation

1. [`TekHSI` main README](../README.md)
2. [`p4p` overview](https://epics-base.github.io/p4p/overview.html#overviewpva)
3. [TekHSI documentation](https://tekhsi.readthedocs.io)
