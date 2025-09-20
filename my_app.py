import streamlit as st
from moviepy import VideoFileClip
import whisper
import os
from pathlib import Path
from gtts import gTTS
import io
from googletrans import Translator

# Load Whisper model (base is good balance of speed/accuracy)
model = whisper.load_model("base")

st.title("🎬 Video to Audio + Text Extractor & Language Converter")

uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "mov", "avi", "mkv"])

# Language selection for TTS
st.sidebar.header("🌍 Language Converter")
languages = {
    "English": "en",
    "Spanish": "es", 
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Portuguese": "pt",
    "Russian": "ru",
    "Japanese": "ja",
    "Korean": "ko",
    "Chinese (Simplified)": "zh",
    "Arabic": "ar",
    "Hindi": "hi",
    "Tamil": "ta"
}

selected_language = st.sidebar.selectbox("Select target language for audio conversion:", list(languages.keys()))

if uploaded_file is not None:
    # Save uploaded video temporarily
    video_path = Path("temp_video.mp4")
    with open(video_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.video(str(video_path))

    if st.button("Extract Audio & Transcribe"):
        with st.spinner("Processing..."):
            # Extract audio
            video = VideoFileClip(str(video_path))
            audio_path = "output_audio.mp3"
            video.audio.write_audiofile(audio_path)

            # Transcribe audio with Whisper
            result = model.transcribe(audio_path)
            text_output = result["text"]

            # Save text to file
            text_path = "transcription.txt"
            with open(text_path, "w", encoding="utf-8") as f:
                f.write(text_output)

            # Store in session state for later use
            st.session_state.text_output = text_output
            st.session_state.audio_path = audio_path
            st.session_state.text_path = text_path
            st.session_state.transcription_done = True

    # Show results after transcription
    if st.session_state.get('transcription_done', False):
        text_output = st.session_state.text_output
        audio_path = st.session_state.audio_path
        text_path = st.session_state.text_path

        # Language conversion section
        st.subheader("🌍 Language Conversion")
        st.info(f"Selected language: {selected_language} (code: {languages[selected_language]})")
        
        if st.button("Convert to Speech in Selected Language"):
            with st.spinner(f"Translating and converting to {selected_language} speech..."):
                try:
                    # Debug info
                    st.write(f"Original text: '{text_output[:100]}...'")
                    st.write(f"Target language: {selected_language} (code: {languages[selected_language]})")
                    
                    # Step 1: Translate the text to the target language
                    translator = Translator()
                    lang_code = languages[selected_language]
                    
                    # Translate the text
                    translated_result = translator.translate(text_output, dest=lang_code)
                    translated_text = translated_result.text
                    
                    st.write(f"Translated text: '{translated_text[:100]}...'")
                    
                    # Step 2: Convert translated text to speech
                    tts = gTTS(text=translated_text, lang=lang_code, slow=False)
                    
                    # Save to bytes
                    tts_buffer = io.BytesIO()
                    tts.write_to_fp(tts_buffer)
                    tts_buffer.seek(0)
                    
                    # Save to file
                    converted_audio_path = f"converted_audio_{lang_code}.mp3"
                    with open(converted_audio_path, "wb") as f:
                        f.write(tts_buffer.getvalue())
                    
                    st.success(f"✅ Text translated and converted to {selected_language} speech!")
                    
                    # Show both original and translated text
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("📝 Original Text")
                        st.text_area("Original", text_output, height=100)
                    
                    with col2:
                        st.subheader(f"🌍 Translated to {selected_language}")
                        st.text_area("Translated", translated_text, height=100)
                    
                    # Play the audio
                    st.subheader("🎵 Converted Audio")
                    st.audio(converted_audio_path, format="audio/mp3")
                    
                    # Provide download links
                    col1, col2 = st.columns(2)
                    with col1:
                        with open(converted_audio_path, "rb") as f:
                            st.download_button(
                                f"Download {selected_language} Audio (MP3)", 
                                f, 
                                file_name=f"audio_{lang_code}.mp3"
                            )
                    
                    with col2:
                        # Save translated text to file
                        translated_text_path = f"translated_text_{lang_code}.txt"
                        with open(translated_text_path, "w", encoding="utf-8") as f:
                            f.write(translated_text)
                        
                        with open(translated_text_path, "rb") as f:
                            st.download_button(
                                f"Download {selected_language} Text (TXT)", 
                                f, 
                                file_name=f"translated_{lang_code}.txt"
                            )
                    
                except Exception as e:
                    st.error(f"Error in translation/speech conversion: {str(e)}")
                    st.write("Make sure you have internet connection for translation and TTS to work.")
                    st.write("Try selecting a different language or check your internet connection.")

        # Provide download links
        st.success("✅ Done! Files ready to download:")
        with open(audio_path, "rb") as f:
            st.download_button("Download Original Audio (MP3)", f, file_name="original_audio.mp3")

        with open(text_path, "rb") as f:
            st.download_button("Download Transcript (TXT)", f, file_name="transcription.txt")

        # Show transcript inline
        st.subheader("📜 Transcript Preview")
        st.text_area("Transcript", text_output, height=200)

    # Clean up temporary video
    if os.path.exists(video_path):
        os.remove(video_path)
