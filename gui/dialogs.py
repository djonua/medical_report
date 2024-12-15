import tkinter as tk
from tkinter import ttk, messagebox

class AddDoctorDialog:
    def __init__(self, parent, specializations):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Добавить врача")
        self.dialog.geometry("400x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Словарь соответствия специализаций
        self.specializations = specializations
        
        # Результат диалога
        self.result = None
        
        self._create_widgets()
        self._center_dialog(parent)
    
    def _create_widgets(self):
        # Создаем и размещаем элементы
        ttk.Label(self.dialog, text="ФИО врача:").pack(padx=10, pady=5)
        self.name_entry = ttk.Entry(self.dialog, width=40)
        self.name_entry.pack(padx=10, pady=5)
        
        ttk.Label(self.dialog, text="Специализация:").pack(padx=10, pady=5)
        self.specialization_var = tk.StringVar()
        self.specialization_combo = ttk.Combobox(
            self.dialog, 
            textvariable=self.specialization_var,
            values=list(self.specializations.keys()),
            state="readonly"
        )
        self.specialization_combo.pack(padx=10, pady=5)
        
        # Кнопки
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Сохранить", command=self.save).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Отмена", command=self.cancel).pack(side="left", padx=10)
    
    def _center_dialog(self, parent):
        self.dialog.update_idletasks()
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        self.dialog.geometry(f"+{x}+{y}")
    
    def save(self):
        name = self.name_entry.get().strip()
        specialization_ru = self.specialization_var.get()
        if name and specialization_ru:
            # Преобразуем русское название в английский код
            specialization_code = self.specializations[specialization_ru]
            self.result = (name, specialization_code)
            self.dialog.destroy()
        else:
            messagebox.showerror("Ошибка", "Заполните все поля")
    
    def cancel(self):
        self.dialog.destroy() 