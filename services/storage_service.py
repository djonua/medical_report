import os
import json
import logging
from models.doctor import Doctor

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        # Создаем необходимые директории
        self.required_dirs = ["audio_records", "Results"]
        self.create_directories()
    
    def create_directories(self):
        """Создание необходимых директорий"""
        for directory in self.required_dirs:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info(f"Создана директория {directory}")
    
    def load_doctors(self):
        """Загрузка списка врачей из файла"""
        try:
            if os.path.exists("doctors.json"):
                with open("doctors.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {name: spec for name, spec in data.items()}
        except Exception as e:
            logger.error(f"Ошибка при загрузке списка врачей: {str(e)}")
        return {
            "Авидзба Леонида": "pediatrician",
            "Амичба Амина": "general_physician"
        }
    
    def save_doctors(self, doctors):
        """Сохранение списка врачей в файл"""
        try:
            with open("doctors.json", "w", encoding="utf-8") as f:
                json.dump(doctors, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка при сохранении списка врачей: {str(e)}")
    
    def load_patient_history(self):
        """Загрузка истории пациентов из файла"""
        try:
            if os.path.exists("patient_history.json"):
                with open("patient_history.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка при загрузке истории пациентов: {str(e)}")
        return []
    
    def save_patient_history(self, history):
        """Сохранение истории пациентов в файл"""
        try:
            with open("patient_history.json", "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка при сохранении истории пациентов: {str(e)}")
    
    def save_transcript(self, transcript, timestamp):
        """Сохранение транскрипта в файл"""
        filename = f"audio_records/transcript_{timestamp}.txt"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(transcript)
            return filename
        except Exception as e:
            logger.error(f"Ошибка при сохранении транскрипта: {str(e)}")
            return None
    
    def save_result(self, result, timestamp):
        """Сохранение результата в JSON"""
        filename = f"Results/result_{timestamp}.json"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            return filename
        except Exception as e:
            logger.error(f"Ошибка при сохранении результата: {str(e)}")
            return None 