import os
import logging
import tkinter as tk
from tkinter import messagebox
import threading
from datetime import datetime
from tkinter import ttk
from report_generator import generate_report
import subprocess

from chatgpt import ChatGPTAPI
from gui.dialogs import AddDoctorDialog
from gui.frames import CollapsibleFrame
from models.doctor import Doctor
from services.audio_service import AudioService
from services.storage_service import StorageService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AudioRecorderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Медицинский диктофон")
        self.root.geometry("500x600")
        
        # Инициализация сервисов
        self.storage_service = StorageService()
        self.audio_service = AudioService(
            on_interim_result=lambda text: self.update_transcript_text(text, is_final=False),
            on_final_result=lambda text, speaker=None: self.update_transcript_text(text, is_final=True, speaker=speaker)
        )
        
        # Состояние приложения
        self.is_recording = False
        self.start_time = None
        self.current_transcript_file = None
        
        # Загрузка данных
        self.patient_history = self.storage_service.load_patient_history()
        self.doctors = self.storage_service.load_doctors()
        self.last_selected_doctor = self.load_last_selected_doctor()
        
        # Создаем интерфейс
        self.setup_ui()
        
        # Устанавливаем последнего выбранного врача
        if self.last_selected_doctor in self.doctors:
            self.doctor_var.set(self.last_selected_doctor)
            self.on_doctor_selected()
    
    def setup_ui(self):
        # Фрейм для выбора врача
        doctor_frame = ttk.LabelFrame(self.root, text="Врач", padding=10)
        doctor_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(doctor_frame, text="Выберите врача:").pack(side="left", padx=5)
        
        # Комбобокс для выбора врача
        self.doctor_var = tk.StringVar()
        self.doctor_combo = ttk.Combobox(doctor_frame, 
                                       textvariable=self.doctor_var,
                                       values=list(self.doctors.keys()),
                                       state="readonly")
        self.doctor_combo.pack(side="left", fill="x", expand=True, padx=5)
        self.doctor_combo.bind('<<ComboboxSelected>>', self.on_doctor_selected)
        
        # Кнопка добавления врача
        ttk.Button(doctor_frame, text="Добавить врача", 
                  command=self.add_doctor_dialog).pack(side="left", padx=5)
        
        # Фрейм для данных пациента
        patient_frame = ttk.LabelFrame(self.root, text="Данные пациента", padding=10)
        patient_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(patient_frame, text="ФИО пациента:").pack(side="left", padx=5)
        
        # Комбобокс с автозаполнением
        self.patient_var = tk.StringVar()
        self.patient_combo = ttk.Combobox(patient_frame, 
                                        textvariable=self.patient_var,
                                        values=self.patient_history)
        self.patient_combo.pack(side="left", fill="x", expand=True, padx=5)
        self.patient_combo.bind('<Return>', self.add_patient)
        self.patient_combo.bind('<<ComboboxSelected>>', self.on_patient_selected)
        
        # Кнопка добавления пациента
        ttk.Button(patient_frame, text="Добавить", 
                  command=self.add_patient).pack(side="left", padx=5)
        
        # Таймер
        self.timer_label = ttk.Label(self.root, text="00:00:00", font=("Arial", 24))
        self.timer_label.pack(pady=20)
        
        # Кнопка записи
        self.record_button = ttk.Button(self.root, text="Начать прием", 
                                      command=self.toggle_recording)
        self.record_button.pack(pady=10)
        
        # Статус записи
        self.status_label = ttk.Label(self.root, text="Готов к записи")
        self.status_label.pack(pady=10)
        
        # Сворачиваемая панель с текстом расшифровки
        self.transcript_frame = CollapsibleFrame(self.root, text="Текст расшифровки")
        self.transcript_frame.pack(fill="x", padx=10, pady=5)
        
        # Текст расшифровки внутри сворачиваемой панели
        self.transcript_text = tk.Text(self.transcript_frame.sub_frame, 
                                     height=10, wrap="word", 
                                     font=("Courier New", 10))
        self.transcript_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Настраиваем теги для форматирования
        self.transcript_text.tag_configure("speaker1", foreground="blue")
        self.transcript_text.tag_configure("speaker2", foreground="green")
        self.transcript_text.tag_configure("interim", foreground="gray")
        
        # Полоса прокрутки для текста
        scrollbar = ttk.Scrollbar(self.transcript_frame.sub_frame, 
                                command=self.transcript_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.transcript_text.config(yscrollcommand=scrollbar.set)
        
        # Добавляем фрейм для ссылки на документ
        self.doc_link_frame = ttk.Frame(self.root)
        self.doc_link_frame.pack(pady=5, fill=tk.X, padx=10)
        self.doc_link_label = ttk.Label(self.doc_link_frame, text="", foreground="blue", cursor="hand2")
        self.doc_link_label.pack()
        self.doc_link_label.bind("<Button-1>", self.open_report)
        self.current_report_path = None
    
    def add_patient(self, event=None):
        """Добавление нового пациента в историю"""
        patient_name = self.patient_var.get().strip()
        if patient_name and patient_name not in self.patient_history:
            self.patient_history.append(patient_name)
            self.patient_combo['values'] = self.patient_history
            self.storage_service.save_patient_history(self.patient_history)
    
    def add_doctor_dialog(self):
        """Открытие диалога добавления врача"""
        dialog = AddDoctorDialog(self.root, Doctor.SPECIALIZATIONS)
        self.root.wait_window(dialog.dialog)
        if dialog.result:
            name, specialization = dialog.result
            self.doctors[name] = specialization
            self.storage_service.save_doctors(self.doctors)
            self.doctor_combo['values'] = list(self.doctors.keys())
            self.doctor_combo.set(name)
            self.on_doctor_selected()
    
    def on_patient_selected(self, event=None):
        """Обработка выбора пациента из списка"""
        pass
    
    def on_doctor_selected(self, event=None):
        """Обработка выбора врача"""
        selected_doctor = self.doctor_var.get()
        if selected_doctor:
            logger.info(f"Выбран врач: {selected_doctor} ({self.doctors[selected_doctor]})")
            self.save_last_selected_doctor()
    
    def update_transcript_text(self, text, is_final=False, speaker=None):
        """Обновление текста расшифровки"""
        if not text:  # Игнорируем пустой текст
            return
            
        if is_final:
            # Удаляем промежуточные результаты
            last_line_start = self.transcript_text.get("end-2c linestart", "end-1c")
            if last_line_start.startswith("Промежуточно:"):
                self.transcript_text.delete("end-2c linestart", "end-1c")
            
            # Определяем тег для спикера
            tag = None
            if speaker == 1:
                text = f"Врач: {text}\n"
                tag = "speaker1"
            elif speaker == 2:
                text = f"Пациент: {text}\n"
                tag = "speaker2"
            else:
                text = f"{text}\n"
            
            # Вставляем текст с тегом
            self.transcript_text.insert(tk.END, text, tag)
        else:
            # Показываем промежуточный текст, но не сохраняем его
            # Удаляем предыдущий промежуточный результат
            last_line_start = self.transcript_text.get("end-2c linestart", "end-1c")
            if last_line_start.startswith("Промежуточно:"):
                self.transcript_text.delete("end-2c linestart", "end-1c")
            
            # Добавляем новый промежуточный текст серым цветом
            self.transcript_text.insert(tk.END, f"Промежуточно: {text}\n", "interim")
        
        # Прокручиваем к последней строке
        self.transcript_text.see(tk.END)
    
    def update_timer(self):
        if self.is_recording and self.start_time:
            elapsed_time = datetime.now() - self.start_time
            hours = int(elapsed_time.total_seconds() // 3600)
            minutes = int((elapsed_time.total_seconds() % 3600) // 60)
            seconds = int(elapsed_time.total_seconds() % 60)
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.timer_label.config(text=time_str)
            self.root.after(1000, self.update_timer)
    
    def process_results(self):
        """Обработка результатов"""
        try:
            if not os.path.exists(self.current_transcript_file):
                raise FileNotFoundError("Файл транскрипта не найден")
            
            if os.path.getsize(self.current_transcript_file) == 0:
                raise ValueError("Файл транскрипта пуст")
            
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Получаем ФИО пациента
            patient_name = self.patient_var.get().strip()
            if not patient_name:
                patient_name = "Не указано"
            
            # Получаем выбранного врача
            selected_doctor = self.doctor_var.get()
            if not selected_doctor:
                raise ValueError("Не выбран врач")
            
            doctor_type = self.doctors[selected_doctor]
            
            # Импортируем соответствующий модуль
            try:
                module_name = f"templates.{doctor_type}"
                process_file = __import__(module_name, fromlist=['process_file']).process_file
            except ImportError:
                raise ImportError(f"Шаблон для специализации {doctor_type} не найден")
            
            # Обрабатываем через ChatGPT
            chatgpt_api = ChatGPTAPI(api_key=os.getenv('OPENAI_API_KEY'))
            result = process_file(self.current_transcript_file, chatgpt_api, None)
            
            # Добавляем информацию о враче и пациенте в результат
            if isinstance(result, dict):
                if 'patient' not in result:
                    result['patient'] = {}
                result['patient']['name'] = patient_name
                result['doctor'] = {
                    'name': selected_doctor,
                    'specialization': Doctor.SPECIALIZATIONS_REVERSE.get(doctor_type, doctor_type)
                }
            
            # Сохраняем результат в JSON
            result_file = self.storage_service.save_result(result, current_time)
            logger.info(f"Результат сохранен в {result_file}")
            
            # Создаем отчет в формате DOCX
            report_text = self.format_report_text(result)
            report_file = generate_report(patient_name=patient_name, report_text=report_text)
            
            if report_file:
                self.current_report_path = report_file
                # Обновляем текст ссылки
                self.doc_link_label.configure(text=f"Открыть заключение: {os.path.basename(report_file)}")
                messagebox.showinfo("Успех", "Заключение успешно сгенерировано")
            
            # Обновляем статус
            self.status_label.config(text="Готов к записи")
            self.reset_ui()
            
        except Exception as e:
            logger.error(f"Ошибка при обработке результатов: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось обработать результаты: {str(e)}")
            self.reset_ui()
        finally:
            # Разблокируем кнопку
            self.root.after(0, lambda: self.record_button.config(state="normal"))
            
    def format_report_text(self, result):
        """Форматирует результат из JSON в текст для отчета"""
        report_parts = []
        
        # Добавляем информацию о враче
        if 'doctor' in result:
            report_parts.append(f"Врач: {result['doctor']['name']}")
            report_parts.append(f"Специализация: {result['doctor']['specialization']}\n")
        
        # Добавляем жалобы
        if 'complaints' in result:
            report_parts.append("Жалобы:")
            for complaint in result['complaints']:
                report_parts.append(f"- {complaint}")
            report_parts.append("")
        
        # Добавляем диагноз
        if 'provisional diagnosis' in result:
            report_parts.append("Предварительный диагноз:")
            for diagnosis in result['provisional diagnosis']:
                report_parts.append(f"- {diagnosis}")
            report_parts.append("")
        
        # Доб��вляем рекомендации
        if 'recommendations' in result:
            report_parts.append("Рекомендации:")
            for recommendation in result['recommendations']:
                report_parts.append(f"- {recommendation}")
        
        return "\n".join(report_parts)
    
    def reset_ui(self):
        """Сброс интерфейса в исходное состояние"""
        self.timer_label.config(text="00:00:00")
        self.status_label.config(text="Готов к записи")
        self.record_button.config(state="normal")
        self.record_button.config(text="Начать прием")
    
    def toggle_recording(self):
        if not self.is_recording:
            # Проверяем наличие ключей API
            if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
                messagebox.showerror("Ошибка", "Не установлена переменная окружения GOOGLE_APPLICATION_CREDENTIALS")
                return
            if not os.getenv('OPENAI_API_KEY'):
                messagebox.showerror("Ошибка", "Не установлена переменная окружения OPENAI_API_KEY")
                return
            
            # Проверяем выбор врача
            if not self.doctor_var.get():
                messagebox.showerror("Ошибка", "Пожалуйста, выберите врача")
                return
            
            # Проверяем выбор пациента
            if not self.patient_var.get().strip():
                messagebox.showerror("Ошибка", "Пожалуйста, выберите пациента")
                return
            
            # Начинаем запись
            self.is_recording = True
            self.record_button.config(text="Завершить прием")
            self.status_label.config(text="Идет запись...")
            self.start_time = datetime.now()
            
            # Инициализируем файл транскрипта
            current_time = self.start_time.strftime("%Y%m%d_%H%M%S")
            self.current_transcript_file = f"audio_records/transcript_{current_time}.txt"
            
            # Запускаем таймер
            self.update_timer()
            
            # Запускаем запись в отдельном потоке
            self.recording_thread = threading.Thread(target=self.audio_service.start_recording)
            self.recording_thread.start()
        else:
            # Останавливаем запи��ь
            self.is_recording = False
            self.record_button.config(state="disabled")
            self.status_label.config(text="Завершение записи...")
            
            def stop_recording():
                try:
                    # Останавливаем запись
                    self.audio_service.stop_recording()
                    
                    # Ждем завершения потока записи
                    if self.recording_thread and self.recording_thread.is_alive():
                        self.recording_thread.join(timeout=5)
                    
                    # Сохраняем транскрипт
                    transcript_content = self.transcript_text.get("1.0", tk.END).strip()
                    if transcript_content:
                        with open(self.current_transcript_file, "w", encoding="utf-8") as f:
                            f.write(transcript_content)
                    
                    # Запускаем обработку результатов
                    if self.current_transcript_file and os.path.exists(self.current_transcript_file):
                        self.process_results()
                    
                    # Обновляем UI
                    self.root.after(0, self.reset_ui)
                except Exception as e:
                    logger.error(f"Ошибка при остановке записи: {str(e)}")
                    self.root.after(0, lambda: messagebox.showerror("Ошибка", 
                        f"Ошибка при остановке записи: {str(e)}"))
                    self.root.after(0, self.reset_ui)
            
            # Запускаем остановку записи в отдельном потоке
            threading.Thread(target=stop_recording).start()
    
    def save_settings(self, key, value):
        """Сохранение настройки в файл"""
        settings = self.load_settings()
        settings[key] = value
        with open("settings.txt", "w", encoding="utf-8") as f:
            for k, v in settings.items():
                f.write(f"{k}={v}\n")

    def load_settings(self):
        """Загрузка настроек из файла"""
        settings = {}
        try:
            with open("settings.txt", "r", encoding="utf-8") as f:
                for line in f:
                    key, value = line.strip().split('=', 1)
                    settings[key] = value
        except FileNotFoundError:
            pass
        return settings

    def save_last_selected_doctor(self):
        """Сохранение последнего выбранного врача"""
        self.save_settings("last_selected_doctor", self.doctor_var.get())

    def load_last_selected_doctor(self):
        """Загрузка последнего выбранного врача"""
        settings = self.load_settings()
        return settings.get("last_selected_doctor")

    def open_report(self, event=None):
        """Открывает сгенерированный отчет"""
        if self.current_report_path and os.path.exists(self.current_report_path):
            try:
                # Используем абсолютный путь
                abs_path = os.path.abspath(self.current_report_path)
                # Используем subprocess.Popen для Windows
                if os.name == 'nt':  # Для Windows
                    os.system(f'start "" "{abs_path}"')
                else:  # Для Linux/Mac
                    subprocess.call(["xdg-open", abs_path])
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть файл: {str(e)}")
                logger.error(f"Ошибка при открытии файла: {str(e)}")

    def process_gpt_response(self, response_text, patient_name):
        """Обрабатывает ответ от GPT и создает отчет"""
        # Создаем отчет
        report_file = generate_report(patient_name=patient_name, report_text=response_text)
        if report_file:
            self.current_report_path = report_file
            # Обновляем текст ссылки
            self.doc_link_label.configure(text=f"Открыть заключение: {os.path.basename(report_file)}")
            messagebox.showinfo("Успех", "Заключение успешно сгенерировано")
        else:
            messagebox.showerror("Ошибка", "Не удалось создать заключение")

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = AudioRecorderApp(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
        messagebox.showerror("Критическая ошибка", f"Приложение будет закрыто: {str(e)}")
