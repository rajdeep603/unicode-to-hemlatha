"""Streamlit UI for the Unicode Telugu -> TL-Hemalatha (iLEAP) converter.

Run:  streamlit run app.py
"""
import base64
import json
from io import BytesIO
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from fontTools.ttLib import TTFont

from u2leap import convert, to_bytes

st.set_page_config(page_title="UNI 2 LEAP — Telugu Converter", page_icon="🔤", layout="wide")

FONT_PATH = Path(__file__).parent / "TL-TTHemalatha-Normal.ttf"


@st.cache_data
def display_font_b64() -> str:
    """Font with a U+F0AD (PUA) alias for the byte-173 glyph.

    Browsers never draw U+00AD (soft hyphen), so the వి/వీ/మి/మీ left piece
    vanished in the output box. The viewer displays U+F0AD instead, which the
    aliased cmap renders identically; the copy handler swaps the real byte back.
    """
    font = TTFont(FONT_PATH)
    for table in font["cmap"].tables:
        if table.isUnicode():
            table.cmap[0xF0AD] = table.cmap[0xAD]
    buf = BytesIO()
    font.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


def output_panel(leap: str) -> str:
    payload = json.dumps(leap).replace("<", "\\u003c")
    return f"""
    <style>
    @font-face {{
        font-family: 'TLHemalatha';
        src: url(data:font/ttf;base64,{display_font_b64()}) format('truetype');
    }}
    body {{ margin: 0; font-family: system-ui, sans-serif; }}
    textarea {{
        width: 100%; height: 380px; box-sizing: border-box; resize: vertical;
        border: 1px solid #d9dee4; border-radius: 8px; padding: 10px;
        font-family: 'TLHemalatha', monospace; font-size: 1.5rem; line-height: 1.6;
    }}
    button {{
        margin-top: 8px; border: 1px solid #d9dee4; background: #fff;
        border-radius: 8px; padding: 7px 14px; cursor: pointer; font-size: .88rem;
    }}
    </style>
    <textarea id="out" readonly></textarea>
    <button id="copy">Copy</button>
    <script>
    const trueOut = {payload};  // real text (contains U+00AD)
    const ta = document.getElementById('out');
    ta.value = trueOut.replace(/\\u00AD/g, '\\uF0AD');  // display alias the font can draw
    // Any copy from the box puts the REAL text (U+00AD) on the clipboard.
    ta.addEventListener('copy', (e) => {{
        const sel = ta.selectionStart === ta.selectionEnd
            ? ta.value : ta.value.slice(ta.selectionStart, ta.selectionEnd);
        e.clipboardData.setData('text/plain', sel.replace(/\\uF0AD/g, '\\u00AD'));
        e.preventDefault();
    }});
    const btn = document.getElementById('copy');
    btn.onclick = () => {{
        ta.focus(); ta.select();
        document.execCommand('copy');  // routes through the copy handler above
        ta.setSelectionRange(0, 0); ta.blur();
        btn.textContent = 'Copied!';
        setTimeout(() => btn.textContent = 'Copy', 1200);
    }};
    </script>
    """


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
    components.html(output_panel(leap_text), height=440)
    if leap_text:
        shy = leap_text.count("\xad")  # soft hyphen: the వి/మి left-piece byte
        if shy:
            st.warning(
                f"Output contains {shy} fragile glyph piece(s) (byte 173 — the left part of "
                "వి/వీ/మి/మీ). It displays and copies correctly here, but Word and web editors "
                "delete it on paste, turning వినయ్ into ఇనయ్. "
                "Paste directly into iLEAP/PageMaker only, or use the ANSI download below."
            )
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
    "The underlying characters are the legacy font byte values — use the ANSI download for "
    "byte-exact files, or paste directly into iLEAP/PageMaker. Avoid routing the text through "
    "Word or web editors: they delete the byte-173 piece used by వి/వీ/మి/మీ."
)
