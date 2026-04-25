import streamlit as st
import openai
import json
import os
import tempfile

# Pull key from Secrets
api_key = st.secrets.get("GROQ_API_KEY")

client = openai.OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1"
)

st.set_page_config(page_title="Task AI Pro", page_icon="📝", layout="wide")

st.title("🎙️ All-in-One Task Generator")
st.write("Upload any combination of Video and Audio files together.")

# Mixed upload with support for Opus/WhatsApp voice notes
uploaded_files = st.file_uploader(
    "Select your Video and Audio files (Mixed)", 
    type=['mp3', 'mp4', 'wav', 'm4a', 'mov', 'mpeg4', 'webm', 'opus', 'ogg'], 
    accept_multiple_files=True
)

if uploaded_files:
    st.info(f"📁 **{len(uploaded_files)} files ready for analysis.**")
    
    if st.button(f"Analyze All Files", type="primary"):
        for i, uploaded_file in enumerate(uploaded_files):
            with st.container():
                icon = "🎥" if uploaded_file.type.startswith('video') else "🎵"
                st.subheader(f"{icon} File {i+1}: {uploaded_file.name}")
                
                with st.spinner(f"AI is processing {uploaded_file.name}..."):
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                            tmp.write(uploaded_file.getvalue())
                            tmp_path = tmp.name

                        with open(tmp_path, "rb") as f:
                            transcript = client.audio.transcriptions.create(model="whisper-large-v3", file=f)
                        os.remove(tmp_path)

                        prompt = f"""
                        Extract the task from this transcript: "{transcript.text}"
                        Output strictly in JSON:
                        {{'h': 'short title', 'd': 'detailed steps'}}
                        """
                        res = client.chat.completions.create(
                            model="llama-3.1-8b-instant",
                            messages=[{"role": "user", "content": prompt}],
                            response_format={"type": "json_object"}
                        )
                        data = json.loads(res.choices[0].message.content)

                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.text_input(f"Task Heading {i+1}", value=data.get('h'), key=f"h_{i}")
                        with col2:
                            st.text_area(f"Task Description {i+1}", value=data.get('d'), height=100, key=f"d_{i}")
                        st.divider()
                        
                    except Exception as e:
                        st.error(f"Could not process {uploaded_file.name}: {e}")
