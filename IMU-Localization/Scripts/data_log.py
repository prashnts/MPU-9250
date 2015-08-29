#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def CSV_Parse_To_Dict(handle, column_delim = ","):
    """
    Initializes the class. The Dictionary structure is built through the first line of the CSV data file. Line delimiter is not customizable and is "\n" by default.
    Args:
        handle (File): File handler. The handle should be opened as "r", or "rw".
        column_delim (str): Column Delimiter Symbol. Default: ",".
    Returns:
        list: A List of Dict each corresponding to the rows.
    Raises:
        ValueError: If non-float data exists in the rows.
    """

    # Reach the beginning of the file
    handle.seek(0)

    # Get the CSV columns - Remove trailing chomp, and split at ","
    column_headers = handle.readline().rstrip().split(",")

    #: List[Dict]: Output data.
    out_list = []

    for row in handle:
        column_data = row.rstrip().split(",")
        if len(column_data) == len(column_headers):
            dat_map = {column_headers[i]: float(column_data[i]) for i in range(0, len(column_headers))}
            out_list.append(dat_map)

    return out_list

