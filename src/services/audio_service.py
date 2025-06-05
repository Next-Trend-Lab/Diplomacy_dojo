# src/services/audio_service.py

import base64
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import texttospeech_v1 as tts
from google.api_core.exceptions import GoogleAPIError

class AudioService:
    def __init__(self):
        self.stt_client = speech.SpeechClient()
        self.tts_client = tts.TextToSpeechClient()

    def transcribe_audio(self, audio_content_b64: str, sample_rate_hertz: int = 44100, language_code: str = "en-US") -> str:
        """
        Converts base64 encoded audio to text using Google Cloud Speech-to-Text.
        Assumes audio is in MP3 format for simplicity from frontend (Streamlit mic recorder).
        """
        try:
            audio_content_bytes = base64.b64decode(audio_content_b64)
            audio = speech.RecognitionAudio(content=audio_content_bytes)
            
            # Using MP3 encoding as it's common for web-captured audio
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.MP3, 
                sample_rate_hertz=sample_rate_hertz,
                language_code=language_code,
                enable_automatic_punctuation=True,
            )
            
            response = self.stt_client.recognize(config=config, audio=audio)
            
            if response.results:
                transcript = response.results[0].alternatives[0].transcript
                print(f"Transcribed audio: {transcript}")
                return transcript
            return ""
        except GoogleAPIError as e:
            print(f"Google Cloud Speech-to-Text API error: {e}")
            raise
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            raise

    def synthesize_speech(self, text: str, language_code: str = "en-US", voice_name: str = "en-US-Neural2-C") -> str:
        """
        Converts text to base64 encoded audio (MP3) using Google Cloud Text-to-Speech.
        """
        try:
            synthesis_input = tts.SynthesisInput(text=text)
            
            # Select a voice (Neural2 voices are high quality)
            voice = tts.VoiceSelectionParams(
                language_code=language_code,
                name=voice_name,
                ssml_gender=tts.SsmlVoiceGender.NEUTRAL,
            )
            
            # Select the type of audio file to return
            audio_config = tts.AudioConfig(
                audio_encoding=tts.AudioEncoding.MP3
            )
            
            response = self.tts_client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            
            audio_content_b64 = base64.b64encode(response.audio_content).decode('utf-8')
            print(f"Synthesized speech for text: {text[:50]}...") # Print first 50 chars
            return audio_content_b64
        except GoogleAPIError as e:
            print(f"Google Cloud Text-to-Speech API error: {e}")
            raise
        except Exception as e:
            print(f"Error synthesizing speech: {e}")
            raise