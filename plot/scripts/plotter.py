import argparse
import os
import json
import plotly.graph_objects as go
import numpy as np


def remove_key(d, key, empty_subkey=None):
    """
    Remove specified key from dictionary 'd'.
    If 'empty_subkey' is provided, it removes 'empty_subkey'
    from 'd[key]' if present and empty. If 'empty_subkey'
    is not provided, it removes 'key' from 'd' if 'key' is
    in 'd' and 'd[key]' is empty.
    """
    result = d
    if key in result:
        if empty_subkey is not None:
            if empty_subkey in result[key]:
                if not len(result[key][empty_subkey]):
                    result[key].pop(empty_subkey)
        else:
            if not len(result[key]):
                result.pop(key)
    return result


def remove_empty_keys(d):
    """
    Recursively remove empty keys (both keys with empty values
    and empty lists/dictionaries).
    """
    result = d
    for k in list(result.keys()):
        if isinstance(result[k], dict):
            result[k] = remove_empty_keys(result[k])
            if not len(result[k]):
                result.pop(k)
        elif isinstance(result[k], list):
            if not len(result[k]):
                result.pop(k)
    return result


def is_valid_file(parser, arg):
    """
    Check if the provided file path exists.
    """
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return open(arg, "r")  # return an open file handle


def load_json_file(file_handle):
    """
    Load and return JSON data from a file handle.
    """
    return json.load(file_handle)


def process_layout_range(layout, axis):
    """
    Ensure that the layout range is specified correctly.
    """
    if f'{axis}axis' in layout:
        if 'range' in layout[f'{axis}axis']:
            if len(layout[f'{axis}axis']['range']) != 2:
                layout[f'{axis}axis']['range'] = None


def map_trace_type_to_plotly_object(trace_type):
    """
    Map vsl.plot.TraceType enum to Plotly objects.
    """
    type_map = {
        'scatter': go.Scatter,
        'pie': go.Pie,
        'heatmap': go.Heatmap,
        'surface': go.Surface,
        'scatter3d': go.Scatter3d,
        'bar': go.Bar,
        'histogram': go.Histogram
    }
    return type_map[trace_type]


def process_trace(trace):
    """
    Process a trace to ensure only accepted keys are present.
    """
    custom_keys = ["x_str"]
    trace_type = trace.pop("trace_type")

    # Remove all JSON keys not accepted by Plotly.
    accepted = dir(map_trace_type_to_plotly_object(trace_type)) + custom_keys
    keys = list(trace.keys())
    for k in keys:
        if k not in accepted:
            trace.pop(k)

    trace = remove_empty_keys(trace)

    if trace_type == 'pie':
        if "marker" in trace:
            trace["marker"].pop("opacity")
            trace["marker"].pop("colorscale")

    if "x_str" in trace:
        if trace_type == 'bar':
            trace["x"] = trace["x_str"]
        trace.pop("x_str")

    # Flatten 'z' when dealing with 3D scatters.
    if trace_type == 'scatter3d':
        trace["z"] = np.array(trace["z"]).flatten()

    return map_trace_type_to_plotly_object(trace_type)(trace)


def main():
    parser = argparse.ArgumentParser(description="Run training")
    parser.add_argument(
        "--data",
        dest="data",
        required=True,
        help="input file with data",
        metavar="FILE",
        type=lambda x: is_valid_file(parser, x),
    )
    parser.add_argument(
        "--layout",
        dest="layout",
        required=True,
        help="input file with layout",
        metavar="FILE",
        type=lambda x: is_valid_file(parser, x),
    )

    args = parser.parse_args()

    # Read data JSON file.
    data = load_json_file(args.data)

    # Read layout JSON file.
    layout = load_json_file(args.layout)

    # Ensure correct layout range specification.
    for axis in ['x', 'y']:
        process_layout_range(layout, axis)

    # List of traces to be plotted.
    plot_data = [process_trace(trace) for trace in data]

    fig = go.Figure(data=plot_data, layout=go.Layout(layout))
    fig.show()


if __name__ == "__main__":
    main()
