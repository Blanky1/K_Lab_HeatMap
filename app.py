import io
import pandas as pd
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt

st.title("Drug Combination Heatmap")

st.caption("Expected format (CSV, TXT, or XLSX):")
st.dataframe(
    {
        "DrugB \\ DrugA": [0, 1.25, 2.5],
        "0":    [13.4, 12.9, 6.9],
        "1.25": [15.4, 10.4, 6.2],
        "2.5":  [16.7,  8.2, 7.6],
        "...":  ["...", "...", "..."],
    },
    hide_index=True,
)

tab_upload, tab_paste = st.tabs(["Upload File", "Paste from Excel"])

with tab_upload:
    uploaded = st.file_uploader("Upload file (CSV, TXT, or XLSX):", type=["csv", "txt", "xlsx"])

with tab_paste:
    pasted = st.text_area("Paste copied Excel cells (Ctrl+C → Ctrl+V):", height=200, placeholder="Paste your Excel selection here...")


def parse_data(raw: pd.DataFrame) -> pd.DataFrame:
    druga_concs = pd.to_numeric(raw.columns[2:], errors="coerce")
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


def parse_pasted(text: str) -> pd.DataFrame:
    sep = "\t" if "\t" in text else ","
    raw = pd.read_csv(io.StringIO(text), sep=sep, header=0)
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
