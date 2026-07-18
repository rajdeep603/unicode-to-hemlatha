"""Streamlit UI for the Unicode Telugu -> TL-Hemalatha (iLEAP) converter.

Run:  streamlit run app.py
"""
import base64
from pathlib import Path

import streamlit as st

from u2leap import convert, to_bytes

st.set_page_config(page_title="UNI 2 LEAP — Telugu Converter", page_icon="🔤", layout="wide")

FONT_PATH = Path(__file__).parent / "TL-TTHemalatha-Normal.ttf"


@st.cache_data
def font_css() -> str:
    b64 = base64.b64encode(FONT_PATH.read_bytes()).decode()
    return f"""
    <style>
    @font-face {{
        font-family: 'TLHemalatha';
        src: url(data:font/ttf;base64,{b64}) format('truetype');
    }}
    .st-key-leap_output textarea {{
        font-family: 'TLHemalatha', monospace !important;
        font-size: 1.5rem !important;
        line-height: 2.2rem !important;
    }}
    </style>
    """


st.markdown(font_css(), unsafe_allow_html=True)

st.title("Telugu Unicode → TL-Hemalatha (iLEAP)")
st.caption(
    "Portable replica of the legacy VB6 “UNI 2 LEAP” tool. "
    "Paste Unicode Telugu (Gautami) on the left; TL-Hemalatha appears on the right, "
    "rendered in the embedded Hemalatha font."
)

SAMPLE = "నమస్కారం! తెలుగు వార్తలు ఆంధ్రప్రభ ముఖ్యమంత్రి ప్రభుత్వం స్త్రీ క్షమించండి ౧౨౩"

col_in, col_out = st.columns(2)

with col_in:
    st.subheader("Unicode Telugu (Gautami)")
    if st.button("Load sample text"):
        st.session_state["uni_input"] = SAMPLE
    uni_text = st.text_area(
        "Paste Unicode Telugu text here",
        key="uni_input",
        height=380,
        placeholder="ఇక్కడ యూనికోడ్ తెలుగు టెక్స్ట్ పేస్ట్ చేయండి…",
        label_visibility="collapsed",
    )

leap_text = convert(uni_text) if uni_text else ""

with col_out:
    st.subheader("TL-Hemalatha (iLEAP)")
    st.session_state["leap_output"] = leap_text  # keyed widgets ignore `value` on reruns
    st.text_area(
        "Converted output — displayed in the Hemalatha font; copy into any TL-Hemalatha document",
        key="leap_output",
        height=380,
        label_visibility="collapsed",
    )
    if leap_text:
        st.download_button(
            "Download as ANSI .txt (legacy-compatible bytes)",
            data=to_bytes(leap_text),
            file_name="converted_hemalatha.txt",
            mime="text/plain",
        )
        with st.expander("Raw character view (what actually gets copied)"):
            st.code(leap_text, language=None)

if uni_text:
    m1, m2, m3 = st.columns(3)
    m1.metric("Characters to convert", len(uni_text))
    m2.metric("Words converted", len(uni_text.split()))
    m3.metric("Output characters", len(leap_text))

st.divider()
st.caption(
    "The output box renders with the embedded TL-Hemalatha font, so it should read as Telugu. "
    "The underlying characters are the legacy font byte values — paste them into Word/PageMaker "
    "with the TL-Hemalatha font selected, or use the ANSI download for byte-exact files."
)
