import tkinter as tk

from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog

import json

import os

import requests

import queue

import threading

import time

from datetime import datetime

import webbrowser

import pygame

import speech_recognition as sr

import psutil

import platform

import markdown

import html2text

from bs4 import BeautifulSoup

import re

import random

class Windows11AICoder:

    def __init__(self, root):

        self.root = root

        self.setup_config()

        self.setup_ui()

        self.setup_services()

        self.start_background_tasks()

        self.context = []

        self.current_response = ""

        self.is_generating = False

        self.response_queue = queue.Queue()

        self.add_to_chat("system", "Добро пожаловать в AI Coder Pro! Готов к работе.")

    def setup_config(self):

        self.config = {

            "current_model": "deepseek-coder",

            "ollama_host": "http://localhost:11434",

            "models": {

                "deepseek-coder": {

                    "pre_prompt": "Ты экспертный помощник по программированию. Давай чёткие ответы с примерами кода.",

                    "context_window": 16384,

                    "temperature": 0.3

                }

            },

            "ui": {

                "theme": "light",

                "font_size": 11

            }

        }

    def setup_ui(self):

        self.root.title("AI Coder Pro - Windows 11 Style")

        self.root.geometry("1200x800")

        self.root.minsize(1000, 700)

        self.style = ttk.Style()

        self.style.theme_use('vista')

        self.colors = {

            "light": {

                "bg": "#f3f3f3",

                "text": "#000000",

                "accent": "#0078d7",

                "card": "#ffffff"

            },

            "dark": {

                "bg": "#1a1a1a",

                "text": "#ffffff",

                "accent": "#4cc2ff",

                "card": "#2d2d2d"

            }

        }

        self.fonts = {

            "normal": ("Segoe UI", 11),

            "code": ("Consolas", 10),

            "title": ("Segoe UI", 12, "bold")

        }

        self.main_frame = ttk.Frame(self.root)

        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.create_header()

        self.create_chat_display()

        self.create_input_area()

        self.create_status_bar()

        self.apply_theme()

    def create_header(self):

        self.header = ttk.Frame(self.main_frame)

        self.header.pack(fill=tk.X, pady=(0, 10))

        self.model_var = tk.StringVar(value=self.config["current_model"])

        self.model_dropdown = ttk.Combobox(

            self.header,

            textvariable=self.model_var,

            values=list(self.config["models"].keys()),

            state="readonly",

            font=self.fonts["normal"],

            width=25

        )

        self.model_dropdown.pack(side=tk.LEFT, padx=5)

        self.title_label = tk.Label(

            self.header,

            text="AI Coder Pro",

            font=self.fonts["title"],

            fg=self.colors[self.config["ui"]["theme"]]["accent"],

            bg=self.colors[self.config["ui"]["theme"]]["bg"]

        )

        self.title_label.pack(side=tk.LEFT, expand=True)

        self.create_header_buttons()

    def create_header_buttons(self):

        btn_frame = ttk.Frame(self.header)

        btn_frame.pack(side=tk.RIGHT)

        settings_btn = ttk.Button(

            btn_frame,

            text="⚙️",

            command=self.show_settings,

            width=3

        )

        settings_btn.pack(side=tk.LEFT, padx=2)

        theme_btn = ttk.Button(

            btn_frame,

            text="🌓",

            command=self.toggle_theme,

            width=3

        )

        theme_btn.pack(side=tk.LEFT, padx=2)

    def create_chat_display(self):

        self.chat_display = scrolledtext.ScrolledText(

            self.main_frame,

            wrap=tk.WORD,

            font=self.fonts["normal"],

            bg=self.colors[self.config["ui"]["theme"]]["card"],

            fg=self.colors[self.config["ui"]["theme"]]["text"],

            insertbackground=self.colors[self.config["ui"]["theme"]]["text"],

            padx=15,

            pady=15,

            state='disabled'

        )

        self.chat_display.pack(fill=tk.BOTH, expand=True)

        self.setup_text_tags()

    def setup_text_tags(self):

        self.chat_display.tag_config("user",

                                   foreground=self.colors[self.config["ui"]["theme"]]["accent"])

        self.chat_display.tag_config("assistant",

                                   foreground=self.colors[self.config["ui"]["theme"]]["text"])

        self.chat_display.tag_config("system",

                                   foreground="#5d5d5d")

        self.chat_display.tag_config("code",

                                   background="#f5f5f5" if self.config["ui"]["theme"] == "light" else "#3a3a3a",

                                   font=self.fonts["code"],

                                   relief=tk.FLAT,

                                   borderwidth=0,

                                   lmargin1=20,

                                   lmargin2=20)

    def create_input_area(self):

        self.input_frame = ttk.Frame(self.main_frame)

        self.input_frame.pack(fill=tk.X, pady=(10, 0))

        self.user_input = tk.Text(

            self.input_frame,

            height=4,

            font=self.fonts["normal"],

            bg=self.colors[self.config["ui"]["theme"]]["card"],

            fg=self.colors[self.config["ui"]["theme"]]["text"],

            insertbackground=self.colors[self.config["ui"]["theme"]]["text"],

            wrap=tk.WORD,

            relief=tk.FLAT,

            highlightthickness=1,

            highlightbackground="#e5e5e5",

            highlightcolor=self.colors[self.config["ui"]["theme"]]["accent"]

        )

        self.user_input.pack(fill=tk.X, expand=True, side=tk.LEFT)

        self.user_input.bind("<Return>", self.on_enter_pressed)

        self.user_input.bind("<Shift-Return>", self.on_shift_enter)

        self.create_input_buttons()

    def create_input_buttons(self):

        btn_frame = ttk.Frame(self.input_frame)

        btn_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        send_btn = ttk.Button(

            btn_frame,

            text="Отправить",

            command=self.send_message,

            style="Accent.TButton"

        )

        send_btn.pack(fill=tk.X, pady=(0, 5))

        voice_btn = ttk.Button(

            btn_frame,

            text="Голос",

            command=self.toggle_voice_input

        )

        voice_btn.pack(fill=tk.X, pady=5)

    def create_status_bar(self):

        self.status_bar = ttk.Frame(self.main_frame, height=24)

        self.status_bar.pack(fill=tk.X, pady=(10, 0))

        self.status_label = ttk.Label(

            self.status_bar,

            text="Готов",

            anchor=tk.W

        )

        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.sys_info_label = ttk.Label(

            self.status_bar,

            text=f"{platform.system()} {platform.release()} | Python {platform.python_version()}",

            anchor=tk.E

        )

        self.sys_info_label.pack(side=tk.RIGHT)

    def setup_services(self):

        self.recognizer = sr.Recognizer()

        self.microphone = sr.Microphone()

        self.is_listening = False

        pygame.mixer.init()

    def start_background_tasks(self):

        self.root.after(100, self.process_responses)

        self.root.after(1000, self.update_system_info)

    def apply_theme(self):

        theme = self.config["ui"]["theme"]

        self.style.configure(".",

                           background=self.colors[theme]["bg"],

                           foreground=self.colors[theme]["text"],

                           font=self.fonts["normal"])

        self.style.configure("TFrame",

                           background=self.colors[theme]["bg"])

        self.style.configure("TLabel",

                           background=self.colors[theme]["bg"],

                           foreground=self.colors[theme]["text"])

        self.style.configure("TButton",

                           background="#f3f3f3",

                           foreground=self.colors[theme]["text"],

                           borderwidth=0)

        self.style.configure("Accent.TButton",

                           background=self.colors[theme]["accent"],

                           foreground="white")

        self.root.config(bg=self.colors[theme]["bg"])

        self.chat_display.config(

            bg=self.colors[theme]["card"],

            fg=self.colors[theme]["text"],

            insertbackground=self.colors[theme]["text"]

        )

        self.user_input.config(

            bg=self.colors[theme]["card"],

            fg=self.colors[theme]["text"],

            insertbackground=self.colors[theme]["text"]

        )

    def toggle_theme(self):

        self.config["ui"]["theme"] = "dark" if self.config["ui"]["theme"] == "light" else "light"

        self.apply_theme()

        self.setup_text_tags()

    def on_enter_pressed(self, event):

        self.send_message()

        return "break"

    def on_shift_enter(self, event):

        self.user_input.insert(tk.INSERT, "\n")

        return "break"

    def send_message(self):

        message = self.user_input.get("1.0", tk.END).strip()

        if not message:

            return

        self.add_to_chat("user", message)

        self.user_input.delete("1.0", tk.END)

        self.status_label.config(text="Генерация ответа...")

        threading.Thread(target=self.generate_response, daemon=True).start()

    def generate_response(self):

        time.sleep(1)

        responses = [

            "Вот пример кода для решения вашей задачи:\n```python\nprint('Hello World!')\n```",

            "Для этого вам понадобится использовать цикл for:\n```python\nfor i in range(10):\n    print(i)\n```",

            "Я могу предложить такое решение:\n```python\ndef calculate(a, b):\n    return a + b\n```"

        ]

        response = random.choice(responses)

        self.add_to_chat("assistant", response)

        self.status_label.config(text="Готов")

    def add_to_chat(self, sender, message):

        self.chat_display.config(state='normal')

        if sender == "user":

            self.chat_display.insert(tk.END, "Вы: ", "user")

        elif sender == "assistant":

            self.chat_display.insert(tk.END, "AI: ", "assistant")

        else:

            self.chat_display.insert(tk.END, "Система: ", "system")

        if "```" in message:

            parts = message.split("```")

            for i, part in enumerate(parts):

                if i % 2 == 1:

                    self.chat_display.insert(tk.END, part + "\n", "code")

                else:

                    self.chat_display.insert(tk.END, part)

        else:

            self.chat_display.insert(tk.END, message)

        self.chat_display.insert(tk.END, "\n\n")

        self.chat_display.config(state='disabled')

        self.chat_display.see(tk.END)

    def toggle_voice_input(self):

        if self.is_listening:

            self.stop_voice_input()

        else:

            self.start_voice_input()

    def start_voice_input(self):

        self.is_listening = True

        self.status_label.config(text="Слушаю... Говорите")

        threading.Thread(target=self.process_voice_input, daemon=True).start()

    def stop_voice_input(self):

        self.is_listening = False

        self.status_label.config(text="Готов")

    def process_voice_input(self):

        try:

            with self.microphone as source:

                self.recognizer.adjust_for_ambient_noise(source)

                audio = self.recognizer.listen(source, timeout=5)

            text = self.recognizer.recognize_google(audio, language="ru-RU")

            self.user_input.insert(tk.END, text)

            self.status_label.config(text="Голосовой ввод завершен")

        except Exception as e:

            self.status_label.config(text=f"Ошибка: {str(e)}")

        finally:

            self.stop_voice_input()

    def process_responses(self):

        self.root.after(100, self.process_responses)

    def update_system_info(self):

        cpu = psutil.cpu_percent()

        ram = psutil.virtual_memory().percent

        self.sys_info_label.config(

            text=f"CPU: {cpu}% | RAM: {ram}% | {platform.system()}"

        )

        self.root.after(5000, self.update_system_info)

    def show_settings(self):

        settings = tk.Toplevel(self.root)

        settings.title("Настройки")

        settings.geometry("500x300")

        notebook = ttk.Notebook(settings)

        notebook.pack(fill=tk.BOTH, expand=True)

        model_tab = ttk.Frame(notebook)

        notebook.add(model_tab, text="Модель")

        ttk.Label(model_tab, text="Адрес сервера Ollama:").pack(pady=5)

        ttk.Entry(model_tab).pack(fill=tk.X, padx=20, pady=5)

        ui_tab = ttk.Frame(notebook)

        notebook.add(ui_tab, text="Интерфейс")

        ttk.Label(ui_tab, text="Размер шрифта:").pack(pady=5)

        ttk.Combobox(ui_tab, values=[10, 11, 12, 14]).pack(fill=tk.X, padx=20, pady=5)

def main():

    root = tk.Tk()

    app = Windows11AICoder(root)

    root.mainloop()

if __name__ == "__main__":

    main()