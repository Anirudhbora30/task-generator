import streamlit as st
import openai
import json
import os
import tempfile

# This pulls your key safely from Streamlit Settings
api_key = st.secrets.get("GROQ_API_KEY")

client = openai.OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1"
)

st.set_page_config(page_title="Task AI", page_icon="📝")

st.title("🎙️ Task Generator")
st.write("Upload media to get your Task Heading & Description.")

uploaded_file = st.file_uploader("Upload Audio/Video", type=['mp3', 'mp4', 'wav', 'm4a', 'mov'])

if uploaded_file:
    if st.button("Generate Task", type="primary"):
        with st.spinner("Processing..."):
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

            st.subheader("✅ Result")
            st.text_input("Heading", value=data.get('h'))
            st.text_area("Description", value=data.get('d'), height=150)
