import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox, filedialog
import threading
import time
import json
import os
from datetime import datetime
import speech_recognition as sr
import pygame
import requests
from PIL import Image, ImageTk
import queue

class OllamaChatInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Coder Pro - Ollama")
        self.root.geometry("1200x800")
        self.root.configure(bg="#1e1e2e")
        
        # Configuration
        self.config_file = "ollama_config.json"
        self.load_config()
        
        # Context management
        self.context = []
        self.context_limit = self.config["models"][self.config["current_model"]]["context_window"]
        self.pre_prompt = self.config["models"][self.config["current_model"]]["pre_prompt"]
        
        # Audio
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_listening = False
        pygame.mixer.init()
        
        # Response queue for streaming
        self.response_queue = queue.Queue()
        
        # UI Setup
        self.setup_ui()
        self.setup_menu()
        
        # Animation
        self.typing_animation_active = False
        self.typing_animation_index = 0
        self.animate_interface()
        
        # Start response handler
        self.root.after(100, self.process_response_queue)

    def load_config(self):
        """Load or create configuration"""
        default_config = {
            "current_model": "deepseek-coder",
            "ollama_host": "http://localhost:11434",
            "models": {
                "deepseek-coder": {
                    "pre_prompt": "You are an expert coding assistant. Provide clean, efficient code with explanations. Ask clarifying questions when needed.",
                    "context_window": 3900,
                    "temperature": 0.7
                },
                "llama3": {
                    "pre_prompt": "You are a helpful AI assistant. Provide detailed, thoughtful responses.",
                    "context_window": 8000,
                    "temperature": 0.7
                }
            }
        }
        
        try:
            with open(self.config_file, "r") as f:
                self.config = json.load(f)
        except:
            self.config = default_config
            self.save_config()

    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=2)

    def setup_ui(self):
        """Set up the main user interface"""
        # Main container
        main_frame = tk.Frame(self.root, bg="#1e1e2e")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        header_frame = tk.Frame(main_frame, bg="#1e1e2e")
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Model selection
        self.model_var = tk.StringVar(value=self.config["current_model"])
        model_dropdown = ttk.Combobox(
            header_frame,
            textvariable=self.model_var,
            values=list(self.config["models"].keys()),
            state="readonly",
            width=20
        )
        model_dropdown.pack(side=tk.LEFT, padx=5)
        model_dropdown.bind("<<ComboboxSelected>>", self.change_model)
        
        # Title
        self.title_label = tk.Label(
            header_frame,
            text=f"AI Coder Pro - {self.config['current_model']}",
            font=("Helvetica", 16, "bold"),
            fg="#89b4fa",
            bg="#1e1e2e"
        )
        self.title_label.pack(side=tk.LEFT, expand=True)
        
        # Context indicator
        self.context_indicator = ttk.Progressbar(
            header_frame,
            orient=tk.HORIZONTAL,
            length=200,
            mode='determinate'
        )
        self.context_indicator.pack(side=tk.RIGHT, padx=10)
        self.update_context_indicator()
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            font=("Consolas", 12),
            bg="#313244",
            fg="#cdd6f4",
            insertbackground="#cdd6f4",
            padx=15,
            pady=15,
            state='disabled'
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags
        self.chat_display.tag_config("user", foreground="#94e2d5")
        self.chat_display.tag_config("assistant", foreground="#89b4fa")
        self.chat_display.tag_config("system", foreground="#f38ba8")
        self.chat_display.tag_config("code", background="#45475a", relief=tk.RIDGE, borderwidth=2)
        
        # Input area
        input_frame = tk.Frame(main_frame, bg="#1e1e2e")
        input_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.user_input = tk.Text(
            input_frame,
            height=4,
            font=("Consolas", 12),
            bg="#313244",
            fg="#cdd6f4",
            insertbackground="#cdd6f4",
            wrap=tk.WORD
        )
        self.user_input.pack(fill=tk.X, expand=True, side=tk.LEFT)
        self.user_input.bind("<Return>", self.send_message_event)
        self.user_input.bind("<Shift-Return>", lambda e: self.user_input.insert(tk.INSERT, "\n"))
        
        # Button frame
        button_frame = tk.Frame(input_frame, bg="#1e1e2e")
        button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        # Buttons
        buttons = [
            ("Send", self.send_message, "#74c7ec"),
            ("Voice", self.toggle_voice_input, "#f38ba8"),
            ("Clear", self.clear_context, "#a6e3a1"),
            ("Stop", self.stop_generation, "#f9e2af")
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(
                button_frame,
                text=text,
                command=command,
                bg="#585b70",
                fg="#cdd6f4",
                activebackground="#6c7086",
                activeforeground="#cdd6f4",
                relief=tk.FLAT,
                highlightbackground=color,
                highlightcolor=color,
                highlightthickness=2
            )
            btn.pack(fill=tk.X, pady=2)
        
        # Status bar
        self.status_bar = tk.Label(
            main_frame,
            text="Ready",
            anchor=tk.W,
            font=("Helvetica", 10),
            fg="#a6adc8",
            bg="#1e1e2e"
        )
        self.status_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Initial message
        self.add_to_chat("system", f"Connected to {self.config['current_model']}. How can I help you today?")

    def setup_menu(self):
        """Set up the menu bar"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Save Chat", command=self.save_chat)
        file_menu.add_command(label="Load Chat", command=self.load_chat)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Model Settings", command=self.show_model_settings)
        settings_menu.add_command(label="Ollama Host", command=self.change_ollama_host)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        
        self.root.config(menu=menubar)

    def change_model(self, event):
        """Change the current model"""
        new_model = self.model_var.get()
        if new_model in self.config["models"]:
            self.config["current_model"] = new_model
            self.save_config()
            
            # Update context settings
            self.context_limit = self.config["models"][new_model]["context_window"]
            self.pre_prompt = self.config["models"][new_model]["pre_prompt"]
            
            # Update UI
            self.title_label.config(text=f"AI Coder Pro - {new_model}")
            self.clear_context()
            self.add_to_chat("system", f"Switched to {new_model} model. How can I help you?")
            self.update_context_indicator()

    def send_message_event(self, event):
        """Handle send message event"""
        if not event.state & 0x1:  # If Shift not pressed
            self.send_message()
            return "break"

    def send_message(self):
        """Send user message to Ollama"""
        message = self.user_input.get("1.0", tk.END).strip()
        if not message:
            return
            
        self.add_to_chat("user", message)
        self.user_input.delete("1.0", tk.END)
        self.add_to_context({"role": "user", "content": message})
        
        self.start_typing_animation()
        threading.Thread(target=self.generate_response, daemon=True).start()

    def generate_response(self):
        """Generate response from Ollama"""
        try:
            messages = [{"role": "system", "content": self.pre_prompt}] + self.context
            
            response = requests.post(
                f"{self.config['ollama_host']}/api/chat",
                json={
                    "model": self.config["current_model"],
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": self.config["models"][self.config["current_model"]]["temperature"]
                    }
                },
                stream=True
            )
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    if "message" in chunk:
                        content = chunk["message"]["content"]
                        full_response += content
                        self.response_queue.put(content)
                        
            self.response_queue.put(None)  # Signal end of response
            
        except Exception as e:
            self.response_queue.put(f"Error: {str(e)}")
            self.response_queue.put(None)

    def process_response_queue(self):
        """Process response queue for streaming"""
        try:
            while True:
                content = self.response_queue.get_nowait()
                
                if content is None:
                    # End of response
                    self.stop_typing_animation()
                    self.add_to_context({"role": "assistant", "content": self.current_response})
                    self.current_response = ""
                elif content.startswith("Error:"):
                    # Error occurred
                    self.stop_typing_animation()
                    self.add_to_chat("system", content)
                else:
                    # Streaming content
                    if not hasattr(self, 'current_response'):
                        self.current_response = ""
                        self.add_to_chat("assistant", "", newline=False)
                    
                    self.current_response += content
                    self.append_to_last_message(content)
                    
        except queue.Empty:
            pass
        
        self.root.after(100, self.process_response_queue)

    def stop_generation(self):
        """Stop the current generation"""
        # In a real implementation, you would cancel the request
        self.stop_typing_animation()
        self.add_to_chat("system", "Generation stopped by user")

    def add_to_chat(self, sender, message, newline=True):
        """Add message to chat display"""
        self.chat_display.config(state='normal')
        
        # Insert sender tag
        if sender == "user":
            self.chat_display.insert(tk.END, "You: ", "user")
        elif sender == "assistant":
            self.chat_display.insert(tk.END, "AI: ", "assistant")
        else:
            self.chat_display.insert(tk.END, "System: ", "system")
        
        # Process message for code blocks
        if "```" in message:
            parts = message.split("```")
            for i, part in enumerate(parts):
                if i % 2 == 1:  # Code block
                    self.chat_display.insert(tk.END, part + "\n", "code")
                else:  # Regular text
                    self.chat_display.insert(tk.END, part)
        else:
            self.chat_display.insert(tk.END, message)
        
        if newline:
            self.chat_display.insert(tk.END, "\n\n")
        
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)

    def append_to_last_message(self, content):
        """Append content to the last message"""
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, content)
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)

    def add_to_context(self, message):
        """Add message to context, managing the token limit"""
        self.context.append(message)
        
        # Calculate current context size (simplified)
        current_size = sum(len(msg["content"]) for msg in self.context) + len(self.pre_prompt)
        
        # Remove oldest messages if over limit
        while current_size > self.context_limit and len(self.context) > 1:
            removed = self.context.pop(0)
            current_size -= len(removed["content"])
        
        self.update_context_indicator()

    def update_context_indicator(self):
        """Update the context size indicator"""
        current_size = sum(len(msg["content"]) for msg in self.context) + len(self.pre_prompt)
        percent = (current_size / self.context_limit) * 100
        self.context_indicator["value"] = percent
        
        # Change color based on how full it is
        if percent > 90:
            self.context_indicator.configure(style="red.Horizontal.TProgressbar")
        elif percent > 70:
            self.context_indicator.configure(style="yellow.Horizontal.TProgressbar")
        else:
            self.context_indicator.configure(style="green.Horizontal.TProgressbar")

    def clear_context(self):
        """Clear the conversation context"""
        if messagebox.askyesno("Clear Context", "Are you sure you want to clear the conversation context?"):
            self.context = []
            self.chat_display.config(state='normal')
            self.chat_display.delete("1.0", tk.END)
            self.chat_display.config(state='disabled')
            self.add_to_chat("system", f"Context cleared. Ready to chat with {self.config['current_model']}.")
            self.update_context_indicator()

    def toggle_voice_input(self):
        """Toggle voice input mode"""
        if self.is_listening:
            self.stop_voice_input()
        else:
            self.start_voice_input()

    def start_voice_input(self):
        """Start listening for voice input"""
        self.is_listening = True
        self.update_status("Listening... Speak now")
        
        threading.Thread(target=self.process_voice_input, daemon=True).start()

    def stop_voice_input(self):
        """Stop voice input"""
        self.is_listening = False
        self.update_status("Voice input stopped")

    def process_voice_input(self):
        """Process voice input"""
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source, timeout=5)
            
            text = self.recognizer.recognize_google(audio)
            self.user_input.insert(tk.END, text)
            self.update_status("Voice input processed")
        except Exception as e:
            self.update_status(f"Voice error: {str(e)}")
        finally:
            self.stop_voice_input()

    def start_typing_animation(self):
        """Start typing animation"""
        self.typing_animation_active = True
        self.typing_animation_text = f"{self.config['current_model']} is typing"
        self.typing_animation_index = 0

    def stop_typing_animation(self):
        """Stop typing animation"""
        self.typing_animation_active = False
        self.update_status("Ready")

    def animate_interface(self):
        """Animate interface elements"""
        if self.typing_animation_active:
            dots = "." * (self.typing_animation_index % 4)
            self.status_bar.config(text=f"{self.typing_animation_text}{dots}")
            self.typing_animation_index += 1
        
        self.root.after(500, self.animate_interface)

    def update_status(self, message):
        """Update status bar"""
        self.status_bar.config(text=message)

    def save_chat(self):
        """Save chat history to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if filename:
            try:
                chat_data = {
                    "model": self.config["current_model"],
                    "timestamp": datetime.now().isoformat(),
                    "messages": self.context
                }
                
                with open(filename, "w") as f:
                    json.dump(chat_data, f, indent=2)
                
                self.update_status(f"Chat saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save chat: {str(e)}")

    def load_chat(self):
        """Load chat history from file"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if filename:
            try:
                with open(filename, "r") as f:
                    chat_data = json.load(f)
                
                if "messages" in chat_data:
                    self.clear_context()
                    self.context = chat_data["messages"]
                    
                    # Replay messages
                    self.chat_display.config(state='normal')
                    self.chat_display.delete("1.0", tk.END)
                    
                    for msg in self.context:
                        self.add_to_chat(msg["role"], msg["content"])
                    
                    self.update_status(f"Chat loaded from {filename}")
                    self.update_context_indicator()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load chat: {str(e)}")

    def show_model_settings(self):
        """Show model settings editor"""
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Model Settings")
        settings_win.geometry("800x600")
        
        editor = scrolledtext.ScrolledText(
            settings_win,
            wrap=tk.WORD,
            font=("Consolas", 10),
            width=80,
            height=30
        )
        editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        editor.insert(tk.END, json.dumps(self.config["models"], indent=2))
        
        def save_settings():
            try:
                new_models = json.loads(editor.get("1.0", tk.END))
                self.config["models"] = new_models
                self.save_config()
                messagebox.showinfo("Success", "Model settings updated")
                settings_win.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Invalid settings: {str(e)}")
        
        tk.Button(
            settings_win,
            text="Save",
            command=save_settings
        ).pack(side=tk.RIGHT, padx=10, pady=10)

    def change_ollama_host(self):
        """Change Ollama host address"""
        new_host = simpledialog.askstring(
            "Ollama Host",
            "Enter Ollama server URL:",
            initialvalue=self.config["ollama_host"]
        )
        
        if new_host:
            self.config["ollama_host"] = new_host
            self.save_config()
            self.update_status(f"Ollama host updated to {new_host}")

def main():
    root = tk.Tk()
    
    # Configure styles
    style = ttk.Style()
    style.theme_use('clam')
    
    # Progress bar styles
    style.configure("green.Horizontal.TProgressbar", troughcolor="#1e1e2e", background="#a6e3a1")
    style.configure("yellow.Horizontal.TProgressbar", troughcolor="#1e1e2e", background="#f9e2af")
    style.configure("red.Horizontal.TProgressbar", troughcolor="#1e1e2e", background="#f38ba8")
    
    app = OllamaChatInterface(root)
    root.mainloop()

if __name__ == "__main__":
    main()