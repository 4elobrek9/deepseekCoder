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
