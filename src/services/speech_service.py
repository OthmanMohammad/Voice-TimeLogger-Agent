import os
import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import tempfile

logger = logging.getLogger(__name__)

# Strategy Pattern for Speech-to-Text Providers
class SpeechToTextStrategy(ABC):
    """Abstract base class for speech-to-text conversion strategies."""
    
    @abstractmethod
    async def transcribe(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Transcribe the given audio file to text.
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            Dict containing 'text' key with the transcribed text
        """
        pass


class OpenAISpeechStrategy(SpeechToTextStrategy):
    """OpenAI Whisper API strategy for speech-to-text conversion."""
    
    def __init__(self, api_key: str):
        """
        Initialize the OpenAI speech strategy.
        
        Args:
            api_key: OpenAI API key
        """
        self.api_key = api_key
        import openai
        openai.api_key = api_key
        self.openai = openai
    
    async def transcribe(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Transcribe using OpenAI Whisper API.
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            Dict containing 'text' key with the transcribed text
        """
        try:
            with open(audio_file_path, "rb") as audio_file:
                response = await self.openai.Audio.atranscribe(
                    model="whisper-1",
                    file=audio_file
                )
            return {"text": response["text"], "provider": "openai"}
        except Exception as e:
            logger.error(f"OpenAI transcription error: {str(e)}")
            raise


class GoogleSpeechStrategy(SpeechToTextStrategy):
    """Google Speech-to-Text API strategy for speech-to-text conversion."""
    
    def __init__(self):
        """Initialize the Google Speech strategy."""
        from google.cloud import speech
        self.client = speech.SpeechClient()
        self.speech = speech
    
    async def transcribe(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Transcribe using Google Speech-to-Text API.
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            Dict containing 'text' key with the transcribed text
        """
        try:
            # Load the audio file
            with open(audio_file_path, "rb") as audio_file:
                content = audio_file.read()
            
            audio = self.speech.RecognitionAudio(content=content)
            
            config = self.speech.RecognitionConfig(
                encoding=self.speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="en-US",
                enable_automatic_punctuation=True,
            )
            
            response = self.client.recognize(config=config, audio=audio)
            
            transcript = ""
            for result in response.results:
                transcript += result.alternatives[0].transcript
            
            return {"text": transcript, "provider": "google"}
        except Exception as e:
            logger.error(f"Google transcription error: {str(e)}")
            raise


# Main Service Class with Strategy Pattern
class SpeechToTextService:
    """Service to convert speech to text using configurable providers."""
    
    def __init__(self, provider: str = "openai", api_key: Optional[str] = None):
        """
        Initialize the speech to text service with the specified strategy.
        
        Args:
            provider: The provider to use ('openai' or 'google')
            api_key: API key for the provider
        """
        self.provider = provider.lower()
        
        if self.provider == "openai":
            api_key = api_key or os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key is required")
            self.strategy = OpenAISpeechStrategy(api_key)
        elif self.provider == "google":
            self.strategy = GoogleSpeechStrategy()
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    async def transcribe(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Transcribe the given audio file to text using the selected strategy.
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            Dict containing 'text' key with the transcribed text
        """
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        return await self.strategy.transcribe(audio_file_path)
    
    @staticmethod
    def save_temp_audio(audio_data: bytes) -> str:
        """
        Save audio data to a temporary file.
        
        Args:
            audio_data: Raw audio data in bytes
            
        Returns:
            Path to the temporary audio file
        """
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_file.write(audio_data)
        temp_file.close()
        return temp_file.name