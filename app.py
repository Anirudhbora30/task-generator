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
    # Ensure text is a string to prevent AttributeError
    if not isinstance(text, str):
        text = json.dumps(text, indent=2)
    
    # Sanitize text for JavaScript
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
st.write("Combine all your videos and audios into one professional bug report.")

uploaded_files = st.file_uploader(
    "Select your Video and Audio files", 
    type=['mp3', 'mp4', 'wav', 'm4a', 'mov', 'mpeg4', 'webm', 'opus', 'ogg'], 
    accept_multiple_files=True
)

if uploaded_files:
    st.info(f"📁 **{len(uploaded_files)} files selected.**")
    
    if st.button("Generate Master Task", type="primary"):
        all_transcripts = []
        
        for uploaded_file in uploaded_files:
            with st.spinner(f"Transcribing {uploaded_file.name}..."):
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = tmp.name

                    with open(tmp_path, "rb") as f:
                        transcript = client.audio.transcriptions.create(model="whisper-large-v3", file=f)
                    
                    all_transcripts.append(f"Source ({uploaded_file.name}): {transcript.text}")
                    os.remove(tmp_path)
                except Exception as e:
                    st.error(f"Error reading {uploaded_file.name}: {e}")

        if all_transcripts:
            with st.spinner("AI is creating the combined report..."):
                combined_text = "\n".join(all_transcripts)
                
                master_prompt = f"""
                You are a Senior QA Automation Engineer. Combine these bug reports into one master Jira-style report.
                Return ONLY a JSON object with two fields:
                "h": A short, professional title.
                "d": A detailed description (string format) with Summary, Steps, and Results.
                
                Transcripts: {combined_text}
                """
                
                res = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": master_prompt}],
                    response_format={"type": "json_object"}
                )
                
                data = json.loads(res.choices[0].message.content)
                heading = data.get('h', '')
                description = data.get('d', '')

                # Convert description to string if the AI accidentally sent a list/dict
                if not isinstance(description, str):
                    description = json.dumps(description, indent=2)

                st.success("### ✅ Master Task Generated")
                
                # Result Display
                st.subheader("Heading")
                st.info(heading)
                copy_button(heading, "Heading")
                
                st.subheader("Description")
                st.text_area("Final Report", value=description, height=300)
                copy_button(description, "Description")
