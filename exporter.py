import re
import numpy as np


def extract_comsol_matrices_from_file(filepath):
    # Load the file
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
        lines = file.read().splitlines()

    # Regex to detect numeric matrix lines
    numeric_line_pattern = re.compile(
        r'^-?\d+(\.\d+)?([eE][-+]?\d+)?(\s+-?\d+(\.\d+)?([eE][-+]?\d+)?)*$'
    )

    section_list = []
    description_lines = []
    matrix_data = []
    collecting_matrix = False

    for line in lines:
        line = line.strip()

        if line.startswith("#"):
            # Add to description
            description_lines.append(line.lstrip("# ").strip())

            # If matrix was being collected, save it and reset
            if collecting_matrix and matrix_data:
                # Detect appropriate dtype
                flat_values = [val for row in matrix_data for val in row]
                dtype = int if all(float(v).is_integer() for v in flat_values) else float
                matrix = np.array(matrix_data, dtype=dtype)

                cleaned_description = "\n".join(
                    line for line in description_lines if line.strip()
                )
                section_list.append({
                    "matrix": matrix,
                    "description": cleaned_description,
                    "ncol": matrix.shape[1]
                })
                matrix_data = []
                collecting_matrix = False
                description_lines = [line.lstrip("# ").strip()]

        elif numeric_line_pattern.match(line):
            # Start or continue matrix collection
            matrix_data.append([float(x) for x in line.split()])
            collecting_matrix = True

        elif collecting_matrix and line == "":
            # End of matrix block
            if matrix_data:
                flat_values = [val for row in matrix_data for val in row]
                dtype = int if all(float(v).is_integer() for v in flat_values) else float
                matrix = np.array(matrix_data, dtype=dtype)

                cleaned_description = "\n".join(
                    line for line in description_lines if line.strip()
                )
                section_list.append({
                    "matrix": matrix,
                    "description": cleaned_description,
                    "ncol": matrix.shape[1]
                })

            collecting_matrix = False
            matrix_data = []
            description_lines = []

        elif not line.startswith("#") and not collecting_matrix:
            # Add to description if not matrix
            description_lines.append(line)

    # Handle matrix at end of file
    if collecting_matrix and matrix_data:
        flat_values = [val for row in matrix_data for val in row]
        dtype = int if all(float(v).is_integer() for v in flat_values) else float
        matrix = np.array(matrix_data, dtype=dtype)

        cleaned_description = "\n".join(
            line for line in description_lines if line.strip()
        )
        section_list.append({
            "matrix": matrix,
            "description": cleaned_description,
            "ncol": matrix.shape[1]
        })

    # Drop metadata-only entries (e.g., short matrices like version info)
    return [s for s in section_list if s["matrix"].shape[0] > 1]


def select_matrix_section(sections, description_contains="", ncol=None, nrow=None):
    """
    Select a matrix section from the extracted COMSOL sections by description substring,
    column count, and row count.

    Parameters:
        sections (list): List of dictionaries with keys 'description', 'matrix', 'ncol'.
        description_contains (str): Substring to search for in the description.
        ncol (int, optional): Expected number of columns in the matrix.
        nrow (int, optional): Expected number of rows in the matrix.

    Returns:
        dict: A dictionary with 'description' and 'matrix' of the matched section, or None if not found.
    """
    for section in sections:
        if description_contains.lower() in section["description"].lower():
            if (ncol is None or section["ncol"] == ncol) and \
               (nrow is None or section["matrix"].shape[0] == nrow):
                return {
                    "description": section["description"],
                    "matrix": section["matrix"]
                }
    return None  # If no match is found
