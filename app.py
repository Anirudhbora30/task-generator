import streamlit as st
import openai
import json
import os
import tempfile
import streamlit.components.v1 as components

# Pull key from Secrets
api_key = st.secrets.get("GROQ_API_KEY")

client = openai.OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1"
)

st.set_page_config(page_title="Task AI Pro", page_icon="📝", layout="centered")

# --- Function for Copy Button ---
def copy_button(text, label):
    if not isinstance(text, str):
        text = json.dumps(text, indent=2)
    safe_text = text.replace("`", "\\`").replace("${", "\\${").replace("'", "\\'")
    
    html_code = f"""
    <button onclick="navigator.clipboard.writeText(`{safe_text}`)" 
    style="background-color: #ff4b4b; color: white; border: none; padding: 10px 15px; 
    border-radius: 5px; cursor: pointer; margin-bottom: 20px; font-weight: bold; width: 100%;">
    Copy {label} to Clipboard
    </button>
    """
    components.html(html_code, height=60)

st.title("🎙️ Unified Task Generator")
st.write("Generate a simple heading and brief description from your files.")

uploaded_files = st.file_uploader(
    "Select your Video and Audio files", 
    type=['mp3', 'mp4', 'wav', 'm4a', 'mov', 'mpeg4', 'webm', 'opus', 'ogg'], 
    accept_multiple_files=True
)

if uploaded_files:
    if st.button("Generate Task Details", type="primary"):
        all_transcripts = []
        
        for uploaded_file in uploaded_files:
            with st.spinner(f"Reading {uploaded_file.name}..."):
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = tmp.name
                    with open(tmp_path, "rb") as f:
                        transcript = client.audio.transcriptions.create(model="whisper-large-v3", file=f)
                    all_transcripts.append(transcript.text)
                    os.remove(tmp_path)
                except Exception as e:
                    st.error(f"Error: {e}")

        if all_transcripts:
            with st.spinner("Processing files..."):
                combined_text = "\n".join(all_transcripts)
                
                # Simplified prompt: No steps/expected/actual, just a brief description
                master_prompt = f"""
                Analyze these transcripts and create a combined task report.
                
                Transcripts: {combined_text}
                
                Output ONLY a JSON object:
                "h": "A short, clear heading",
                "d": "A brief, professional description of the task based on the files provided."
                """
                
                res = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": master_prompt}],
                    response_format={"type": "json_object"}
                )
                
                data = json.loads(res.choices[0].message.content)
                heading = data.get('h', '')
                description = data.get('d', '')

                st.success("### ✅ Task Generated")
                
                st.subheader("Task Heading")
                st.info(heading)
                copy_button(heading, "Heading")
                
                st.subheader("Task Description")
                st.text_area("Details", value=description, height=250)
                copy_button(description, "Description")
