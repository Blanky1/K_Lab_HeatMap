import io
import os
import pandas as pd
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt

st.title("Drug Combination Heatmap")

st.markdown("""
**Expected file format** (CSV, TXT, or XLSX):

| Drug B \\ Drug A | 0 | 1.25 | 2.5 | ... |
|---|---|---|---|---|
| (optional numbering row) | 1 | 2 | 3 | ... |
| 0 | val | val | val | ... |
| 1.25 | val | val | val | ... |

- Column 1: Drug B concentration (numeric)
- Column 2: Letter label (A, B, C …) — optional
- Remaining columns: data values; column headers = Drug A concentrations
- An optional row where all values are sequential integers (1, 2, 3 …) is skipped automatically.
""")

uploaded = st.file_uploader("Upload data file", type=["csv", "txt", "xlsx"])


def parse_data(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Takes a raw DataFrame with the structure exported from Excel/CSV:
      col0 = Drug B concentrations (numeric), col1 = letter labels,
      col2+ = data values; column headers col2+ = Drug A concentrations.
    Returns a clean DataFrame indexed by Drug B concs, columns = Drug A concs.
    """
    # Drug A concentrations come from column headers (skip first two label cols)
    druga_concs = pd.to_numeric(raw.columns[2:], errors="coerce")

    # Keep only rows where col0 is a valid number (Drug B concentration rows)
    drugb_numeric = pd.to_numeric(raw.iloc[:, 0], errors="coerce")
    data_rows = raw[drugb_numeric.notna()].copy()
    drugb_values = drugb_numeric[drugb_numeric.notna()].values

    data = data_rows.iloc[:, 2:].astype(float).values

    df_out = pd.DataFrame(data, index=drugb_values, columns=druga_concs.tolist())
    df_out.index.name = "Drug B Conc"
    df_out.columns.name = "Drug A Conc"
    return df_out


def load_file(f, name: str) -> pd.DataFrame:
    if name.endswith(".xlsx"):
        raw = pd.read_excel(f)
    else:
        content = f.read().decode("utf-8")
        raw = pd.read_csv(io.StringIO(content))
    return parse_data(raw)


def make_heatmap(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(df, annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
    ax.set_title("Drug Combination Heatmap")
    ax.set_xlabel("Drug A Concentration")
    ax.set_ylabel("Drug B Concentration")
    return fig


if uploaded is not None:
    try:
        df = load_file(uploaded, uploaded.name)
        st.subheader("Parsed Data")
        st.dataframe(df)
        st.pyplot(make_heatmap(df))
    except Exception as e:
        st.error(f"Could not parse file: {e}")
else:
    sample = os.path.join(os.path.dirname(__file__), "your_file.csv")
    if os.path.exists(sample):
        st.info("No file uploaded — showing sample data from `your_file.csv`.")
        with open(sample, "rb") as f:
            df = load_file(f, "your_file.csv")
        st.subheader("Sample Data")
        st.dataframe(df)
        st.pyplot(make_heatmap(df))
