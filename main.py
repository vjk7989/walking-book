import streamlit as st
import fitz  # PyMuPDF for PDF processing
import requests
from elevenlabs import play
from elevenlabs.client import ElevenLabs


import io

# GEMINI_API_KEY = "AIzaSyALs5U3G39wEo-SyCuLFv-fEEWQmNkf6Pg"
# ELEVEN_LABS_API_KEY = 'sk_3b999e00686ceba0316ba5becd382e9a9987b6d92c1bcfaa'
# ELEVEN_LABS_VOICE_ID = 'onwK4e9ZLuTAKqWW03F9'  # Choose a voice ID from Eleven Labs
# Initialize Eleven Labs client
client = ElevenLabs(api_key="sk_3b999e00686ceba0316ba5becd382e9a9987b6d92c1bcfaa")

# Gemini API key
GEMINI_API_KEY = "AIzaSyALs5U3G39wEo-SyCuLFv-fEEWQmNkf6Pg"

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Function to summarize text using Gemini API
def summarize_text(text):
    url = f'https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={GEMINI_API_KEY}'
    headers = {
        'Content-Type': 'application/json'
    }

    data = {
        'contents': [{
            'parts': [{
                'text': f"Please summarize the following text: {text}"
            }]
        }]
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {str(e)}")
        return f"Error generating summary: {str(e)}"
    
    try:
        result = response.json()
        if 'candidates' in result and len(result['candidates']) > 0:
            summary = result['candidates'][0].get('content', {}).get('parts', [{}])[0].get('text', 'No summary generated.')
            
            # Trim summary to be between 300 and 450 characters
            summary = summary[:450]
            if len(summary) > 300:
                summary = summary[:summary.rfind(' ', 0, 450)]  # Avoid cutting off in the middle of a word
            
            return summary
        else:
            return "No summary generated."
    except Exception as e:
        st.error(f"Error parsing API response: {str(e)}")
        return "Error processing summary."

# Function to convert text to speech using Eleven Labs API
def text_to_speech(text):
    audio = client.generate(
        text=text,
        voice="Brian",  # You can change the voice if you like
        model="eleven_multilingual_v2"  # Multilingual model for diverse languages
    )

    # Collect audio chunks into a single byte stream
    audio_bytes = b"".join(audio)

    # Return audio as a BytesIO object
    audio_binary = io.BytesIO(audio_bytes)
    return audio_binary

# Streamlit UI
st.title('📚 PDF Book Summarizer & TTS')

uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

if uploaded_file is not None:
    with st.spinner('Extracting text from PDF...'):
        extracted_text = extract_text_from_pdf(uploaded_file)
    
    st.subheader('Extracted Text:')
    st.text_area("Extracted Text", extracted_text, height=300, label_visibility="collapsed")
    
    if st.button('Summarize & Convert to Speech'):
        with st.spinner('Summarizing text using Gemini API...'):
            summary = summarize_text(extracted_text)
            st.subheader('Summary:')
            st.write(summary)
            
            with st.spinner('Generating audio with Eleven Labs...'):
                audio_binary = text_to_speech(summary)
                st.audio(audio_binary, format="audio/mp3")  # Stream the audio
                st.download_button("Download Audio", audio_binary, "summary.mp3", "audio/mp3")
else:
    st.info('Please upload a PDF to proceed.')
