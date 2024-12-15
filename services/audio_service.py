import logging
from google.cloud import speech_v1p1beta1
import pyaudio
import wave
from datetime import datetime

logger = logging.getLogger(__name__)

class AudioService:
    def __init__(self, on_interim_result=None, on_final_result=None):
        self.on_interim_result = on_interim_result
        self.on_final_result = on_final_result
        self.is_recording = False
        self.client = None
        self.audio_input = None
        self.stream = None
    
    def start_recording(self):
        """Начало записи аудио"""
        self.is_recording = True
        self.client = speech_v1p1beta1.SpeechClient()
        
        config = speech_v1p1beta1.RecognitionConfig(
            encoding=speech_v1p1beta1.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="ru-RU",
            enable_speaker_diarization=True,
            diarization_speaker_count=2,
            enable_automatic_punctuation=True,
        )

        streaming_config = speech_v1p1beta1.StreamingRecognitionConfig(
            config=config, 
            interim_results=True
        )

        def audio_generator():
            self.audio_input = pyaudio.PyAudio()
            self.stream = self.audio_input.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024
            )
            
            logger.info("Начало записи аудио...")
            while self.is_recording:
                try:
                    data = self.stream.read(1024, exception_on_overflow=False)
                    yield speech_v1p1beta1.StreamingRecognizeRequest(audio_content=data)
                except Exception as e:
                    logger.error(f"Ошибка при чтении аудио: {str(e)}")
                    break

        requests = audio_generator()
        responses = self.client.streaming_recognize(streaming_config, requests)

        try:
            for response in responses:
                if not self.is_recording:
                    break

                if not response.results:
                    continue

                result = response.results[0]
                if not result.alternatives:
                    continue

                transcript = result.alternatives[0].transcript

                if result.is_final:
                    if hasattr(result, 'speaker_tags') and result.speaker_tags:
                        self._process_diarization(result, transcript)
                    else:
                        if self.on_final_result:
                            self.on_final_result(transcript)
                else:
                    if self.on_interim_result:
                        self.on_interim_result(transcript)

        except Exception as e:
            logger.error(f"Ошибка при транскрибации: {str(e)}")
            raise
    
    def _process_diarization(self, result, transcript):
        """Обработка результатов с диаризацией"""
        words_info = result.speaker_tags
        current_speaker = None
        speaker_text = ""

        for word_info in words_info:
            if current_speaker != word_info.speaker_tag:
                if current_speaker is not None:
                    speaker_num = (current_speaker % 2) + 1
                    if self.on_final_result:
                        self.on_final_result(speaker_text.strip(), speaker=speaker_num)
                current_speaker = word_info.speaker_tag
                speaker_text = word_info.word
            else:
                speaker_text += " " + word_info.word

        if speaker_text:
            speaker_num = (current_speaker % 2) + 1
            if self.on_final_result:
                self.on_final_result(speaker_text.strip(), speaker=speaker_num)
    
    def stop_recording(self):
        """Остановка записи"""
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio_input:
            self.audio_input.terminate()
        logger.info("Запись остановлена") 