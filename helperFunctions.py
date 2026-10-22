import numpy as np
import pandas as pd

def fct_markdownTableStripAndSplitLine(line):
  """
  Strip a Markdown table row and split it into individual cell values.

  Removes any leading and trailing characters that are not '|', then
  splits the row at each '|' and strips whitespace from each cell.

  Parameters
  ----------
  line : str
      A single row from a Markdown table,
      e.g. '| Col1 | Col2 |\\n'.

  Returns
  -------
  list of str
      List of cell contents with leading/trailing whitespace removed.

  Examples
  --------
  >>> fct_markdownTableStripAndSplitLine("|  Short  | Symbol  |\\n")
  ['Short', 'Symbol']
  """
  # Remove trailing characters until the line ends with '|'
  while line[-1] != "|":
    line = line[:-1]

  # Remove leading characters until the line starts with '|'
  while line[0] != "|":
    line = line[1:]

  # Drop the outer pipes, split at '|', and strip each cell
  return [arg.strip() for arg in line[1:-1].split("|")]



def fct_markdownTable2dataFrame(fname):
  """
  Read a Markdown table from a file and return it as a DataFrame.

  Only lines starting with '|' are processed. The first such line is
  used as the column header, the second line (separator) is skipped,
  and all remaining lines are read as data rows.

  Parameters
  ----------
  fname : str
      Path to the Markdown file containing the table.

  Returns
  -------
  pd.DataFrame
    DataFrame with columns from the Markdown header and the
    corresponding data values.

  Examples
  --------
  >>> df = fct_markdownTable2dataFrame("portfolio.md")
  >>> print(df.head())
  """
  # Read all lines from the file
  with open(fname, "r") as fid:
    lines = fid.readlines()

  # Keep only lines that belong to the table (start with '|')
  lines = [line for line in lines if line[0][0] == "|"]

  # Parse the first line as column headers
  header = fct_markdownTableStripAndSplitLine(lines[0])

  entries = []

  # Start at index 2: index 1 is the separator line (e.g. |---|---|)
  for entry in lines[2:]:
    entry = fct_markdownTableStripAndSplitLine(entry)
    entries.append(entry)

  return pd.DataFrame(entries, columns=header)



def fct_dataFrame2markdownTable(df, alignment=None):
  """
  Convert a pandas DataFrame into a formatted Markdown table string.

  Column widths are determined automatically by the longest entry in
  each column. Per-column alignment can be specified individually.
  Missing values (NaN) are rendered as empty cells.

  Parameters
  ----------
  df : pd.DataFrame
    The DataFrame to convert.
  alignment : list of str or None, optional
    Alignment character per column: 'l' for left-aligned, 'r' for
    right-aligned (default). Missing entries are filled with 'r'.
    Defaults to None (all columns right-aligned).

  Returns
  -------
  str
    The complete Markdown table as a string, consisting of the
    header row, separator row, and data rows.

  Examples
  --------
  >>> md = fct_dataFrame2markdownTable(df, alignment=["l", "r", "r"])
  >>> print(md)
  | Name  |  Price |  N |
  | :---- | -----: | -: |
  | AAPL  | 150.00 |  5 |
  """
  # Avoid mutable default argument
  if alignment is None:
    alignment = []

  clmns = df.columns

  # Minimum column width equals the length of the column name
  clmnLengths = np.zeros(len(clmns), dtype=int)
  for it, clmn in enumerate(clmns):
    clmnLengths[it] = len(str(clmn))

  # Fill missing alignment entries with 'r' (right-aligned)
  while len(alignment) < len(clmns):
    alignment.append("r")

  # Expand column widths to fit the longest cell content
  for it, clmn in enumerate(clmns):
    clmn = df.loc[:, clmn]
    for entry in clmn:
      entryLen = len(str(entry))
      if entryLen > clmnLengths[it]:
        clmnLengths[it] = entryLen

  # --- Build the header row ---
  header = ""
  for it, clmn in enumerate(clmns):
    tmpStr = str(clmn)
    lenStr = len(tmpStr)
    pad = (clmnLengths[it] - lenStr) * " "

    if alignment[it] == "l":
      # Left-aligned: text first, padding on the right
      header += "| " + tmpStr + pad + " "
    else:
      # Right-aligned: padding on the left, text last
      header += "| " + pad + tmpStr + " "
  header += "|\n"

  # --- Build the separator row (encodes alignment for Markdown parsers) ---
  hline = ""
  for it, clmn in enumerate(clmns):
    if alignment[it] == "l":
      # Left-aligned: colon at the start of the dashes
      hline += "| " + ":" + (clmnLengths[it] - 1) * "-" + " "
    else:
      # Right-aligned: colon at the end of the dashes
      hline += "| " + (clmnLengths[it] - 1) * "-" + ":" + " "
  hline += "|\n"

  # --- Build the data rows ---
  content = ""
  for linIdx in range(len(df)):
    for colIdx in range(len(clmns)):
      entry = df.iloc[linIdx, colIdx]
      tmpStr = str(entry)
      lenStr = len(tmpStr)

      # Render NaN as an empty cell
      if tmpStr == "nan":
        tmpStr = ""
        lenStr = 0

      pad = (clmnLengths[colIdx] - lenStr) * " "

      if alignment[colIdx] == "l":
        content += "| " + tmpStr + pad + " "
      else:
        content += "| " + pad + tmpStr + " "

    content += "|\n"

  return header + hline + content

# testbench

# csv = """Datum,Typ,WKN,N,Kurs,WRG,Pos,Kommentar
# 250929,EK,157484,12.000000,27.3300,EUR,-328.96,
# 251023,DD,157484,12.000000,0.3300,USD,+2.90,
# 260205,DD,157484,12.000000,0.3300,USD,+2.51,
# 260423,DD,157484,12.000000,0.3300,USD,+2.52,
# 260522,EK,157484,2.671875,21.6750,EUR,-58.91,
# 260723,DD,157484,14.671875,0.3300,USD,+3.17,"""

# df = pd.read_csv(StringIO(csv))

# # Print as a Markdown table (date, type, WKN, comment left-aligned;
# # numeric columns right-aligned)
# print(fct_dataFrame2markdownTable(
#     df,
#     alignment=["l", "l", "l", "r", "r", "l", "r", "l"]
# ))