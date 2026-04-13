# EPICS PVA / P4P Interface

This folder contains a minimal bridge between `TekHSI` and an EPICS PVA server built with
[`p4p`](https://epics-base.github.io/p4p/overview.html#overviewpva).

The goal is simple:

1. Read one analog waveform from a Tektronix scope with `TekHSI`
2. Publish the waveform as two EPICS PVA array PVs
3. View those PVs from Phoebus

## What Is Published

The server publishes two arrays from one `AnalogWaveform`:

1. `mso44b:x` from `waveform.normalized_horizontal_values`
2. `mso44b:y` from `waveform.normalized_vertical_values`

In the current example, both PVs are declared as `NTScalar("ad")`, which means
"array of doubles". In Phoebus, the value field is typically accessed as:

1. `pva://mso44b:x/value`
2. `pva://mso44b:y/value`

## Files In This Folder

1. [`p4p_analog_waveform_server.py`](p4p_analog_waveform_server.py)
   Minimal P4P server that reads one waveform and publishes the two arrays
2. [`p4p_analog_waveform_4ch_server.py`](p4p_analog_waveform_4ch_server.py)
   Four-channel P4P server that reads `ch1` through `ch4` from the same acquisition
   and publishes one `x`/`y` PV pair per channel
3. [`p4p_analog_waveform_client.bob`](p4p_analog_waveform_client.bob)
   Simple Phoebus client that shows the `x` and `y` arrays separately
4. [`p4p_analog_waveform_xyplot_client.bob`](p4p_analog_waveform_xyplot_client.bob)
   Phoebus X-Y plot client with a black background and yellow trace
5. [`p4p_analog_waveform_4ch_xyplot_client.bob`](p4p_analog_waveform_4ch_xyplot_client.bob)
   Phoebus X-Y plot client with four traces for `ch1` through `ch4`

## Requirements

1. A supported Tektronix scope with the High Speed Interface enabled
2. A 64-bit Python installation
3. `TekHSI`
4. `p4p`
5. Phoebus, if you want to use the `.bob` clients

`PyVISA` is not required for this workflow.

## Installation

Install the Python packages:

```shell
pip install tekhsi p4p
```

## Configure The Server

Edit the constants at the top of
[`p4p_analog_waveform_server.py`](p4p_analog_waveform_server.py):

```python
SCOPE_ADDRESS = "192.168.2.194:5000"
SOURCE_NAME = "ch1"
PV_PREFIX = "mso44b"
```

These control:

1. `SCOPE_ADDRESS`
   Scope IP address and High Speed Interface port
2. `SOURCE_NAME`
   The waveform source to read, for example `ch1`
3. `PV_PREFIX`
   The prefix used to build the published PV names

With the defaults above, the published PVs are:

1. `mso44b:x`
2. `mso44b:y`

If you change `PV_PREFIX`, update the Phoebus `.bob` files as well, or adjust the PV names inside
Phoebus after opening them.

For the 4-channel server in
[`p4p_analog_waveform_4ch_server.py`](p4p_analog_waveform_4ch_server.py), the defaults are:

```python
SCOPE_ADDRESS = "192.168.2.194:5000"
SOURCE_NAMES = ("ch1", "ch2", "ch3", "ch4")
PV_PREFIX = "mso44b"
```

That script publishes:

1. `mso44b:ch1:x` and `mso44b:ch1:y`
2. `mso44b:ch2:x` and `mso44b:ch2:y`
3. `mso44b:ch3:x` and `mso44b:ch3:y`
4. `mso44b:ch4:x` and `mso44b:ch4:y`

## Run The Server

From the repository root:

```shell
python p4p_interface/p4p_analog_waveform_server.py
```

At startup the script prints the scope address, source name, and the PVs that it publishes.

For four synchronized channels:

```shell
python p4p_interface/p4p_analog_waveform_4ch_server.py
```

At startup that script prints the scope address, the four source names, and the eight published
PVs.

## How The Server Works

The implementation is intentionally small:

1. `TekHSIConnect` opens a gRPC connection to the oscilloscope
2. `connection.access_data()` locks access to one consistent acquisition
3. `connection.get_data(SOURCE_NAME)` reads the waveform
4. `waveform.normalized_horizontal_values` and `waveform.normalized_vertical_values` are converted
   to `float64` NumPy arrays
5. `SharedPV.post(...)` publishes the arrays to the PVA server

The 4-channel server follows the same pattern, but it calls `get_data(...)` for `ch1`, `ch2`,
`ch3`, and `ch4` inside one `access_data()` block so all four traces come from the same
acquisition.

## Phoebus Clients

Three example Phoebus clients are included.

### Array Client

Open [`p4p_analog_waveform_client.bob`](p4p_analog_waveform_client.bob) in Phoebus to inspect the
raw arrays directly.

It subscribes to:

1. `pva://mso44b:x/value`
2. `pva://mso44b:y/value`

### X-Y Plot Client

Open [`p4p_analog_waveform_xyplot_client.bob`](p4p_analog_waveform_xyplot_client.bob) in Phoebus
to view the waveform as a scope-like X-Y trace.

This display uses:

1. Black plot background
2. White axes
3. Yellow waveform trace

### 4-Channel X-Y Plot Client

Open
[`p4p_analog_waveform_4ch_xyplot_client.bob`](p4p_analog_waveform_4ch_xyplot_client.bob) in
Phoebus to view `ch1`, `ch2`, `ch3`, and `ch4` on the same X-Y plot.

This display uses:

1. One trace per scope channel
2. PV names of the form `pva://mso44b:ch1:x/value` and `pva://mso44b:ch1:y/value`
3. A plot legend to distinguish the four traces

## Typical Workflow

1. Enable the oscilloscope High Speed Interface
2. Update `SCOPE_ADDRESS`, `SOURCE_NAME` or `SOURCE_NAMES`, and optionally `PV_PREFIX`
3. Run the single-channel or 4-channel server script
4. Open one of the `.bob` files in Phoebus
5. Verify that the plotted waveform matches the selected scope channel or channels

## Troubleshooting

1. If the server cannot connect, make sure the scope High Speed Interface is enabled and that you
   are using the correct port, usually `5000`
2. If no waveform appears, verify that `SOURCE_NAME` or every entry in `SOURCE_NAMES` matches a
   valid source such as `ch1`
3. If Phoebus connects but shows no values, confirm that the PV prefix in the `.bob` file matches
   the prefix configured in the corresponding Python server
4. If you changed the PV names, remember that the Phoebus widgets are currently configured to read
   the `value` field, for example `pva://mso44b:y/value`

## Related Documentation

1. [`TekHSI` main README](../README.md)
2. [`p4p` overview](https://epics-base.github.io/p4p/overview.html#overviewpva)
3. [TekHSI documentation](https://tekhsi.readthedocs.io)
