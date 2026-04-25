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

st.set_page_config(page_title="Task AI Pro", page_icon="📝", layout="centered")

st.title("🎙️ Unified Task Generator")
st.write("Upload all videos/audios. AI will combine them into **one** master task.")

uploaded_files = st.file_uploader(
    "Select your Video and Audio files", 
    type=['mp3', 'mp4', 'wav', 'm4a', 'mov', 'mpeg4', 'webm', 'opus', 'ogg'], 
    accept_multiple_files=True
)

if uploaded_files:
    st.info(f"📁 **{len(uploaded_files)} files selected.**")
    
    if st.button("Generate One Master Task", type="primary"):
        all_transcripts = []
        
        # Step 1: Process every file to get text
        for uploaded_file in uploaded_files:
            with st.spinner(f"Reading {uploaded_file.name}..."):
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = tmp.name

                    with open(tmp_path, "rb") as f:
                        transcript = client.audio.transcriptions.create(model="whisper-large-v3", file=f)
                    
                    all_transcripts.append(f"File ({uploaded_file.name}): {transcript.text}")
                    os.remove(tmp_path)
                except Exception as e:
                    st.error(f"Error reading {uploaded_file.name}: {e}")

        # Step 2: Combine all text into ONE AI prompt
        if all_transcripts:
            with st.spinner("Combining everything into one task..."):
                combined_text = "\n".join(all_transcripts)
                
                master_prompt = f"""
                You are a professional QA Lead. I am giving you multiple bug report transcripts for the same task.
                Combine all of them into one single, cohesive bug report.
                
                Transcripts:
                {combined_text}
                
                Output ONLY a JSON object:
                {{'h': 'One master heading for all', 'd': 'One master description combining all details'}}
                """
                
                res = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": master_prompt}],
                    response_format={"type": "json_object"}
                )
                data = json.loads(res.choices[0].message.content)

                # Step 3: Show the single result
                st.success("### ✅ Master Task Generated")
                st.text_input("Master Heading", value=data.get('h'))
                st.text_area("Master Description", value=data.get('d'), height=250)
