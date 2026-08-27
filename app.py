import io
import pandas as pd
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt

st.title("Drug Combination Heatmap")
st.caption("Expected format (CSV, TXT, or XLSX):")
st.dataframe(
    {
        "0":    [13.4, 12.9, 6.9],
        "1.25": [15.4, 10.4, 6.2],
        "2.5":  [16.7,  8.2, 7.6],
        "...":  ["...", "...", "..."],
        "DrugB \\ DrugA": [0, 1.25, 2.5],
    },
    hide_index=True,
)

tab_upload, tab_paste = st.tabs(["Upload File", "Paste from Excel"])
with tab_upload:
    uploaded = st.file_uploader("Upload file (CSV, TXT, or XLSX):", type=["csv", "txt", "xlsx"])
with tab_paste:
    pasted = st.text_area("Paste copied Excel cells (Ctrl+C → Ctrl+V):", height=200, placeholder="Paste your Excel selection here...")


def _is_number(s) -> bool:
    try:
        float(s)
        return True
    except (TypeError, ValueError):
        return False


def parse_data(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Expects one column to be a non-numeric-header 'label' column
    (e.g. 'DrugB \\ DrugA') holding the Drug B concentrations, and
    all other columns to have numeric headers = Drug A concentrations.
    Falls back to treating the last column as the label column if every
    header happens to look numeric.
    """
    label_col = None
    for col in raw.columns:
        if not _is_number(str(col).strip()):
            label_col = col
            break
    if label_col is None:
        label_col = raw.columns[-1]

    data_cols = [c for c in raw.columns if c != label_col]
    if not data_cols:
        raise ValueError("No numeric Drug A concentration columns found.")

    druga_concs = pd.to_numeric(pd.Series(data_cols), errors="coerce")
    if druga_concs.isna().any():
        bad = [c for c, ok in zip(data_cols, druga_concs.notna()) if not ok]
        raise ValueError(f"Column header(s) are not numeric Drug A concentrations: {bad}")

    drugb_values = pd.to_numeric(raw[label_col], errors="coerce")
    valid = drugb_values.notna()
    if not valid.any():
        raise ValueError(f"No numeric Drug B concentrations found in column '{label_col}'.")

    data_rows = raw.loc[valid, data_cols].apply(pd.to_numeric, errors="coerce")
    if data_rows.isna().any().any():
        raise ValueError("Some data cells could not be parsed as numbers.")

    df_out = pd.DataFrame(
        data_rows.values,
        index=drugb_values[valid].values,
        columns=druga_concs.tolist(),
    )
    df_out.index.name = "Drug B Conc"
    df_out.columns.name = "Drug A Conc"

    # keep concentrations in ascending order on both axes
    df_out = df_out.sort_index().sort_index(axis=1)
    return df_out


def _sniff_sep(text: str) -> str:
    return "\t" if "\t" in text else ","


def load_file(f, name: str) -> pd.DataFrame:
    if name.endswith(".xlsx"):
        raw = pd.read_excel(f)
    else:
        content = f.read().decode("utf-8")
        raw = pd.read_csv(io.StringIO(content), sep=_sniff_sep(content))
    return parse_data(raw)


def parse_pasted(text: str) -> pd.DataFrame:
    raw = pd.read_csv(io.StringIO(text), sep=_sniff_sep(text), header=0)
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
elif pasted.strip():
    try:
        df = parse_pasted(pasted)
        st.subheader("Parsed Data")
        st.dataframe(df)
        st.pyplot(make_heatmap(df))
    except Exception as e:
        st.error(f"Could not parse data: {e}")
