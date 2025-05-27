import tkinter as tk

from tkinter import scrolledtext, ttk, messagebox, filedialog, simpledialog

import threading

import time

import json

import os

from datetime import datetime

_speech_recognition_available = False

try:

    import speech_recognition as sr

    _speech_recognition_available = True

except ImportError:

    pass

_pygame_available = False

try:

    import pygame

    _pygame_available = True

except ImportError:

     pass

_requests_available = False

try:

    import requests

    _requests_available = True

except ImportError:

    pass

_psutil_available = False

try:

    import psutil

    _psutil_available = True

except ImportError:

    pass

_web_parsing_available = False

try:

    from bs4 import BeautifulSoup

    import html2text

    _web_parsing_available = True

except ImportError:

     pass

_markdown_available = False

try:

    import markdown

    _markdown_available = True

except ImportError:

    pass

import webbrowser

import platform

import queue

import logging

import re

logging.basicConfig(

    level=logging.INFO,

    format='%(asctime)s - %(levelname)s - %(message)s',

    filename='ai_coder.log',

    filemode='a'

)

logger = logging.getLogger("AICoderUltimate")

console_handler = logging.StreamHandler()

console_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(levelname)s - %(message)s')

console_handler.setFormatter(formatter)

if not logger.handlers:

    logger.addHandler(console_handler)

class Tooltip:

    def __init__(self, widget, text):

        self.widget = widget

        self.text = text

        self.tooltip_window = None

        self.opacity = 0.0

        self.timer = None

        widget.bind("<Enter>", self.on_enter)

        widget.bind("<Leave>", self.on_leave)

        widget.bind("<ButtonPress>", self.on_leave)

    def on_enter(self, event=None):

        self.timer = self.widget.after(700, self.show)

    def on_leave(self, event=None):

        if self.timer:

            self.widget.after_cancel(self.timer)

            self.timer = None

        self.hide()

    def show(self):

        if self.tooltip_window:

            return

        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 10

        y = self.widget.winfo_rooty() + (self.widget.winfo_height() // 2)

        self.tooltip_window = tk.Toplevel(self.widget)

        self.tooltip_window.wm_overrideredirect(True)

        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        self.tooltip_window.attributes("-alpha", 0.0)

        label = tk.Label(

            self.tooltip_window,

            text=self.text,

            bg="#d6d6d6",

            fg="#333333",

            relief=tk.SOLID,

            borderwidth=1,

            padx=8,

            pady=4,

            font=("Segoe UI", 9)

        )

        label.pack()

        self.opacity = 0.0

        self._fade_in()

    def hide(self):

        if not self.tooltip_window:

            return

        self._fade_out()

    def _fade_in(self):

        if self.tooltip_window and self.opacity < 1.0:

            self.opacity += 0.1

            if self.opacity > 1.0:

                self.opacity = 1.0

            try:

                self.tooltip_window.attributes("-alpha", self.opacity)

                self.widget.after(25, self._fade_in)

            except tk.TclError:

                pass

    def _fade_out(self):

        if self.tooltip_window and self.opacity > 0.0:

            self.opacity -= 0.1

            if self.opacity < 0.0:

                self.opacity = 0.0

            try:

                self.tooltip_window.attributes("-alpha", self.opacity)

                self.widget.after(25, self._fade_out)

            except tk.TclError:

                 pass

        elif self.tooltip_window and self.opacity == 0.0:

            try:

                self.tooltip_window.destroy()

            except tk.TclError:

                pass

            self.tooltip_window = None

class AICoderUltimate:

    def __init__(self, root):

        self.root = root

        self.logger = logger

        self.logger.info("Initializing AI Coder Ultimate")

        self.root.title("AI Coder Ultimate ∞")

        self.root.geometry("1400x900")

        self.config_file = "ai_coder_config.json"

        self.load_config()

        self.context = []

        self.current_response_buffer = ""

        self.is_generating = False

        self.is_listening = False

        self._stop_requested = False

        self.response_queue = queue.Queue()

        self.current_links = {}

        self._assistant_response_start_index = None

        self.typing_animation_active = False

        self.typing_animation_index = 0

        self.typing_animation_id = None

        self.fullscreen_state = False

        self._check_service_availability()

        self.setup_theme()

        self.setup_styles()

        self.setup_services()

        self.setup_main_window()

        self.setup_menu()

        models_config = self.config.get("models", {})

        initial_model = self.config.get("current_model")

        if not initial_model or initial_model not in models_config:

             initial_model = list(models_config.keys())[0] if models_config else "default"

             if initial_model == "default":

                  self.logger.error("No models defined in config, using default placeholder.")

                  model_config = {"context_window": 8192, "pre_prompt": "You are a helpful AI."}

             else:

                  self.config["current_model"] = initial_model

                  self.save_config()

                  model_config = models_config.get(initial_model, {})

                  self.logger.warning(f"Invalid or missing current_model in config. Using first available model: {initial_model}")

        else:

             model_config = models_config.get(initial_model, {})

        self.context_limit = model_config.get("context_window", 8192)

        self.pre_prompt = model_config.get("pre_prompt", "")

        self.logger.info(f"Initial context limit set to {self.context_limit} for model {initial_model}")

        self.start_background_tasks()

        self.logger.info("Application initialized successfully")

    def _check_service_availability(self):

        if not _requests_available:

            self.logger.warning("Requests library not found. AI generation and web parsing will be disabled.")

        if not _speech_recognition_available:

            self.logger.warning("SpeechRecognition library not found. Voice input will be disabled.")

        if not _pygame_available:

             self.logger.warning("Pygame library not found. Audio feedback for voice input will be disabled.")

        if not _psutil_available:

            self.logger.warning("Psutil library not found. System monitoring will be disabled.")

        if not _web_parsing_available:

            self.logger.warning("BeautifulSoup4 or html2text library not found. Web parsing will be disabled.")

        if not _markdown_available:

            self.logger.warning("Markdown library not found. Assistant response formatting may be limited.")

    def setup_theme(self):

        self.themes = {

            "light": {

                "bg": "#f5f5f5",

                "bg_light": "#e8e8e8",

                "fg": "#333333",

                "primary": "#6c8ebf",

                "primary_light": "#8faed9",

                "secondary": "#82b366",

                "accent": "#b85450",

                "accent_light": "#d6b3b3",

                "text": "#333333",

                "text_light": "#555555",

                "code_bg": "#e1e1e1",

                "highlight": "#d6d6d6",

                "highlight_light": "#e0e0e0",

                "status": "#6c8ebf",

                "warning": "#d6b656",

                "error": "#d79b9b"

            },

            "dark": {

                "bg": "#2b2b2b",

                "bg_light": "#3c3c3c",

                "fg": "#cccccc",

                "primary": "#5f819d",

                "primary_light": "#7a9ebb",

                "secondary": "#7b9a66",

                "accent": "#a5504a",

                "accent_light": "#c08b8b",

                "text": "#cccccc",

                "text_light": "#999999",

                "code_bg": "#4e4e4e",

                "highlight": "#5a5a5a",

                "highlight_light": "#6a6a6a",

                "status": "#5f819d",

                "warning": "#c0a040",

                "error": "#c08b8b"

            }

        }

        theme_name = self.config.get("ui", {}).get("theme", "light")

        self.theme = self.themes.get(theme_name, self.themes["light"])

        self.current_theme_name = theme_name

        self.root.configure(bg=self.theme["bg"])

        font_size = self.config.get("ui", {}).get("font_size", 11)

        self.font_normal = ("Segoe UI", font_size)

        self.font_code = ("Consolas", max(font_size - 1, 8))

        self.font_title = ("Segoe UI", max(font_size + 3, 12), "bold")

        self.font_small = ("Segoe UI", max(font_size - 2, 8))

        self.apply_theme_to_widgets()

    def apply_theme_to_widgets(self):

        self.root.configure(bg=self.theme["bg"])

        if hasattr(self, 'main_frame') and self.main_frame.winfo_exists():

             self.main_frame.configure(bg=self.theme["bg"])

        if hasattr(self, 'header_frame') and self.header_frame.winfo_exists():

             self.header_frame.configure(bg=self.theme["bg"])

             if hasattr(self, 'title_label') and self.title_label.winfo_exists():

                  self.title_label.configure(fg=self.theme["primary"], bg=self.theme["bg"])

             if hasattr(self, 'context_label') and self.context_label.winfo_exists():

                  self.context_label.configure(fg=self.theme["text"], bg=self.theme["bg"])

             for widget in self.header_frame.winfo_children():

                  if isinstance(widget, tk.Button):

                       widget.configure(bg=self.theme["bg"], fg=self.theme["text"],

                                        activebackground=self.theme["highlight_light"], activeforeground=self.theme["text"])

        if hasattr(self, 'chat_display') and self.chat_display.winfo_exists():

             self.chat_display.configure(bg=self.theme["bg_light"], fg=self.theme["text"], insertbackground=self.theme["text"])

             self.configure_text_tags()

        if hasattr(self, 'input_frame') and self.input_frame.winfo_exists():

             self.input_frame.configure(bg=self.theme["bg"])

             if hasattr(self, 'user_input') and self.user_input.winfo_exists():

                  self.user_input.configure(bg=self.theme["bg_light"], fg=self.theme["text"],

                                           insertbackground=self.theme["text"],

                                           highlightbackground=self.theme["highlight"], highlightcolor=self.theme["highlight"])

             if hasattr(self, 'button_frame') and self.button_frame.winfo_exists():

                  self.button_frame.configure(bg=self.theme["bg"])

                  for widget in self.button_frame.winfo_children():

                       if isinstance(widget, tk.Button):

                            widget.configure(bg=self.theme["bg"], fg=self.theme["text"],

                                             activebackground=self.theme["highlight_light"], activeforeground=self.theme["text"])

        if hasattr(self, 'status_bar') and self.status_bar.winfo_exists():

             self.status_bar.configure(bg=self.theme["bg"])

             if hasattr(self, 'status_label') and self.status_label.winfo_exists():

                  self.status_label.configure(fg=self.theme["status"], bg=self.theme["bg"])

             if hasattr(self, 'sys_monitor') and self.sys_monitor.winfo_exists():

                  self.sys_monitor.configure(fg=self.theme["text"], bg=self.theme["bg"])

        self.setup_styles()

    def setup_styles(self):

        style = ttk.Style()

        style.configure("TCombobox",

                        fieldbackground=self.theme["bg_light"],

                        background=self.theme["bg_light"],

                        foreground=self.theme["text"],

                        arrowcolor=self.theme["fg"],

                        bordercolor=self.theme["highlight"],

                        lightcolor=self.theme["highlight"],

                        darkcolor=self.theme["highlight"],

                        padding=5,

                        font=self.font_normal

                        )

        style.map("TCombobox",

                  fieldbackground=[("readonly", self.theme["bg_light"])],

                  selectbackground=[("readonly", self.theme["primary_light"])],

                  selectforeground=[("readonly", self.theme["fg"])])

        style.configure("TProgressbar",

                        background=self.theme["primary"],

                        troughcolor=self.theme["bg_light"],

                        bordercolor=self.theme["highlight"])

        style.map("TProgressbar",

                  background=[('active', self.theme["primary_light"])])

        try:

             style.element_create("horizontal.Smooth.Progressbar.trough", "image", "hborder.png")

             style.layout("Smooth.Horizontal.TProgressbar",

                        [('Smooth.Horizontal.Progressbar.trough',

                          {'children': [('Smooth.Horizontal.Progressbar.pbar',

                                         {'side': 'left', 'sticky': 'ns'})],

                           'sticky': 'nswe'})])

             style.configure("Smooth.Horizontal.TProgressbar",

                             background=self.theme["secondary"],

                             troughcolor=self.theme["bg_light"])

             self.logger.info("Custom Smooth progressbar style loaded (requires hborder.png)")

        except tk.TclError:

             style.configure("Smooth.Horizontal.TProgressbar",

                             background=self.theme["secondary"],

                             troughcolor=self.theme["bg_light"])

             self.logger.warning("Could not create custom Smooth progressbar style. Using default TProgressbar appearance. (hborder.png missing?)")

    def clear_context(self):

        print("clear_context method called!")

        pass

    def load_config(self):

        default_config = {

                "ollama_host": "http://localhost:11434",

                "current_model": "deepseek-coder-v2",

                "models": {

                    "deepseek-coder-v2:16b": {

                        "pre_prompt": "You are an expert coding assistant that provides clear, concise, and correct code examples and explanations. Use markdown formatting for code blocks and explanations. Prioritize helpfulness and accuracy.",

                        "context_window": 16384,

                        "temperature": 0.3,

                        "max_tokens": 4096,

                        "description": "DeepSeek Coder V2 16B - Excellent for coding tasks."

                    },

                   "llama3": {

                        "pre_prompt": "You are a helpful and harmless AI assistant. Provide clear and detailed responses, using markdown formatting where appropriate.",

                        "context_window": 8192,

                        "temperature": 0.7,

                        "max_tokens": 2000,

                        "description": "Llama 3 - General purpose AI assistant."

                    }

                },

                "ui": {

                    "font_size": 11,

                    "theme": "light",

                    "animation_speed": 1.0,

                    "enable_animations": True

                },

                "voice_input": {

                    "enabled": True,

                    "language": "en-US",

                    "hotkey": "<Control-v>"

                },

                "shortcuts": {

                    "send_message": "<Control-Return>",

                    "clear_context": "<Control-l>",

                    "stop_generation": "<Control-s>",

                    "open_settings": "<Control-p>",

                    "parse_web": "<Control-w>"

                }

        }

        try:

            if os.path.exists(self.config_file):

                with open(self.config_file, "r", encoding="utf-8") as f:

                    config_data = json.load(f)

                    self.config = default_config

                    self._deep_update(self.config, config_data)

                self.logger.info("Configuration loaded successfully")

            else:

                self.config = default_config

                self.save_config()

                self.logger.info("Configuration file not found, created default config")

        except Exception as e:

            self.logger.error(f"Failed to load configuration: {str(e)}. Using default config.")

            self.config = default_config

            self.save_config()

    def _deep_update(self, target, source):

        for key, value in source.items():

            if isinstance(value, dict) and key in target and isinstance(target[key], dict):

                self._deep_update(target[key], value)

            else:

                target[key] = value

    def save_config(self):

        try:

            with open(self.config_file, "w", encoding="utf-8") as f:

                json.dump(self.config, f, indent=2)

            self.logger.info("Configuration saved")

        except Exception as e:

            self.logger.error(f"Failed to save config: {str(e)}")

    def setup_services(self):

        self.recognizer = None

        self.microphone = None

        if _speech_recognition_available and self.config["voice_input"].get("enabled", True):

            try:

                self.recognizer = sr.Recognizer()

                try:

                    self.microphone = sr.Microphone()

                    self.logger.info("Speech Recognition initialized")

                except Exception as e:

                     self.microphone = None

                     self.logger.error(f"Microphone initialization error: {e}. Voice input disabled.")

                     self.update_status("Microphone not found. Voice input disabled.", level="error")

            except Exception as e:

                self.logger.error(f"Speech Recognition initialization error: {e}. Voice input disabled.")

                self.recognizer = None

                self.update_status("Speech Recognition unavailable. Voice input disabled.", level="error")

        elif not _speech_recognition_available:

             self.logger.warning("SpeechRecognition not installed. Voice input disabled.")

        else:

             self.logger.info("Voice input disabled in config.")

        self.listen_sound = None

        self.stop_sound = None

        if _pygame_available:

             try:

                 pygame.mixer.init()

                 script_dir = os.path.dirname(__file__)

                 listen_sound_path = os.path.join(script_dir, "listen_start.wav")

                 stop_sound_path = os.path.join(script_dir, "listen_stop.wav")

                 if os.path.exists(listen_sound_path):

                      self.listen_sound = pygame.mixer.Sound(listen_sound_path)

                 else:

                      self.logger.warning(f"{listen_sound_path} not found.")

                 if os.path.exists(stop_sound_path):

                      self.stop_sound = pygame.mixer.Sound(stop_sound_path)

                 else:

                      self.logger.warning(f"{stop_sound_path} not found.")

                 if self.listen_sound or self.stop_sound:

                      self.logger.info("Audio feedback sounds loaded")

                 else:

                      pygame.mixer.quit()

                      self.logger.info("Audio feedback disabled (sound files not found).")

             except Exception as e:

                 self.logger.error(f"Pygame mixer initialization error: {e}. Audio feedback disabled.")

                 self.listen_sound = self.stop_sound = None

                 try: pygame.mixer.quit()

                 except Exception: pass

        else:

             self.logger.warning("Pygame not installed. Audio feedback disabled.")

    def setup_main_window(self):

        self.main_frame = tk.Frame(self.root, bg=self.theme["bg"])

        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.setup_header(self.main_frame)

        self.setup_chat_display(self.main_frame)

        self.setup_input_area(self.main_frame)

        self.setup_status_bar(self.main_frame)

        if self.config["ui"].get("enable_animations", True):

             self.animate_welcome_message()

        else:

             self.add_to_chat("system", f"Welcome to AI Coder Ultimate!\n\nCurrent model: {self.config['current_model']}\nReady to assist you.")

    def setup_header(self, parent):

        self.header_frame = tk.Frame(parent, bg=self.theme["bg"], pady=5)

        self.header_frame.pack(fill=tk.X, pady=(0, 15))

        self.model_var = tk.StringVar(value=self.config["current_model"])

        model_options = list(self.config["models"].keys())

        if self.model_var.get() not in model_options and model_options:

             self.model_var.set(model_options[0])

             self.config["current_model"] = model_options[0]

             self.save_config()

        elif not model_options:

             model_options = ["No models found"]

             self.model_var.set("No models found")

             messagebox.showerror("Config Error", "No AI models defined in ai_coder_config.json")

             self.logger.error("No AI models defined in config.")

        self.model_dropdown = ttk.Combobox(

            self.header_frame,

            textvariable=self.model_var,

            values=model_options,

            state="readonly" if model_options[0] != "No models found" else "disabled",

            font=self.font_normal,

            width=25,

            style="TCombobox"

        )

        self.model_dropdown.pack(side=tk.LEFT, padx=10)

        self.model_dropdown.bind("<<ComboboxSelected>>", self.change_model)

        self.title_label = tk.Label(

            self.header_frame,

            text="✦ AI Coder Ultimate ✦",

            font=self.font_title,

            fg=self.theme["primary"],

            bg=self.theme["bg"]

        )

        self.title_label.pack(side=tk.LEFT, expand=True)

        self.setup_context_indicator(self.header_frame)

        info_btn = tk.Button(

            self.header_frame,

            text="ℹ️",

            command=self.show_model_info,

            font=("Segoe UI Emoji", 14),

            bg=self.theme["bg"],

            fg=self.theme["primary"],

            activebackground=self.theme["highlight_light"],

            activeforeground=self.theme["primary"],

            relief=tk.FLAT,

            borderwidth=0,

            cursor="hand2"

        )

        info_btn.pack(side=tk.RIGHT, padx=10)

        Tooltip(info_btn, "Show model information")

    def setup_context_indicator(self, parent):

        indicator_frame = tk.Frame(parent, bg=self.theme["bg"])

        indicator_frame.pack(side=tk.RIGHT, padx=10)

        self.context_label = tk.Label(

            indicator_frame,

            text="Context:",

            font=self.font_small,

            fg=self.theme["text"],

            bg=self.theme["bg"]

        )

        self.context_label.pack(side=tk.LEFT)

        self.context_indicator = ttk.Progressbar(

            indicator_frame,

            orient=tk.HORIZONTAL,

            length=180,

            mode='determinate',

            style="Smooth.Horizontal.TProgressbar"

        )

        self.context_indicator.pack(side=tk.LEFT, padx=5)

        self.update_context_indicator()

        Tooltip(self.context_indicator, "Current context memory usage (based on message count).\nApproximate token usage depends on the model.")

    def setup_chat_display(self, parent):

        self.chat_display = scrolledtext.ScrolledText(

            parent,

            wrap=tk.WORD,

            font=self.font_normal,

            bg=self.theme["bg_light"],

            fg=self.theme["text"],

            insertbackground=self.theme["text"],

            padx=25,

            pady=25,

            state='disabled',

            relief=tk.FLAT,

            highlightthickness=0,

            borderwidth=0

        )

        self.chat_display.pack(fill=tk.BOTH, expand=True)

        self.configure_text_tags()

        self.chat_display.tag_bind("link", "<Button-1>", self.open_link)

        self.chat_display.tag_bind("link", "<Enter>", lambda e: self.chat_display.config(cursor="hand2"))

        self.chat_display.tag_bind("link", "<Leave>", lambda e: self.chat_display.config(cursor=""))

    def configure_text_tags(self):

        for tag in self.chat_display.tag_names():

            if not tag.startswith("vtext"):

                 self.chat_display.tag_delete(tag)

        self.chat_display.tag_config("user",

                                    foreground=self.theme["secondary"],

                                    font=(self.font_normal[0], self.font_normal[1], "bold"))

        self.chat_display.tag_config("assistant",

                                    foreground=self.theme["primary"],

                                    font=self.font_normal)

        self.chat_display.tag_config("system",

                                    foreground=self.theme["accent"],

                                    font=(self.font_normal[0], self.font_normal[1], "italic"))

        self.chat_display.tag_config("code",

                                    background=self.theme["code_bg"],

                                    foreground=self.theme["text"],

                                    font=self.font_code,

                                    relief=tk.FLAT,

                                    borderwidth=0,

                                    lmargin1=25,

                                    lmargin2=25,

                                    spacing1=8,

                                    spacing3=8)

        self.chat_display.tag_config("inline-code",

                                    background=self.theme["code_bg"],

                                    foreground=self.theme["text"],

                                    font=self.font_code,

                                    relief=tk.FLAT,

                                    borderwidth=0,

                                    )

        self.chat_display.tag_config("link",

                                    foreground=self.theme["primary"],

                                    underline=True)

        self.chat_display.tag_config("quote",

                                    foreground=self.theme["text_light"],

                                    lmargin1=30,

                                    lmargin2=30,

                                    spacing1=5)

        self.chat_display.tag_config("bold", font=(self.font_normal[0], self.font_normal[1], "bold"))

        self.chat_display.tag_config("italic", font=(self.font_normal[0], self.font_normal[1], "italic"))

        self.chat_display.tag_config("bold-italic", font=(self.font_normal[0], self.font_normal[1], "bold", "italic"))

        self.chat_display.tag_config("h1", font=(self.font_title[0], max(self.font_title[1]+6, 20), "bold"), spacing1=15, spacing3=10)

        self.chat_display.tag_config("h2", font=(self.font_title[0], max(self.font_title[1]+3, 16), "bold"), spacing1=12, spacing3=8)

        self.chat_display.tag_config("h3", font=(self.font_title[0], self.font_title[1], "bold"), spacing1=10, spacing3=6)

        self.chat_display.tag_config("streaming_marker", elide=True)

    def setup_input_area(self, parent):

        input_frame = tk.Frame(parent, bg=self.theme["bg"], pady=10)

        input_frame.pack(fill=tk.X)

        self.user_input = tk.Text(

            input_frame,

            height=5,

            font=self.font_normal,

            bg=self.theme["bg_light"],

            fg=self.theme["text"],

            insertbackground=self.theme["text"],

            wrap=tk.WORD,

            relief=tk.FLAT,

            highlightthickness=1,

            highlightbackground=self.theme["highlight"],

            highlightcolor=self.theme["highlight"],

            borderwidth=0,

            padx=10,

            pady=10

        )

        self.user_input.pack(fill=tk.X, expand=True, side=tk.LEFT, ipady=5)

        self.user_input.bind("<Control-Return>", self.send_message_event)

        self.user_input.bind("<Return>", self.insert_newline)

        self.user_input.bind("<Shift-Return>", self.insert_newline)

        button_frame = tk.Frame(input_frame, bg=self.theme["bg"])

        button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(15, 0))

        buttons = [

            ("✉️", self.send_message, "Send message", self.config["shortcuts"].get("send_message", "<Control-Return>")),

            ("🎤", self.toggle_voice_input, "Toggle voice input", self.config["voice_input"].get("hotkey", "<Control-v>")),

            ("🧹", self.clear_context, "Clear conversation context", self.config["shortcuts"].get("clear_context", "<Control-l>")),

            ("✖️", self.stop_generation, "Stop current generation", self.config["shortcuts"].get("stop_generation", "<Control-s>")),

            ("⚙️", self.show_settings, "Open settings", self.config["shortcuts"].get("open_settings", "<Control-p>")),

            ("🌐", self.parse_web_content, "Parse web content", self.config["shortcuts"].get("parse_web", "<Control-w>"))

        ]

        for icon, command, tooltip_text, shortcut in buttons:

            btn = tk.Button(

                button_frame,

                text=icon,

                command=command,

                font=("Segoe UI Emoji", 14),

                bg=self.theme["bg"],

                fg=self.theme["text"],

                activebackground=self.theme["highlight_light"],

                activeforeground=self.theme["text"],

                relief=tk.FLAT,

                borderwidth=0,

                padx=8,

                pady=5,

                cursor="hand2"

            )

            btn.pack(fill=tk.X, pady=3)

            Tooltip(btn, f"{tooltip_text}\nShortcut: {shortcut}")

            self.root.bind(shortcut, lambda e=None, cmd=command: cmd())

    def insert_newline(self, event):

        self.user_input.insert(tk.INSERT, "\n")

        return "break"

    def setup_status_bar(self, parent):

        self.status_bar = tk.Frame(parent, bg=self.theme["bg"], height=24)

        self.status_bar.pack(fill=tk.X, pady=(10, 0))

        self.status_label = tk.Label(

            self.status_bar,

            text="Ready",

            anchor=tk.W,

            font=self.font_small,

            fg=self.theme["status"],

            bg=self.theme["bg"]

        )

        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        self.sys_monitor = tk.Label(

            self.status_bar,

            text="",

            anchor=tk.E,

            font=self.font_small,

            fg=self.theme["text"],

            bg=self.theme["bg"]

        )

        self.sys_monitor.pack(side=tk.RIGHT, padx=10)

        if _psutil_available:

             self.update_system_monitor()

        else:

             self.sys_monitor.config(text="Sys Mon Unavailable")

             self.logger.warning("System monitoring disabled due to missing psutil.")

    def setup_menu(self):

        menubar = tk.Menu(self.root,

                          bg=self.theme["bg_light"],

                          fg=self.theme["text"],

                          activebackground=self.theme["highlight_light"],

                          activeforeground=self.theme["text"],

                          relief=tk.FLAT)

        file_menu = tk.Menu(menubar, tearoff=0,

                            bg=self.theme["bg_light"],

                            fg=self.theme["text"],

                            activebackground=self.theme["highlight_light"],

                            activeforeground=self.theme["text"])

        file_menu.add_command(label="New Chat", command=self.new_chat, accelerator="Ctrl+N")

        file_menu.add_command(label="Save Chat", command=self.save_chat, accelerator="Ctrl+S")

        file_menu.add_command(label="Load Chat", command=self.load_chat, accelerator="Ctrl+O")

        file_menu.add_separator()

        file_menu.add_command(label="Export as Markdown", command=self.export_markdown)

        file_menu.add_command(label="Export as HTML", command=self.export_html)

        file_menu.add_separator()

        file_menu.add_command(label="Exit", command=self.root.quit)

        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0,

                           bg=self.theme["bg_light"],

                           fg=self.theme["text"],

                           activebackground=self.theme["highlight_light"],

                           activeforeground=self.theme["text"])

        edit_menu.add_command(label="Copy Last Response", command=self.copy_last_response, accelerator="Ctrl+C")

        edit_menu.add_command(label="Clear Context", command=self.clear_context, accelerator="Ctrl+L")

        edit_menu.add_separator()

        edit_menu.add_command(label="Preferences", command=self.show_settings, accelerator="Ctrl+P")

        menubar.add_cascade(label="Edit", menu=edit_menu)

        view_menu = tk.Menu(menubar, tearoff=0,

                            bg=self.theme["bg_light"],

                            fg=self.theme["text"],

                            activebackground=self.theme["highlight_light"],

                            activeforeground=self.theme["text"])

        view_menu.add_command(label="Toggle Fullscreen", command=self.toggle_fullscreen, accelerator="F11")

        view_menu.add_command(label="Zoom In", command=lambda: self.change_font_size(1), accelerator="Ctrl++")

        view_menu.add_command(label="Zoom Out", command=lambda: self.change_font_size(-1), accelerator="Ctrl+-")

        view_menu.add_separator()

        theme_menu = tk.Menu(view_menu, tearoff=0,

                             bg=self.theme["bg_light"],

                             fg=self.theme["text"],

                             activebackground=self.theme["highlight_light"],

                             activeforeground=self.theme["text"])

        self.theme_var = tk.StringVar(value=self.current_theme_name)

        for theme_name in self.themes.keys():

             theme_menu.add_radiobutton(label=theme_name.capitalize(),

                                        variable=self.theme_var,

                                        value=theme_name,

                                        command=self.change_theme)

        view_menu.add_cascade(label="Theme", menu=theme_menu)

        self.animations_enabled_var = tk.BooleanVar(value=self.config["ui"].get("enable_animations", True))

        view_menu.add_checkbutton(label="Enable Animations", command=self.toggle_animations, variable=self.animations_enabled_var)

        menubar.add_cascade(label="View", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=0,

                           bg=self.theme["bg_light"],

                           fg=self.theme["text"],

                           activebackground=self.theme["highlight_light"],

                           activeforeground=self.theme["text"])

        help_menu.add_command(label="Documentation", command=self.show_docs)

        help_menu.add_command(label="API Reference (Ollama)", command=self.show_api_reference)

        help_menu.add_command(label="Model Info", command=self.show_model_info)

        help_menu.add_separator()

        help_menu.add_command(label="About", command=self.show_about)

        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

        self.root.bind("<Control-n>", lambda e: self.new_chat())

        self.root.bind("<Control-s>", lambda e: self.save_chat())

        self.root.bind("<Control-o>", lambda e: self.load_chat())

        self.root.bind("<F11>", lambda e: self.toggle_fullscreen())

        self.root.bind("<Control-plus>", lambda e: self.change_font_size(1))

        self.root.bind("<Control-minus>", lambda e: self.change_font_size(-1))

        self.root.bind("<Control-equal>", lambda e: self.change_font_size(1))

    def animate_welcome_message(self):

        if not self.config["ui"].get("enable_animations", True):

             return

        welcome_msg = f"Welcome to AI Coder Ultimate!\n\nCurrent model: {self.config['current_model']}\nReady to assist you."

        self.chat_display.config(state='normal')

        self.chat_display.insert(tk.END, "System: ", "system")

        self.chat_display.config(state='disabled')

        def type_message(index=0):

            if not self.root.winfo_exists(): return

            if index < len(welcome_msg):

                self.chat_display.config(state='normal')

                self.chat_display.insert(tk.END, welcome_msg[index], "system")

                self.chat_display.config(state='disabled')

                self.chat_display.see(tk.END)

                animation_delay = int(50 * (1.0 / self.config["ui"].get("animation_speed", 1.0)))

                self.root.after(animation_delay, lambda: type_message(index + 1))

            else:

                 self.add_to_chat("system", "", newline=True)

        type_message()

    def change_model(self, event=None):

        new_model = self.model_var.get()

        if new_model in self.config["models"] and new_model != self.config["current_model"]:

            self.logger.info(f"Attempting to change model to {new_model}")

            if self.is_generating:

                 messagebox.showwarning("Warning", "Cannot change model while generating a response.")

                 self.model_var.set(self.config["current_model"])

                 return

            if self.config["ui"].get("enable_animations", True):

                 self.animate_model_change(new_model)

            self.config["current_model"] = new_model

            self.save_config()

            model_config = self.config["models"].get(new_model, {})

            self.context_limit = model_config.get("context_window", 8192)

            self.pre_prompt = model_config.get("pre_prompt", "")

            self.logger.info(f"Context limit set to {self.context_limit} for model {new_model}")

            self.clear_context(ask_confirm=False)

            self.chat_display.config(state='normal')

            self.chat_display.delete("1.0", tk.END)

            self.chat_display.config(state='disabled')

            self.current_response_buffer = ""

            self.current_links = {}

            self._assistant_response_start_index = None

            if self.config["ui"].get("enable_animations", True):

                 self.animate_welcome_message()

            else:

                 self.add_to_chat("system", f"Switched model to {new_model}.\nReady to assist you.")

            self.update_context_indicator()

            self.logger.info(f"Changed model successfully to {new_model}")

        elif new_model not in self.config["models"]:

            messagebox.showerror("Error", f"Model '{new_model}' not found in configuration.")

            self.model_var.set(self.config["current_model"])

            self.logger.error(f"Attempted to switch to non-existent model: {new_model}")

    def change_theme(self):

        new_theme_name = self.theme_var.get()

        if new_theme_name != self.current_theme_name and new_theme_name in self.themes:

            self.theme = self.themes[new_theme_name]

            self.current_theme_name = new_theme_name

            if "ui" not in self.config: self.config["ui"] = {}

            self.config["ui"]["theme"] = new_theme_name

            self.save_config()

            self.apply_theme_to_widgets()

            self.update_status(f"Theme changed to {new_theme_name.capitalize()}.")

            self.logger.info(f"Theme changed to {new_theme_name}.")

    def animate_model_change(self, new_model):

        if not self.config["ui"].get("enable_animations", True):

             return

        current_text = self.title_label.cget("text")

        new_text = f"✦ Switching to {new_model}... ✦"

        animation_duration_ms = 500

        steps = 20

        delay_per_step = animation_duration_ms // (2 * steps)

        delay_per_step = int(delay_per_step * (1.0 / self.config["ui"].get("animation_speed", 1.0)))

        if delay_per_step < 1: delay_per_step = 1

        def run_animation(step=0):

            if not self.root.winfo_exists():

                return

            if step <= steps:

                ratio = 1.0 - step / steps

                color = self.blend_colors(self.theme["primary"], self.theme["bg"], ratio)

                self.title_label.config(fg=color)

                self.root.after(delay_per_step, lambda: run_animation(step + 1))

            elif step <= 2 * steps:

                if step == steps + 1:

                    self.title_label.config(text=new_text)

                ratio = (step - steps) / steps

                color = self.blend_colors(self.theme["primary"], self.theme["bg"], ratio)

                self.title_label.config(fg=color)

                self.root.after(delay_per_step, lambda: run_animation(step + 1))

            else:

                self.title_label.config(text=f"✦ AI Coder Ultimate ✦", fg=self.theme["primary"])

        run_animation()

    def blend_colors(self, color1_hex, color2_hex, ratio):

        try:

            r1, g1, b1 = int(color1_hex[1:3], 16), int(color1_hex[3:5], 16), int(color1_hex[5:7], 16)

            r2, g2, b2 = int(color2_hex[1:3], 16), int(color2_hex[3:5], 16), int(color2_hex[5:7], 16)

            r = int(r1 * ratio + r2 * (1 - ratio))

            g = int(g1 * ratio + g2 * (1 - ratio))

            b = int(b1 * ratio + b2 * (1 - ratio))

            return f"#{r:02x}{g:02x}{b:02x}"

        except (ValueError, IndexError) as e:

            self.logger.error(f"Invalid color format for blending: {color1_hex}, {color2_hex}. Error: {e}")

            return color1_hex

    def send_message_event(self, event):

        if event.keysym != 'Return' or (event.state & 0x4):

             self.send_message()

             return "break"

    def send_message(self):

        if self.is_generating:

             self.update_status("Already generating a response. Please wait or stop.")

             return

        if not _requests_available:

             self.update_status("Cannot send message. Requests library not available.", level="error")

             return

        message = self.user_input.get("1.0", tk.END).strip()

        if not message:

            self.update_status("Please enter a message.")

            return

        self.add_to_chat("user", message)

        self.user_input.delete("1.0", tk.END)

        self.add_to_context({"role": "user", "content": message})

        self.current_response_buffer = ""

        self._assistant_response_start_index = None

        self.add_to_chat("assistant", "", newline=False)

        self._assistant_response_start_index = self.chat_display.index(tk.END)

        self._stop_requested = False

        self.start_typing_animation()

        self.update_status("Generating response...")

        threading.Thread(target=self.generate_response, daemon=True).start()

    def generate_response(self):

        if not _requests_available:

            self.response_queue.put("Error: Requests library not available.")

            self.response_queue.put(None)

            return

        try:

            self.is_generating = True

            messages = [{"role": "system", "content": self.pre_prompt}] + self.context

            ollama_url = f"{self.config.get('ollama_host', 'http://localhost:11434').rstrip('/')}/api/chat"

            model_config = self.config["models"].get(self.config["current_model"], {})

            response = requests.post(

                ollama_url,

                json={

                    "model": self.config["current_model"],

                    "messages": messages,

                    "stream": True,

                    "options": {

                        "temperature": model_config.get("temperature", 0.7),

                        "num_ctx": self.context_limit,

                        "num_predict": model_config.get("max_tokens", -1)

                    }

                },

                stream=True,

                timeout=180

            )

            response.raise_for_status()

            for line in response.iter_lines():

                if self._stop_requested:

                    self.logger.info("Generation stopped prematurely.")

                    break

                if line:

                    try:

                        chunk = json.loads(line)

                        if "message" in chunk and "content" in chunk["message"]:

                             content = chunk["message"]["content"]

                             if content:

                                self.response_queue.put(content)

                        if chunk.get("done"):

                            break

                    except json.JSONDecodeError:

                        self.logger.error(f"Failed to decode JSON chunk from Ollama: {line}")

                    except Exception as e:

                        self.logger.error(f"Error processing Ollama stream chunk: {e}")

        except requests.exceptions.ConnectionError:

            error_msg = f"Error: Could not connect to Ollama at {self.config.get('ollama_host', 'http://localhost:11434')}. Make sure Ollama is running and accessible."

            self.response_queue.put(error_msg)

            self.logger.error(error_msg)

        except requests.exceptions.Timeout:

            error_msg = "Error: Ollama response timed out."

            self.response_queue.put(error_msg)

            self.logger.error(error_msg)

        except requests.exceptions.RequestException as e:

            error_msg = f"Error during Ollama request: {str(e)}"

            self.response_queue.put(error_msg)

            self.logger.error(error_msg)

        except Exception as e:

            error_msg = f"An unexpected error occurred during generation: {str(e)}"

            self.response_queue.put(error_msg)

            self.logger.error(error_msg)

        finally:

            self.is_generating = False

            self.response_queue.put(None)

    def process_response_queue(self):

        try:

            while True:

                content = self.response_queue.get_nowait()

                if content is None:

                    self.stop_typing_animation()

                    if self.current_response_buffer:

                        self.add_to_context({"role": "assistant", "content": self.current_response_buffer})

                        self.chat_display.config(state='normal')

                        if self._assistant_response_start_index:

                             self.chat_display.delete(self._assistant_response_start_index, tk.END)

                             self.render_markdown_response_at_index(self.current_response_buffer, self._assistant_response_start_index)

                        else:

                             self.render_markdown_response(self.current_response_buffer)

                        self.chat_display.config(state='disabled')

                        self._assistant_response_start_index = None

                    else:

                        self.chat_display.config(state='normal')

                        if self._assistant_response_start_index:

                             prefix_start = self.chat_display.search(f"{self.config.get('current_model', 'Assistant')}: ", self._assistant_response_start_index, backwards=True, regexp=False)

                             if prefix_start:

                                  self.chat_display.delete(prefix_start, tk.END)

                             self._assistant_response_start_index = None

                        self.chat_display.config(state='disabled')

                    self.current_response_buffer = ""

                    if self._stop_requested:

                         self.update_status("Generation stopped.")

                    elif "Error:" in (content or ""):

                         self.update_status("Generation finished with error.", level="error")

                    else:

                        self.update_status("Ready")

                elif content.startswith("Error:"):

                    self.stop_typing_animation()

                    self.update_status("Generation Error", level="error")

                    self.add_to_chat("system", content)

                    self.current_response_buffer = ""

                    self._assistant_response_start_index = None

                else:

                    self.current_response_buffer += content

                    self.chat_display.config(state='normal')

                    if self._assistant_response_start_index:

                         self.chat_display.insert(tk.END, content, "assistant")

                         self.chat_display.see(tk.END)

                    self.chat_display.config(state='disabled')

        except queue.Empty:

            pass

        if self.root.winfo_exists():

             self.root.after(50, self.process_response_queue)

    def render_markdown_response(self, markdown_text):

        if not _markdown_available:

            self.add_to_chat("system", "Markdown library not available. Displaying raw text.")

            last_assistant_tag_ranges = self.chat_display.tag_ranges("assistant")

            if last_assistant_tag_ranges:

                 start_index = last_assistant_tag_ranges[-1].string

                 self.chat_display.config(state='normal')

                 self.chat_display.insert(start_index, markdown_text, "assistant")

                 self.chat_display.insert(tk.END, "\n\n")

                 self.chat_display.config(state='disabled')

                 self.chat_display.see(tk.END)

            else:

                 self.add_to_chat("assistant", markdown_text, newline=True)

            return

        self.chat_display.config(state='normal')

        start_index = None

        last_assistant_tag_ranges = self.chat_display.tag_ranges("assistant")

        if last_assistant_tag_ranges:

             end_of_prefix_index = last_assistant_tag_ranges[-1].string

             start_index = end_of_prefix_index

             self.chat_display.delete(start_index, tk.END)

        else:

             start_index = tk.END

        self.current_links = {}

        try:

            html_content = markdown.markdown(markdown_text, extensions=['fenced_code', 'nl2br', 'codehilite', 'extra'])

            soup = BeautifulSoup(html_content, 'html.parser')

            self._process_soup_element(soup.body, start_index, base_tag="assistant")

        except Exception as e:

            self.logger.error(f"Failed to parse HTML or apply Tkinter tags: {e}")

            self.chat_display.insert(start_index, markdown_text, "assistant")

        self.chat_display.insert(tk.END, "\n\n")

        self.chat_display.config(state='disabled')

        self.chat_display.see(tk.END)

    def render_markdown_response_at_index(self, markdown_text, start_index):

        if not _markdown_available:

            self.chat_display.config(state='normal')

            self.chat_display.insert(start_index, markdown_text, "assistant")

            self.chat_display.config(state='disabled')

            self.chat_display.see(tk.END)

            return

        self.chat_display.config(state='normal')

        self.current_links = {}

        try:

            html_content = markdown.markdown(markdown_text, extensions=['fenced_code', 'nl2br', 'codehilite', 'extra'])

            soup = BeautifulSoup(html_content, 'html.parser')

            self._process_soup_element(soup.body, start_index, base_tag="assistant")

        except Exception as e:

            self.logger.error(f"Failed to render loaded markdown: {e}")

            self.chat_display.insert(start_index, markdown_text, "assistant")

    def _process_soup_element(self, element, current_index, base_tag="assistant"):

        if not element:

            return current_index

        if isinstance(element, str):

            self.chat_display.insert(current_index, element, base_tag)

            return self.chat_display.index(tk.INSERT)

        if element.name:

            tag_name = element.name.lower()

            if tag_name in ['p', 'div', 'blockquote', 'ul', 'ol', 'li', 'pre', 'code', 'h1', 'h2', 'h3', 'hr']:

                try:

                    prev_char_index = self.chat_display.index(f"{current_index} -1c")

                    prev_char = self.chat_display.get(prev_char_index)

                    if current_index != '1.0' and prev_char != '\n':

                        self.chat_display.insert(current_index, "\n")

                        current_index = self.chat_display.index(tk.INSERT)

                except tk.TclError:

                    pass

                tags_to_apply = [base_tag]

                if tag_name == 'blockquote':

                    tags_to_apply.append('quote')

                elif tag_name.startswith('h') and len(tag_name) == 2 and tag_name[1].isdigit():

                    tags_to_apply.append(tag_name)

                elif tag_name == 'pre':

                    tags_to_apply.append('code')

                for child in element.contents:

                    current_index = self._process_soup_element(child, current_index, base_tag=tuple(tags_to_apply) if len(tags_to_apply) > 1 else base_tag)

                if tag_name not in ['pre', 'code', 'hr']:

                    self.chat_display.insert(current_index, "\n")

                    current_index = self.chat_display.index(tk.INSERT)

                elif tag_name == 'hr':

                     self.chat_display.insert(current_index, "\n" + "-"*20 + "\n", "system")

                     current_index = self.chat_display.index(tk.INSERT)

            elif tag_name in ['strong', 'b']:

                tags_to_apply = list(base_tag if isinstance(base_tag, tuple) else [base_tag]) + ['bold']

                for child in element.contents:

                    current_index = self._process_soup_element(child, current_index, base_tag=tuple(tags_to_apply))

            elif tag_name in ['em', 'i']:

                tags_to_apply = list(base_tag if isinstance(base_tag, tuple) else [base_tag]) + ['italic']

                for child in element.contents:

                    current_index = self._process_soup_element(child, current_index, base_tag=tuple(tags_to_apply))

            elif tag_name == 'code':

                 if element.parent and element.parent.name != 'pre':

                    tags_to_apply = list(base_tag if isinstance(base_tag, tuple) else [base_tag]) + ['inline-code']

                    for child in element.contents:

                        self.chat_display.insert(current_index, str(child), tuple(tags_to_apply))

                        current_index = self.chat_display.index(tk.INSERT)

                 else:

                      for child in element.contents:

                           current_index = self._process_soup_element(child, current_index, base_tag=base_tag)

            elif tag_name == 'a':

                url = element.get('href', '')

                link_text = "".join(child.get_text() if child.name else str(child) for child in element.contents)

                if not link_text: link_text = url

                if url:

                    tag_name = f"link_{len(self.current_links)}"

                    self.current_links[tag_name] = url

                    tags_to_apply = list(base_tag if isinstance(base_tag, tuple) else [base_tag]) + ["link", tag_name]

                    self.chat_display.insert(current_index, link_text, tuple(tags_to_apply))

                    current_index = self.chat_display.index(tk.INSERT)

                else:

                    self.chat_display.insert(current_index, link_text, base_tag)

                    current_index = self.chat_display.index(tk.INSERT)

            elif tag_name == 'br':

                self.chat_display.insert(current_index, "\n")

                current_index = self.chat_display.index(tk.INSERT)

            elif tag_name in ['ul', 'ol']:

                 for child in element.contents:

                      if child.name == 'li':

                           current_index = self._process_soup_element(child, current_index, base_tag=base_tag)

            elif tag_name == 'li':

                 list_marker = "- "

                 if element.parent and element.parent.name == 'ol':

                      list_marker = "1. "

                 self.chat_display.insert(current_index, list_marker, base_tag)

                 current_index = self.chat_display.index(tk.INSERT)

                 for child in element.contents:

                      current_index = self._process_soup_element(child, current_index, base_tag=base_tag)

                 self.chat_display.insert(current_index, "\n", base_tag)

                 current_index = self.chat_display.index(tk.INSERT)

            else:

                for child in element.contents:

                    current_index = self._process_soup_element(child, current_index, base_tag=base_tag)

            return current_index

        return current_index

    def open_link(self, event):

        index = self.chat_display.index(f"@{event.x},{event.y}")

        tags_at_click = self.chat_display.tag_names(index)

        clicked_url = None

        link_tag_name = None

        for tag in tags_at_click:

            if tag.startswith("link_"):

                link_tag_name = tag

                clicked_url = self.current_links.get(tag)

                break

        if clicked_url:

            if self.config["ui"].get("enable_animations", True) and link_tag_name:

                original_color = self.chat_display.tag_cget(link_tag_name, "foreground")

                self.chat_display.tag_config(link_tag_name, foreground=self.theme["accent"])

                self.root.update_idletasks()

                animation_delay = int(150 * (1.0 / self.config["ui"].get("animation_speed", 1.0)))

                self.root.after(animation_delay, lambda: self.chat_display.tag_config(link_tag_name, foreground=original_color))

            try:

                webbrowser.open(clicked_url)

                self.logger.info(f"Opened link: {clicked_url}")

                self.update_status(f"Opened link: {clicked_url}")

            except Exception as e:

                self.update_status(f"Failed to open link: {clicked_url}", level="error")

                self.logger.error(f"Failed to open link {clicked_url}: {e}")

    def add_to_chat(self, sender, message, newline=True):

        self.chat_display.config(state='normal')

        if self.chat_display.index("end-1c") != "1.0":

             last_char = self.chat_display.get("end-2c", "end-1c")

             if last_char != "\n":

                  self.chat_display.insert(tk.END, "\n")

        if sender == "user":

            prefix = "You: "

            tag = "user"

        elif sender == "assistant":

            prefix = f"{self.config.get('current_model', 'Assistant')}: "

            tag = "assistant"

        else:

            prefix = "System: "

            tag = "system"

        self.chat_display.insert(tk.END, prefix, tag)

        if message:

             if sender in ["user", "system"]:

                  self._process_text_with_links(message, tag)

             else:

                  pass

        if newline:

            self.chat_display.insert(tk.END, "\n")

        self.chat_display.config(state='disabled')

        self.chat_display.see(tk.END)

    def _process_text_with_links(self, text, base_tag):

        parts = re.split(r'(https?://[^\s]+)', text)

        for i, part in enumerate(parts):

            if i % 2 == 1:

                url = part

                tag_name = f"link_{len(self.current_links)}"

                self.current_links[tag_name] = url

                self.chat_display.insert(tk.END, url, (base_tag, "link", tag_name))

            else:

                self.chat_display.insert(tk.END, part, base_tag)

    def add_to_context(self, message):

        self.context.append(message)

        self.trim_context()

        self.update_context_indicator()

        self.logger.debug(f"Added message to context. Current context size (messages): {len(self.context)}")

    def trim_context(self):

        estimated_tokens_per_message = 500

        max_messages_by_tokens = self.context_limit // estimated_tokens_per_message if estimated_tokens_per_message > 0 else 100

        min_messages_to_keep = 10

        trim_limit_messages = max(min_messages_to_keep, max_messages_by_tokens)

        fixed_pre_prompt_count = 1 if self.pre_prompt and self.context and self.context and self.context[0].get("role") == "system" and self.context[0].get("content") == self.pre_prompt else 0

        while len(self.context) > fixed_pre_prompt_count + trim_limit_messages:

             self.context.pop(fixed_pre_prompt_count)

             self.logger.debug("Trimmed oldest message from context.")

        self._messages_trim_limit = trim_limit_messages + fixed_pre_prompt_count

    def update_context_indicator(self):

        current_messages = len(self.context)

        max_messages = self._messages_trim_limit if hasattr(self, '_messages_trim_limit') else 50

        if max_messages <= 0: max_messages = 1

        value = min(100, (current_messages / max_messages) * 100)

        self.context_indicator["value"] = value

    def update_status(self, message, level="info"):

        color = self.theme.get(level, self.theme["status"])

        self.status_label.config(text=message, fg=color)

    def update_system_monitor(self):

        if not _psutil_available:

            return

        try:

            cpu_percent = psutil.cpu_percent(interval=1)

            mem_info = psutil.virtual_memory()

            ram_percent = mem_info.percent

            monitor_text = f"CPU: {cpu_percent:.1f}% | RAM: {ram_percent:.1f}%"

            self.sys_monitor.config(text=monitor_text)

        except Exception as e:

            self.logger.warning(f"Failed to get system stats: {e}")

            self.sys_monitor.config(text="Sys Info Err")

        if self.root.winfo_exists():

            self.root.after(5000, self.update_system_monitor)

    def start_typing_animation(self):

        if not self.config["ui"].get("enable_animations", True):

             return

        if self.typing_animation_active:

            return

        self.typing_animation_active = True

        self.typing_animation_index = 0

        self._animate_typing()

    def _animate_typing(self):

        if not self.typing_animation_active or not self.root.winfo_exists():

            return

        base_text = "Generating response"

        dots = "." * (self.typing_animation_index % 4)

        self.status_label.config(text=f"{base_text}{dots}")

        self.typing_animation_index += 1

        animation_delay = int(200 * (1.0 / self.config["ui"].get("animation_speed", 1.0)))

        if animation_delay < 1: animation_delay = 1

        self.typing_animation_id = self.root.after(animation_delay, self._animate_typing)

    def stop_typing_animation(self):

        if not self.typing_animation_active:

            return

        self.typing_animation_active = False

        if self.typing_animation_id:

            self.root.after_cancel(self.typing_animation_id)

            self.typing_animation_id = None

    def stop_generation(self):

        if self.is_generating:

            self._stop_requested = True

            self.update_status("Stopping generation...")

            self.logger.info("Stop generation requested by user.")

        else:

            self.update_status("No generation in progress.")

    def toggle_voice_input(self):

        if not _speech_recognition_available or not self.config["voice_input"].get("enabled", True):

             self.update_status("Voice input is disabled or dependencies are missing.", level="error")

             self.logger.error("Voice input toggle failed: Service not available or disabled in config.")

             return

        if not self.recognizer or not self.microphone:

             self.update_status("Voice input not fully initialized. Check microphone access and PyAudio.", level="error")

             self.logger.error("Voice input toggle failed: Recognizer or microphone not initialized.")

             return

        if self.is_listening:

            self.is_listening = False

            self.update_status("Voice input off.")

            if self.stop_sound:

                 try: pygame.mixer.Sound.play(self.stop_sound)

                 except Exception as e: self.logger.error(f"Failed to play stop sound: {e}")

            self.logger.info("Voice input stopped by user.")

        else:

            self.is_listening = True

            self.update_status("Listening...")

            if self.listen_sound:

                 try: pygame.mixer.Sound.play(self.listen_sound)

                 except Exception as e: self.logger.error(f"Failed to play listen sound: {e}")

            self.logger.info("Voice input started.")

            threading.Thread(target=self._listen_in_background, daemon=True).start()

    def _listen_in_background(self):

        if not self.recognizer or not self.microphone or not self.is_listening:

             self.is_listening = False

             self.root.after(0, self.update_status, "Voice input stopped unexpectedly.", level="error")

             self.logger.error("Voice input background thread started but services not available.")

             if self.stop_sound: self.stop_sound.play()

             return

        try:

            with self.microphone as source:

                self.recognizer.dynamic_energy_threshold = True

                self.recognizer.pause_threshold = 0.8

                self.recognizer.non_speaking_duration = 0.5

                self.root.after(0, self.update_status, "Listening...")

                while self.is_listening:

                    try:

                        audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)

                        self.root.after(0, self.update_status, "Processing voice input...")

                        lang = self.config["voice_input"].get("language", "en-US")

                        text = self.recognizer.recognize_google(audio, language=lang)

                        self.logger.info(f"Voice recognized: {text}")

                        self.root.after(0, self.user_input.insert, tk.END, text + " ")

                        self.root.after(0, self.update_status, "Ready" if not self.is_generating else "Generating...")

                    except sr.WaitTimeoutError:

                        if self.is_listening:

                             self.root.after(0, self.update_status, "Listening...")

                        pass

                    except sr.UnknownValueError:

                        self.root.after(0, self.update_status, "Could not understand audio.", level="warning")

                        self.logger.warning("Speech Recognition could not understand audio")

                        if self.is_listening: self.root.after(0, self.update_status, "Listening...")

                    except sr.RequestError as e:

                        self.root.after(0, self.update_status, f"Speech Recognition service error: {e}", level="error")

                        self.logger.error(f"Speech Recognition service error: {e}")

                        self.is_listening = False

                    except Exception as e:

                        self.root.after(0, self.update_status, f"Voice input error: {e}", level="error")

                        self.logger.error(f"Unexpected voice input error: {e}")

                        self.is_listening = False

        except Exception as e:

             self.logger.error(f"Error in voice input setup or loop: {e}")

             self.root.after(0, self.update_status, "Voice input encountered a fatal error.", "error")

             self.is_listening = False

        finally:

             if self.stop_sound:

                  try: pygame.mixer.Sound.play(self.stop_sound)

                  except Exception: pass

             self.root.after(0, self.update_status, "Ready" if not self.is_generating else "Generating...", level="info")

             self.is_listening = False

    def new_chat(self):

        if self.is_generating:

             messagebox.showwarning("Warning", "Cannot start new chat while generating a response.")

             return

        if self.context and messagebox.askyesno("New Chat", "Start a new conversation? This will clear the current context."):

            self.clear_context(ask_confirm=False)

            self.chat_display.config(state='normal')

            self.chat_display.delete("1.0", tk.END)

            self.chat_display.config(state='disabled')

            self.current_response_buffer = ""

            self.current_links = {}

            self._assistant_response_start_index = None

            self.update_status("New chat started.")

            if self.config["ui"].get("enable_animations", True):

                 self.animate_welcome_message()

            else:

                 self.add_to_chat("system", f"New chat started.\n\nCurrent model: {self.config['current_model']}\nReady to assist you.")

            self.logger.info("New chat started.")

        elif not self.context:

            self.clear_context(ask_confirm=False)

            self.chat_display.config(state='normal')

            self.chat_display.delete("1.0", tk.END)

            self.chat_display.config(state='disabled')

            self.current_response_buffer = ""

            self.current_links = {}

            self._assistant_response_start_index = None

            self.update_status("New chat started.")

            if self.config["ui"].get("enable_animations", True):

                 self.animate_welcome_message()

            else:

                 self.add_to_chat("system", f"New chat started.\n\nCurrent model: {self.config['current_model']}\nReady to assist you.")

            self.logger.info("New chat started (context was already empty).")

    def save_chat(self):

        if not self.context:

            messagebox.showinfo("Save Chat", "No conversation to save.")

            return

        file_path = filedialog.asksaveasfilename(

            defaultextension=".json",

            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],

            title="Save Conversation"

        )

        if file_path:

            try:

                with open(file_path, 'w', encoding='utf-8') as f:

                    json.dump(self.context, f, indent=2, ensure_ascii=False)

                messagebox.showinfo("Save Chat", "Conversation saved successfully.")

                self.update_status(f"Conversation saved to {os.path.basename(file_path)}")

                self.logger.info(f"Conversation saved to {file_path}")

            except Exception as e:

                messagebox.showerror("Save Error", f"Failed to save conversation: {e}")

                self.logger.error(f"Failed to save conversation: {e}")

    def load_chat(self):

        if self.is_generating:

             messagebox.showwarning("Warning", "Cannot load chat while generating a response.")

             return

        if self.context and not messagebox.askyesno("Load Chat", "Load a new conversation? This will clear the current context."):

            return

        file_path = filedialog.askopenfilename(

            defaultextension=".json",

            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],

            title="Load Conversation"

        )

        if file_path:

            try:

                with open(file_path, 'r', encoding='utf-8') as f:

                    loaded_context = json.load(f)

                if isinstance(loaded_context, list) and all(isinstance(msg, dict) and "role" in msg and "content" in msg for msg in loaded_context):

                    self.context = loaded_context

                    self.chat_display.config(state='normal')

                    self.chat_display.delete("1.0", tk.END)

                    self.current_links = {}

                    self._assistant_response_start_index = None

                    self.update_status("Rendering loaded chat...")

                    start_index = 1 if self.pre_prompt and self.context and self.context[0].get("role") == "system" and self.context[0].get("content") == self.pre_prompt else 0

                    for message in self.context[start_index:]:

                         role = message.get("role", "system")

                         content = message.get("content", "")

                         if role == "assistant":

                              self.add_to_chat("assistant", "", newline=False)

                              insert_index = self.chat_display.index(tk.END)

                              self.render_markdown_response_at_index(content, insert_index)

                         else:

                              self.add_to_chat(role, content, newline=True)

                    self.chat_display.config(state='disabled')

                    self.update_context_indicator()

                    messagebox.showinfo("Load Chat", "Conversation loaded successfully.")

                    self.update_status(f"Conversation loaded from {os.path.basename(file_path)}")

                    self.logger.info(f"Conversation loaded from {file_path}")

                else:

                    messagebox.showerror("Load Error", "Invalid conversation file format.")

                    self.logger.error(f"Invalid conversation file format: {file_path}")

                    self.clear_context(ask_confirm=False)

            except FileNotFoundError:

                messagebox.showerror("Load Error", "File not found.")

            except json.JSONDecodeError:

                messagebox.showerror("Load Error", "Invalid JSON format.")

                self.logger.error(f"Invalid JSON format in file: {file_path}")

            except Exception as e:

                messagebox.showerror("Load Error", f"Failed to load conversation: {e}")

                self.logger.error(f"Failed to load conversation: {e}")

    def render_markdown_response_at_index(self, markdown_text, start_index):

        if not _markdown_available:

            self.chat_display.config(state='normal')

            self.chat_display.insert(start_index, markdown_text, "assistant")

            self.chat_display.config(state='disabled')

            self.chat_display.see(tk.END)

            return

        self.chat_display.config(state='normal')

        self.current_links = {}

        try:

            html_content = markdown.markdown(markdown_text, extensions=['fenced_code', 'nl2br', 'codehilite', 'extra'])

            soup = BeautifulSoup(html_content, 'html.parser')

            self._process_soup_element(soup.body, start_index, base_tag="assistant")

        except Exception as e:

            self.logger.error(f"Failed to render loaded markdown: {e}")

            self.chat_display.insert(start_index, markdown_text, "assistant")

    def _process_soup_element(self, element, current_index, base_tag="assistant"):

        if not element:

            return current_index

        if isinstance(element, str):

            self.chat_display.insert(current_index, element, base_tag)

            return self.chat_display.index(tk.INSERT)

        if element.name:

            tag_name = element.name.lower()

            if tag_name in ['p', 'div', 'blockquote', 'ul', 'ol', 'li', 'pre', 'code', 'h1', 'h2', 'h3', 'hr']:

                try:

                    prev_char_index = self.chat_display.index(f"{current_index} -1c")

                    prev_char = self.chat_display.get(prev_char_index)

                    if current_index != '1.0' and prev_char != '\n':

                        self.chat_display.insert(current_index, "\n")

                        current_index = self.chat_display.index(tk.INSERT)

                except tk.TclError:

                    pass

                tags_to_apply = [base_tag]

                if tag_name == 'blockquote':

                    tags_to_apply.append('quote')

                elif tag_name.startswith('h') and len(tag_name) == 2 and tag_name[1].isdigit():

                    tags_to_apply.append(tag_name)

                elif tag_name == 'pre':

                    tags_to_apply.append('code')

                for child in element.contents:

                    current_index = self._process_soup_element(child, current_index, base_tag=tuple(tags_to_apply) if len(tags_to_apply) > 1 else base_tag)

                if tag_name not in ['pre', 'code', 'hr']:

                    self.chat_display.insert(current_index, "\n")

                    current_index = self.chat_display.index(tk.INSERT)

                elif tag_name == 'hr':

                     self.chat_display.insert(current_index, "\n" + "-"*20 + "\n", "system")

                     current_index = self.chat_display.index(tk.INSERT)

            elif tag_name in ['strong', 'b']:

                tags_to_apply = list(base_tag if isinstance(base_tag, tuple) else [base_tag]) + ['bold']

                for child in element.contents:

                    current_index = self._process_soup_element(child, current_index, base_tag=tuple(tags_to_apply))

            elif tag_name in ['em', 'i']:

                tags_to_apply = list(base_tag if isinstance(base_tag, tuple) else [base_tag]) + ['italic']

                for child in element.contents:

                    current_index = self._process_soup_element(child, current_index, base_tag=tuple(tags_to_apply))

            elif tag_name == 'code':

                 if element.parent and element.parent.name != 'pre':

                    tags_to_apply = list(base_tag if isinstance(base_tag, tuple) else [base_tag]) + ['inline-code']

                    for child in element.contents:

                        self.chat_display.insert(current_index, str(child), tuple(tags_to_apply))

                        current_index = self.chat_display.index(tk.INSERT)

                 else:

                      for child in element.contents:

                           current_index = self._process_soup_element(child, current_index, base_tag=base_tag)

            elif tag_name == 'a':

                url = element.get('href', '')

                link_text = "".join(child.get_text() if child.name else str(child) for child in element.contents)

                if not link_text: link_text = url

                if url:

                    tag_name = f"link_{len(self.current_links)}"

                    self.current_links[tag_name] = url

                    tags_to_apply = list(base_tag if isinstance(base_tag, tuple) else [base_tag]) + ["link", tag_name]

                    self.chat_display.insert(current_index, link_text, tuple(tags_to_apply))

                    current_index = self.chat_display.index(tk.INSERT)

                else:

                    self.chat_display.insert(current_index, link_text, base_tag)

                    current_index = self.chat_display.index(tk.INSERT)

            elif tag_name == 'br':

                self.chat_display.insert(current_index, "\n")

                current_index = self.chat_display.index(tk.INSERT)

            elif tag_name in ['ul', 'ol']:

                 for child in element.contents:

                      if child.name == 'li':

                           current_index = self._process_soup_element(child, current_index, base_tag=base_tag)

            elif tag_name == 'li':

                 list_marker = "- "

                 if element.parent and element.parent.name == 'ol':

                      list_marker = "1. "

                 self.chat_display.insert(current_index, list_marker, base_tag)

                 current_index = self.chat_display.index(tk.INSERT)

                 for child in element.contents:

                      current_index = self._process_soup_element(child, current_index, base_tag=base_tag)

                 self.chat_display.insert(current_index, "\n", base_tag)

                 current_index = self.chat_display.index(tk.INSERT)

            else:

                for child in element.contents:

                    current_index = self._process_soup_element(child, current_index, base_tag=base_tag)

            return current_index

        return current_index

    def open_link(self, event):

        index = self.chat_display.index(f"@{event.x},{event.y}")

        tags_at_click = self.chat_display.tag_names(index)

        clicked_url = None

        link_tag_name = None

        for tag in tags_at_click:

            if tag.startswith("link_"):

                link_tag_name = tag

                clicked_url = self.current_links.get(tag)

                break

        if clicked_url:

            if self.config["ui"].get("enable_animations", True) and link_tag_name:

                original_color = self.chat_display.tag_cget(link_tag_name, "foreground")

                self.chat_display.tag_config(link_tag_name, foreground=self.theme["accent"])

                self.root.update_idletasks()

                animation_delay = int(150 * (1.0 / self.config["ui"].get("animation_speed", 1.0)))

                self.root.after(animation_delay, lambda: self.chat_display.tag_config(link_tag_name, foreground=original_color))

            try:

                webbrowser.open(clicked_url)

                self.logger.info(f"Opened link: {clicked_url}")

                self.update_status(f"Opened link: {clicked_url}")

            except Exception as e:

                self.update_status(f"Failed to open link: {clicked_url}", level="error")

                self.logger.error(f"Failed to open link {clicked_url}: {e}")

    def add_to_chat(self, sender, message, newline=True):

        self.chat_display.config(state='normal')

        if self.chat_display.index("end-1c") != "1.0":

             last_char = self.chat_display.get("end-2c", "end-1c")

             if last_char != "\n":

                  self.chat_display.insert(tk.END, "\n")

        if sender == "user":

            prefix = "You: "

            tag = "user"

        elif sender == "assistant":

            prefix = f"{self.config.get('current_model', 'Assistant')}: "

            tag = "assistant"

        else:

            prefix = "System: "

            tag = "system"

        self.chat_display.insert(tk.END, prefix, tag)

        if message:

             if sender in ["user", "system"]:

                  self._process_text_with_links(message, tag)

             else:

                  pass

        if newline:

            self.chat_display.insert(tk.END, "\n")

        self.chat_display.config(state='disabled')

        self.chat_display.see(tk.END)

    def _process_text_with_links(self, text, base_tag):

        parts = re.split(r'(https?://[^\s]+)', text)

        for i, part in enumerate(parts):

            if i % 2 == 1:

                url = part

                tag_name = f"link_{len(self.current_links)}"

                self.current_links[tag_name] = url

                self.chat_display.insert(tk.END, url, (base_tag, "link", tag_name))

            else:

                self.chat_display.insert(tk.END, part, base_tag)

    def add_to_context(self, message):

        self.context.append(message)

        self.trim_context()

        self.update_context_indicator()

        self.logger.debug(f"Added message to context. Current context size (messages): {len(self.context)}")

    def trim_context(self):

        estimated_tokens_per_message = 500

        max_messages_by_tokens = self.context_limit // estimated_tokens_per_message if estimated_tokens_per_message > 0 else 100

        min_messages_to_keep = 10

        trim_limit_messages = max(min_messages_to_keep, max_messages_by_tokens)

        fixed_pre_prompt_count = 1 if self.pre_prompt and self.context and self.context and self.context[0].get("role") == "system" and self.context[0].get("content") == self.pre_prompt else 0

        while len(self.context) > fixed_pre_prompt_count + trim_limit_messages:

             self.context.pop(fixed_pre_prompt_count)

             self.logger.debug("Trimmed oldest message from context.")

        self._messages_trim_limit = trim_limit_messages + fixed_pre_prompt_count

    def update_context_indicator(self):

        current_messages = len(self.context)

        max_messages = self._messages_trim_limit if hasattr(self, '_messages_trim_limit') else 50

        if max_messages <= 0: max_messages = 1

        value = min(100, (current_messages / max_messages) * 100)

        self.context_indicator["value"] = value

    def update_status(self, message, level="info"):

        color = self.theme.get(level, self.theme["status"])

        self.status_label.config(text=message, fg=color)

    def update_system_monitor(self):

        if not _psutil_available:

            return

        try:

            cpu_percent = psutil.cpu_percent(interval=1)

            mem_info = psutil.virtual_memory()

            ram_percent = mem_info.percent

            monitor_text = f"CPU: {cpu_percent:.1f}% | RAM: {ram_percent:.1f}%"

            self.sys_monitor.config(text=monitor_text)

        except Exception as e:

            self.logger.warning(f"Failed to get system stats: {e}")

            self.sys_monitor.config(text="Sys Info Err")

        if self.root.winfo_exists():

            self.root.after(5000, self.update_system_monitor)

    def start_typing_animation(self):

        if not self.config["ui"].get("enable_animations", True):

             return

        if self.typing_animation_active:

            return

        self.typing_animation_active = True

        self.typing_animation_index = 0

        self._animate_typing()

    def _animate_typing(self):

        if not self.typing_animation_active or not self.root.winfo_exists():

            return

        base_text = "Generating response"

        dots = "." * (self.typing_animation_index % 4)

        self.status_label.config(text=f"{base_text}{dots}")

        self.typing_animation_index += 1

        animation_delay = int(200 * (1.0 / self.config["ui"].get("animation_speed", 1.0)))

        if animation_delay < 1: animation_delay = 1

        self.typing_animation_id = self.root.after(animation_delay, self._animate_typing)

    def stop_typing_animation(self):

        if not self.typing_animation_active:

            return

        self.typing_animation_active = False

        if self.typing_animation_id:

            self.root.after_cancel(self.typing_animation_id)

            self.typing_animation_id = None

    def stop_generation(self):

        if self.is_generating:

            self._stop_requested = True

            self.update_status("Stopping generation...")

            self.logger.info("Stop generation requested by user.")

        else:

            self.update_status("No generation in progress.")

    def toggle_voice_input(self):

        if not _speech_recognition_available or not self.config["voice_input"].get("enabled", True):

             self.update_status("Voice input is disabled or dependencies are missing.", level="error")

             self.logger.error("Voice input toggle failed: Service not available or disabled in config.")

             return

        if not self.recognizer or not self.microphone:

             self.update_status("Voice input not fully initialized. Check microphone access and PyAudio.", level="error")

             self.logger.error("Voice input toggle failed: Recognizer or microphone not initialized.")

             return

        if self.is_listening:

            self.is_listening = False

            self.update_status("Voice input off.")

            if self.stop_sound:

                 try: pygame.mixer.Sound.play(self.stop_sound)

                 except Exception as e: self.logger.error(f"Failed to play stop sound: {e}")

            self.logger.info("Voice input stopped by user.")

        else:

            self.is_listening = True

            self.update_status("Listening...")

            if self.listen_sound:

                 try: pygame.mixer.Sound.play(self.listen_sound)

                 except Exception as e: self.logger.error(f"Failed to play listen sound: {e}")

            self.logger.info("Voice input started.")

            threading.Thread(target=self._listen_in_background, daemon=True).start()

    def _listen_in_background(self):

        if not self.recognizer or not self.microphone or not self.is_listening:

             self.is_listening = False

             self.root.after(0, self.update_status, "Voice input stopped unexpectedly.", level="error")

             self.logger.error("Voice input background thread started but services not available.")

             if self.stop_sound: self.stop_sound.play()

             return

        try:

            with self.microphone as source:

                self.recognizer.dynamic_energy_threshold = True

                self.recognizer.pause_threshold = 0.8

                self.recognizer.non_speaking_duration = 0.5

                self.root.after(0, self.update_status, "Listening...")

                while self.is_listening:

                    try:

                        audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)

                        self.root.after(0, self.update_status, "Processing voice input...")

                        lang = self.config["voice_input"].get("language", "en-US")

                        text = self.recognizer.recognize_google(audio, language=lang)

                        self.logger.info(f"Voice recognized: {text}")

                        self.root.after(0, self.user_input.insert, tk.END, text + " ")

                        self.root.after(0, self.update_status, "Ready" if not self.is_generating else "Generating...")

                    except sr.WaitTimeoutError:

                        if self.is_listening:

                             self.root.after(0, self.update_status, "Listening...")

                        pass

                    except sr.UnknownValueError:

                        self.root.after(0, self.update_status, "Could not understand audio.", level="warning")

                        self.logger.warning("Speech Recognition could not understand audio")

                        if self.is_listening: self.root.after(0, self.update_status, "Listening...")

                    except sr.RequestError as e:

                        self.root.after(0, self.update_status, f"Speech Recognition service error: {e}", level="error")

                        self.logger.error(f"Speech Recognition service error: {e}")

                        self.is_listening = False

                    except Exception as e:

                        self.root.after(0, self.update_status, f"Voice input error: {e}", level="error")

                        self.logger.error(f"Unexpected voice input error: {e}")

                        self.is_listening = False

        except Exception as e:

             self.logger.error(f"Error in voice input setup or loop: {e}")

             self.root.after(0, self.update_status, "Voice input encountered a fatal error.", "error")

             self.is_listening = False

        finally:

             if self.stop_sound:

                  try: pygame.mixer.Sound.play(self.stop_sound)

                  except Exception: pass

             self.root.after(0, self.update_status, "Ready" if not self.is_generating else "Generating...", level="info")

             self.is_listening = False

    def new_chat(self):

        if self.is_generating:

             messagebox.showwarning("Warning", "Cannot start new chat while generating a response.")

             return

        if self.context and messagebox.askyesno("New Chat", "Start a new conversation? This will clear the current context."):

            self.clear_context(ask_confirm=False)

            self.chat_display.config(state='normal')

            self.chat_display.delete("1.0", tk.END)

            self.chat_display.config(state='disabled')

            self.current_response_buffer = ""

            self.current_links = {}

            self._assistant_response_start_index = None

            self.update_status("New chat started.")

            if self.config["ui"].get("enable_animations", True):

                 self.animate_welcome_message()

            else:

                 self.add_to_chat("system", f"New chat started.\n\nCurrent model: {self.config['current_model']}\nReady to assist you.")

            self.logger.info("New chat started.")

        elif not self.context:

            self.clear_context(ask_confirm=False)

            self.chat_display.config(state='normal')

            self.chat_display.delete("1.0", tk.END)

            self.chat_display.config(state='disabled')

            self.current_response_buffer = ""

            self.current_links = {}

            self._assistant_response_start_index = None

            self.update_status("New chat started.")

            if self.config["ui"].get("enable_animations", True):

                 self.animate_welcome_message()

            else:

                 self.add_to_chat("system", f"New chat started.\n\nCurrent model: {self.config['current_model']}\nReady to assist you.")

            self.logger.info("New chat started (context was already empty).")

    def save_chat(self):

        if not self.context:

            messagebox.showinfo("Save Chat", "No conversation to save.")

            return

        file_path = filedialog.asksaveasfilename(

            defaultextension=".json",

            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],

            title="Save Conversation"

        )

        if file_path:

            try:

                with open(file_path, 'w', encoding='utf-8') as f:

                    json.dump(self.context, f, indent=2, ensure_ascii=False)

                messagebox.showinfo("Save Chat", "Conversation saved successfully.")

                self.update_status(f"Conversation saved to {os.path.basename(file_path)}")

                self.logger.info(f"Conversation saved to {file_path}")

            except Exception as e:

                messagebox.showerror("Save Error", f"Failed to save conversation: {e}")

                self.logger.error(f"Failed to save conversation: {e}")

    def load_chat(self):

        if self.is_generating:

             messagebox.showwarning("Warning", "Cannot load chat while generating a response.")

             return

        if self.context and not messagebox.askyesno("Load Chat", "Load a new conversation? This will clear the current context."):

            return

        file_path = filedialog.askopenfilename(

            defaultextension=".json",

            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],

            title="Load Conversation"

        )

        if file_path:

            try:

                with open(file_path, 'r', encoding='utf-8') as f:

                    loaded_context = json.load(f)

                if isinstance(loaded_context, list) and all(isinstance(msg, dict) and "role" in msg and "content" in msg for msg in loaded_context):

                    self.context = loaded_context

                    self.chat_display.config(state='normal')

                    self.chat_display.delete("1.0", tk.END)

                    self.current_links = {}

                    self._assistant_response_start_index = None

                    self.update_status("Rendering loaded chat...")

                    start_index = 1 if self.pre_prompt and self.context and self.context[0].get("role") == "system" and self.context[0].get("content") == self.pre_prompt else 0

                    for message in self.context[start_index:]:

                         role = message.get("role", "system")

                         content = message.get("content", "")

                         if role == "assistant":

                              self.add_to_chat("assistant", "", newline=False)

                              insert_index = self.chat_display.index(tk.END)

                              self.render_markdown_response_at_index(content, insert_index)

                         else:

                              self.add_to_chat(role, content, newline=True)

                    self.chat_display.config(state='disabled')

                    self.update_context_indicator()

                    messagebox.showinfo("Load Chat", "Conversation loaded successfully.")

                    self.update_status(f"Conversation loaded from {os.path.basename(file_path)}")

                    self.logger.info(f"Conversation loaded from {file_path}")

                else:

                    messagebox.showerror("Load Error", "Invalid conversation file format.")

                    self.logger.error(f"Invalid conversation file format: {file_path}")

                    self.clear_context(ask_confirm=False)

            except FileNotFoundError:

                messagebox.showerror("Load Error", "File not found.")

            except json.JSONDecodeError:

                messagebox.showerror("Load Error", "Invalid JSON format.")

                self.logger.error(f"Invalid JSON format in file: {file_path}")

            except Exception as e:

                messagebox.showerror("Load Error", f"Failed to load conversation: {e}")

                self.logger.error(f"Failed to load conversation: {e}")

    def render_markdown_response_at_index(self, markdown_text, start_index):

        if not _markdown_available:

            self.chat_display.config(state='normal')

            self.chat_display.insert(start_index, markdown_text, "assistant")

            self.chat_display.config(state='disabled')

            self.chat_display.see(tk.END)

            return

        self.chat_display.config(state='normal')

        self.current_links = {}

        try:

            html_content = markdown.markdown(markdown_text, extensions=['fenced_code', 'nl2br', 'codehilite', 'extra'])

            soup = BeautifulSoup(html_content, 'html.parser')

            self._process_soup_element(soup.body, start_index, base_tag="assistant")

        except Exception as e:

            self.logger.error(f"Failed to render loaded markdown: {e}")

            self.chat_display.insert(start_index, markdown_text, "assistant")

    def _process_soup_element(self, element, current_index, base_tag="assistant"):

        if not element:

            return current_index

        if isinstance(element, str):

            self.chat_display.insert(current_index, element, base_tag)

            return self.chat_display.index(tk.INSERT)

        if element.name:

            tag_name = element.name.lower()

            if tag_name in ['p', 'div', 'blockquote', 'ul', 'ol', 'li', 'pre', 'code', 'h1', 'h2', 'h3', 'hr']:

                try:

                    prev_char_index = self.chat_display.index(f"{current_index} -1c")

                    prev_char = self.chat_display.get(prev_char_index)

                    if current_index != '1.0' and prev_char != '\n':

                        self.chat_display.insert(current_index, "\n")

                        current_index = self.chat_display.index(tk.INSERT)

                except tk.TclError:

                    pass

                tags_to_apply = [base_tag]

                if tag_name == 'blockquote':

                    tags_to_apply.append('quote')

                elif tag_name.startswith('h') and len(tag_name) == 2 and tag_name[1].isdigit():

                    tags_to_apply.append(tag_name)

                elif tag_name == 'pre':

                    tags_to_apply.append('code')

                for child in element.contents:

                    current_index = self._process_soup_element(child, current_index, base_tag=tuple(tags_to_apply) if len(tags_to_apply) > 1 else base_tag)

                if tag_name not in ['pre', 'code', 'hr']:

                    self.chat_display.insert(current_index, "\n")

                    current_index = self.chat_display.index(tk.INSERT)

                elif tag_name == 'hr':

                     self.chat_display.insert(current_index, "\n" + "-"*20 + "\n", "system")

                     current_index = self.chat_display.index(tk.INSERT)

            elif tag_name in ['strong', 'b']:

                tags_to_apply = list(base_tag if isinstance(base_tag, tuple) else [base_tag]) + ['bold']

                for child in element.contents:

                    current_index = self._process_soup_element(child, current_index, base_tag=tuple(tags_to_apply))

            elif tag_name in ['em', 'i']:

                tags_to_apply = list(base_tag if isinstance(base_tag, tuple) else [base_tag]) + ['italic']

                for child in element.contents:

                    current_index = self._process_soup_element(child, current_index, base_tag=tuple(tags_to_apply))

            elif tag_name == 'code':

                 if element.parent and element.parent.name != 'pre':

                    tags_to_apply = list(base_tag if isinstance(base_tag, tuple) else [base_tag]) + ['inline-code']

                    for child in element.contents:

                        self.chat_display.insert(current_index, str(child), tuple(tags_to_apply))

                        current_index = self.chat_display.index(tk.INSERT)

                 else:

                      for child in element.contents:

                           current_index = self._process_soup_element(child, current_index, base_tag=base_tag)

            elif tag_name == 'a':

                url = element.get('href', '')

                link_text = "".join(child.get_text() if child.name else str(child) for child in element.contents)

                if not link_text: link_text = url

                if url:

                    tag_name = f"link_{len(self.current_links)}"

                    self.current_links[tag_name] = url

                    tags_to_apply = list(base_tag if isinstance(base_tag, tuple) else [base_tag]) + ["link", tag_name]

                    self.chat_display.insert(current_index, link_text, tuple(tags_to_apply))

                    current_index = self.chat_display.index(tk.INSERT)

                else:

                    self.chat_display.insert(current_index, link_text, base_tag)

                    current_index = self.chat_display.index(tk.INSERT)

            elif tag_name == 'br':

                self.chat_display.insert(current_index, "\n")

                current_index = self.chat_display.index(tk.INSERT)

            elif tag_name in ['ul', 'ol']:

                 for child in element.contents:

                      if child.name == 'li':

                           current_index = self._process_soup_element(child, current_index, base_tag=base_tag)

            elif tag_name == 'li':

                 list_marker = "- "

                 if element.parent and element.parent.name == 'ol':

                      list_marker = "1. "

                 self.chat_display.insert(current_index, list_marker, base_tag)

                 current_index = self.chat_display.index(tk.INSERT)

                 for child in element.contents:

                      current_index = self._process_soup_element(child, current_index, base_tag=base_tag)

                 self.chat_display.insert(current_index, "\n", base_tag)

                 current_index = self.chat_display.index(tk.INSERT)

            else:

                for child in element.contents:

                    current_index = self._process_soup_element(child, current_index, base_tag=base_tag)

            return current_index

        return current_index

    def open_link(self, event):

        index = self.chat_display.index(f"@{event.x},{event.y}")

        tags_at_click = self.chat_display.tag_names(index)

        clicked_url = None

        link_tag_name = None

        for tag in tags_at_click:

            if tag.startswith("link_"):

                link_tag_name = tag

                clicked_url = self.current_links.get(tag)

                break

        if clicked_url:

            if self.config["ui"].get("enable_animations", True) and link_tag_name:

                original_color = self.chat_display.tag_cget(link_tag_name, "foreground")

                self.chat_display.tag_config(link_tag_name, foreground=self.theme["accent"])

                self.root.update_idletasks()

                animation_delay = int(150 * (1.0 / self.config["ui"].get("animation_speed", 1.0)))

                self.root.after(animation_delay, lambda: self.chat_display.tag_config(link_tag_name, foreground=original_color))

            try:

                webbrowser.open(clicked_url)

                self.logger.info(f"Opened link: {clicked_url}")

                self.update_status(f"Opened link: {clicked_url}")

            except Exception as e:

                self.update_status(f"Failed to open link: {clicked_url}", level="error")

                self.logger.error(f"Failed to open link {clicked_url}: {e}")

    def show_docs(self):

        messagebox.showinfo("Documentation", "Documentation not available yet.")

        self.logger.info("Show documentation (placeholder).")

    def show_api_reference(self):

        try:

            webbrowser.open("https://github.com/ollama/ollama/blob/main/docs/api.md")

            self.update_status("Opening Ollama API documentation.")

            self.logger.info("Opening Ollama API documentation.")

        except Exception as e:

            self.update_status("Failed to open API documentation.", level="error")

            self.logger.error(f"Failed to open API documentation: {e}")

    def show_model_info(self):

        model_name = self.config["current_model"]

        model_info = self.config["models"].get(model_name, {})

        description = model_info.get("description", "No description available.")

        context_window = model_info.get("context_window", "N/A")

        temperature = model_info.get("temperature", "N/A")

        max_tokens = model_info.get("max_tokens", "N/A")

        pre_prompt = model_info.get("pre_prompt", "N/A")

        info_text = f"Model: {model_name}\n\nDescription: {description}\n\nContext Window: {context_window} tokens (approximate)\nTemperature: {temperature}\nMax Tokens (Generate): {max_tokens}\n\nPre-prompt:\n{pre_prompt}"

        messagebox.showinfo(f"Model Info: {model_name}", info_text)

        self.logger.info(f"Showing info for model: {model_name}")

    def show_about(self):

        about_text = "AI Coder Ultimate ∞\n\nVersion: 1.0\nCreated by [Your Name/Alias]\n\nThis is a conversational AI coding assistant powered by Ollama.\n\nDependencies: "

        deps = []

        if _requests_available: deps.append("requests")

        if _speech_recognition_available: deps.append("speech_recognition")

        if _pygame_available: deps.append("pygame")

        if _psutil_available: deps.append("psutil")

        if _web_parsing_available: deps.append("beautifulsoup4, html2text")

        if _markdown_available: deps.append("markdown")

        deps.append("tkinter, threading, json, os, datetime, webbrowser, platform, queue, logging, re")

        about_text += ", ".join(deps)

        messagebox.showinfo("About AI Coder Ultimate", about_text)

        self.logger.info("Showing about information.")

    def start_background_tasks(self):

        self.process_response_queue()

if __name__ == "__main__":

    required_libs_flags = {

        'requests': _requests_available,

        'beautifulsoup4': _web_parsing_available,

        'html2text': _web_parsing_available,

        'markdown': _markdown_available

    }

    missing_libs_list = []

    for lib_name, is_available in required_libs_flags.items():

        if not is_available:

            if lib_name == 'beautifulsoup4' and 'beautifulsoup4 (and html2text)' not in missing_libs_list:

                 missing_libs_list.append('beautifulsoup4 (and html2text)')

            elif lib_name == 'html2text':

                 pass

            else:

                 missing_libs_list.append(lib_name)

    if missing_libs_list:

        print(f"Error: Missing required libraries: {', '.join(missing_libs_list)}")

        print("Please install them using: pip install requests beautifulsoup4 html2text markdown psutil pygame SpeechRecognition --break-system-packages")

        exit()

    root = tk.Tk()

    app = AICoderUltimate(root)

    root.mainloop()