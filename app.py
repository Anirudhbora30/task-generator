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

st.title("🎙️ Multi-Task Generator")
st.write("Upload multiple videos and audio files. AI will process them all at once.")

# The magic change is here: accept_multiple_files=True
uploaded_files = st.file_uploader("Select multiple files", type=['mp3', 'mp4', 'wav', 'm4a', 'mov'], accept_multiple_files=True)

if uploaded_files:
    if st.button(f"Generate Tasks for {len(uploaded_files)} files", type="primary"):
        for i, uploaded_file in enumerate(uploaded_files):
            with st.container():
                st.subheader(f"📄 File {i+1}: {uploaded_file.name}")
                with st.spinner(f"Analyzing {uploaded_file.name}..."):
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                            tmp.write(uploaded_file.getvalue())
                            tmp_path = tmp.name

                        with open(tmp_path, "rb") as f:
                            transcript = client.audio.transcriptions.create(model="whisper-large-v3", file=f)
                        os.remove(tmp_path)

                        prompt = f"Create a task from this: {transcript.text}. Output JSON: {{'h': 'heading', 'd': 'description'}}"
                        res = client.chat.completions.create(
                            model="llama-3.1-8b-instant",
                            messages=[{"role": "user", "content": prompt}],
                            response_format={"type": "json_object"}
                        )
                        data = json.loads(res.choices[0].message.content)

                        # Create two clean columns for easy copying
                        col1, col2 = st.columns(2)
                        with col1:
                            st.text_input(f"Heading {i+1}", value=data.get('h'), key=f"h_{i}")
                        with col2:
                            st.text_area(f"Description {i+1}", value=data.get('d'), height=100, key=f"d_{i}")
                        st.divider()
                    except Exception as e:
                        st.error(f"Error processing {uploaded_file.name}: {e}")
