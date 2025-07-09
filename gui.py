import tkinter as tk
from tkinter import ttk, filedialog
import json
import os
import socket
import time
from module_loader import ModuleLoader
import threading
from PIL import Image, ImageTk

# Logging system with different verbosity levels
class LogLevel:
    NO_LOG = 0
    OUTPUT_TRIGGERS_ONLY = 1
    SHOW_MODE = 2
    VERBOSE = 3

class Logger:
    def __init__(self, log_callback=None, level=LogLevel.SHOW_MODE):
        self.log_callback = log_callback
        self.level = level
    
    def set_level(self, level):
        self.level = level
    
    def log(self, message, level=LogLevel.SHOW_MODE):
        """Log a message if the current level allows it"""
        if self.level >= level and self.log_callback:
            self.log_callback(message)
    
    def no_log(self, message):
        """Log only when level is VERBOSE"""
        self.log(message, LogLevel.VERBOSE)
    
    def output_trigger(self, message):
        """Log only when level is OUTPUT_TRIGGERS_ONLY or higher"""
        self.log(message, LogLevel.OUTPUT_TRIGGERS_ONLY)
    
    def show_mode(self, message):
        """Log only when level is SHOW_MODE or higher"""
        self.log(message, LogLevel.SHOW_MODE)
    
    def verbose(self, message):
        """Log only when level is VERBOSE"""
        self.log(message, LogLevel.VERBOSE)

# Import the OSC server manager
from modules.osc_input.osc_server_manager import osc_manager

# Update the OSC manager to use our logger
def update_osc_manager_logger(logger):
    """Update the OSC manager to use our logger"""
    osc_manager.log = logger.show_mode

# Configuration paths
CONFIG_PATH = "config/interactions/interactions.json"
APP_CONFIG_PATH = "config/config.json"

def get_local_ip():
    """Get the local network IP address"""
    try:
        # Create a socket to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

def load_app_config():
    """Load app-level configuration"""
    default_config = {
        "installation_name": "Default Installation",
        "theme": "dark",
        "version": "1.0.0",
        "master_volume": 100.0,
        "log_level": "Show Mode"
    }
    
    if os.path.exists(APP_CONFIG_PATH):
        try:
            with open(APP_CONFIG_PATH, "r") as f:
                config = json.load(f)
                # Ensure all default keys exist
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception:
            return default_config
    else:
        # Create default config file
        os.makedirs(os.path.dirname(APP_CONFIG_PATH), exist_ok=True)
        with open(APP_CONFIG_PATH, "w") as f:
            json.dump(default_config, f, indent=2)
        return default_config

def save_app_config(config):
    """Save app-level configuration"""
    os.makedirs(os.path.dirname(APP_CONFIG_PATH), exist_ok=True)
    with open(APP_CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

class EditableLabel:
    """A label that can be clicked to become an editable entry field"""
    def __init__(self, parent, text, font, command=None):
        self.parent = parent
        self.text = text
        self.font = font
        self.command = command
        self.is_editing = False
        
        # Create label
        self.label = tk.Label(parent, text=text, font=font, cursor="hand2")
        self.label.pack(side="left")
        self.label.bind("<Button-1>", self.start_edit)
        
        # Create entry (hidden initially)
        self.entry = tk.Entry(parent, font=font, relief="flat", bd=0)
        self.entry.bind("<Return>", self.finish_edit)
        self.entry.bind("<FocusOut>", self.finish_edit)
        self.entry.bind("<Escape>", self.cancel_edit)
    
    def start_edit(self, event=None):
        if not self.is_editing:
            self.is_editing = True
            self.entry.delete(0, tk.END)
            self.entry.insert(0, self.text)
            self.entry.select_range(0, tk.END)
            self.label.pack_forget()
            self.entry.pack(side="left")
            self.entry.focus()
    
    def finish_edit(self, event=None):
        if self.is_editing:
            new_text = self.entry.get().strip()
            if new_text:
                self.text = new_text
                self.label.config(text=new_text)
                if self.command:
                    self.command(new_text)
            self.cancel_edit()
    
    def cancel_edit(self, event=None):
        if self.is_editing:
            self.is_editing = False
            self.entry.pack_forget()
            self.label.pack(side="left")
    
    def update_text(self, new_text):
        self.text = new_text
        self.label.config(text=new_text)

class InteractionBlock:
    cursor_img = None  # Class-level cache for the cursor image

    def __init__(self, parent, loader, logger, on_change_callback, remove_callback, preset=None):
        self.parent = parent
        self.loader = loader
        self.logger = logger
        self.on_change_callback = on_change_callback
        self.remove_callback = remove_callback
        
        # Variables
        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.input_instance = None
        self.output_instance = None
        self.input_config_fields = {}
        self.output_config_fields = {}
        
        # Cursor animation
        self.cursor_running = True
        self.cursor_thread = threading.Thread(target=self._cursor_animation_loop, daemon=True)
        self.cursor_thread.start()
        
        # Build the GUI
        self.build_block()
        
        # Load preset if provided
        if preset:
            self.load_from_preset(preset)

    def is_valid(self):
        return bool(self.input_var.get() and self.output_var.get())

    def on_change(self):
        """Called when any field changes to trigger config save"""
        if self.on_change_callback:
            self.on_change_callback()

    def remove_self(self):
        self.cursor_running = False
        # Destroy the frame first
        if hasattr(self, 'frame'):
            self.frame.destroy()
        # Then call the remove callback
        self.remove_callback(self)

    def draw_waveform_on_canvas(self, file_path, canvas):
        img_path = f"{file_path}.waveform.png"
        if not os.path.isfile(img_path):
            canvas.delete("all")
            return
        try:
            image = Image.open(img_path)
        except Exception as e:
            self.logger.output_trigger(f"Waveform error: {e}")
            canvas.delete("all")
            return
        def update_canvas(event=None):
            width = canvas.winfo_width()
            height = canvas.winfo_height()
            if width > 0 and height > 0:
                resized_image = image.resize((width, height), Image.Resampling.LANCZOS)
                tk_image = ImageTk.PhotoImage(resized_image)
                canvas.delete("all")
                canvas.create_image(0, 0, anchor="nw", image=tk_image)
                canvas.image = tk_image  # Prevent garbage collection
        canvas.bind("<Configure>", update_canvas)
        canvas.update_idletasks()
        update_canvas()

    def _cursor_animation_loop(self):
        # Load the cursor image once
        if InteractionBlock.cursor_img is None:
            cursor_path = os.path.join(os.path.dirname(__file__), "modules", "audio_output", "cursor.png")
            try:
                img = Image.open(cursor_path)
                InteractionBlock.cursor_img = ImageTk.PhotoImage(img)
            except Exception as e:
                self.logger.output_trigger(f"⚠️ Failed to load cursor image: {e}")
                InteractionBlock.cursor_img = None
        
        while self.cursor_running:
            try:
                waveform_data = self.output_config_fields.get("waveform")
                if waveform_data:
                    cursor_canvas = waveform_data["cursor"]
                    start_time = waveform_data.get("start_time")
                    duration = waveform_data.get("duration")
                    is_playing = waveform_data.get("is_playing", False)
                    if cursor_canvas and is_playing and start_time and duration:
                        elapsed = time.time() - start_time
                        if elapsed <= duration:
                            width = cursor_canvas.winfo_width()
                            height = cursor_canvas.winfo_height()
                            if width > 1 and height > 1 and InteractionBlock.cursor_img is not None:
                                x = int((elapsed / duration) * width)
                                cursor_canvas.delete("cursor")
                                
                                # Scale cursor image to match canvas height
                                cursor_path = os.path.join(os.path.dirname(__file__), "modules", "audio_output", "cursor.png")
                                try:
                                    img = Image.open(cursor_path)
                                    # Resize to match canvas height, maintain aspect ratio
                                    img_resized = img.resize((int(img.width * height / img.height), height), Image.Resampling.LANCZOS)
                                    cursor_img_scaled = ImageTk.PhotoImage(img_resized)
                                    cursor_canvas.create_image(x, 0, anchor="nw", image=cursor_img_scaled, tags="cursor")
                                    # Keep a reference to prevent garbage collection
                                    cursor_canvas.cursor_img_ref = cursor_img_scaled
                                except Exception as e:
                                    # Fallback to original image if scaling fails
                                    cursor_canvas.create_image(x, 0, anchor="nw", image=InteractionBlock.cursor_img, tags="cursor")
                        else:
                            cursor_canvas.delete("cursor")
                            waveform_data["is_playing"] = False
                            waveform_data["start_time"] = None
                            waveform_data["duration"] = None
            except Exception as e:
                pass
            time.sleep(0.05)

    def build_block(self):
        self.frame = ttk.Frame(self.parent, style="Block.TFrame")
        self.frame.pack(fill="x", padx=10, pady=5)

        # Header with remove button
        header = ttk.Frame(self.frame, style="Block.TFrame")
        header.pack(fill="x", pady=(0, 10))
        
        ttk.Label(header, text="Interaction", font=("Inter", 12, "bold"), style="Header.TLabel").pack(side="left")
        ttk.Button(header, text="×", command=self.remove_self, style="Remove.TButton", width=3).pack(side="right")

        # Main content area - horizontal layout
        content_frame = ttk.Frame(self.frame, style="Block.TFrame")
        content_frame.pack(fill="x")

        # Input section (left)
        input_frame = ttk.LabelFrame(content_frame, text="Input", style="Section.TLabelframe")
        input_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        ttk.Label(input_frame, text="Module:", style="Label.TLabel").pack(anchor="w", padx=10, pady=(10, 5))
        input_combo = ttk.Combobox(input_frame, textvariable=self.input_var, state="readonly", style="Combo.TCombobox")
        input_combo.pack(fill="x", padx=10, pady=(0, 10))
        input_combo.bind("<<ComboboxSelected>>", self.draw_input_fields)

        # Populate input modules
        input_modules = [name for name, info in self.loader.module_registry.items() if info["manifest"]["type"] == "input"]
        input_combo["values"] = input_modules

        self.input_fields_container = ttk.Frame(input_frame, style="Fields.TFrame")
        self.input_fields_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Output section (middle)
        output_frame = ttk.LabelFrame(content_frame, text="Output", style="Section.TLabelframe")
        output_frame.pack(side="left", fill="both", expand=True, padx=5)

        ttk.Label(output_frame, text="Module:", style="Label.TLabel").pack(anchor="w", padx=10, pady=(10, 5))
        output_combo = ttk.Combobox(output_frame, textvariable=self.output_var, state="readonly", style="Combo.TCombobox")
        output_combo.pack(fill="x", padx=10, pady=(0, 10))
        output_combo.bind("<<ComboboxSelected>>", self.draw_output_fields)

        # Populate output modules
        output_modules = [name for name, info in self.loader.module_registry.items() if info["manifest"]["type"] == "output"]
        output_combo["values"] = output_modules

        self.output_fields_container = ttk.Frame(output_frame, style="Fields.TFrame")
        self.output_fields_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Control section (right)
        control_frame = ttk.LabelFrame(content_frame, text="Controls", style="Section.TLabelframe")
        control_frame.pack(side="left", fill="y", padx=(5, 0))

        # Trigger button
        ttk.Button(control_frame, text="▶ Trigger", command=self.trigger_output, 
                  style="Action.TButton").pack(padx=10, pady=(20, 10), fill="x")
        
        # Remove button (in control section)
        ttk.Button(control_frame, text="🗑 Remove", command=self.remove_self, 
                  style="Remove.TButton").pack(padx=10, pady=(0, 20), fill="x")

    def draw_input_fields(self, event=None, create_instance=True):
        for widget in self.input_fields_container.winfo_children():
            widget.destroy()

        module_name = self.input_var.get()
        if module_name not in self.loader.module_registry:
            self.logger.show_mode(f"⚠️ Invalid input module: '{module_name}'")
            return

        manifest = self.loader.module_registry[module_name]["manifest"]
        fields = manifest.get("fields", [])

        self.input_config_fields = {}
        for field in fields:
            if field["type"] == "button":
                action = field.get("action", field["name"])
                button = ttk.Button(self.input_fields_container, text=field["label"], 
                                  command=lambda name=action: self.handle_button_action(name), style="Action.TButton")
                button.pack(fill="x", pady=5, padx=5)
                continue

            label = ttk.Label(self.input_fields_container, text=field["label"], style="Label.TLabel")
            label.pack(anchor="w", padx=5, pady=(10, 5))
            entry = ttk.Entry(self.input_fields_container, style="Entry.TEntry")
            entry.insert(0, field.get("default", ""))
            entry.pack(fill="x", pady=(0, 10), padx=5)
            entry.bind("<KeyRelease>", lambda e: self.on_change())
            self.input_config_fields[field["name"]] = entry

        if create_instance:
            # Stop any existing input instance before creating a new one
            if self.input_instance and hasattr(self.input_instance, "stop"):
                self.logger.verbose("🛑 Stopping existing input instance...")
                self.input_instance.stop()
                
            # Create input instance
            try:
                self.input_instance = self.loader.create_instance(
                    module_name,
                    self.get_input_config(),
                    log_callback=self.logger.show_mode
                )
                self.connect_modules()
            except Exception as e:
                self.logger.show_mode(f"⚠️ Failed to create input instance: {e}")

    def draw_output_fields(self, event=None):
        for widget in self.output_fields_container.winfo_children():
            widget.destroy()

        module_name = self.output_var.get()
        if module_name not in self.loader.module_registry:
            self.logger.show_mode(f"⚠️ Invalid output module: '{module_name}'")
            return

        manifest = self.loader.module_registry[module_name]["manifest"]
        fields = manifest.get("fields", [])

        self.output_config_fields = {}
        for field in fields:
            if field["type"] == "button":
                action = field.get("action", field["name"])
                button = ttk.Button(self.output_fields_container, text=field["label"], 
                                  command=lambda name=action: self.handle_button_action(name), style="Action.TButton")
                button.pack(fill="x", pady=5, padx=5)
                continue

            if field["type"] == "waveform":
                label = ttk.Label(self.output_fields_container, text=field["label"], style="Label.TLabel")
                label.pack(anchor="w", padx=5, pady=(10, 5))

                # Create waveform container
                waveform_container = ttk.Frame(self.output_fields_container, style="Fields.TFrame")
                waveform_container.pack(fill="x", pady=(0, 10), padx=5)
                
                # Create canvas for waveform
                waveform_canvas = tk.Canvas(waveform_container, width=300, height=60, bg="#111", highlightthickness=0)
                waveform_canvas.pack(fill="x")
                
                # Create transparent cursor canvas that overlays the waveform
                cursor_canvas = tk.Canvas(waveform_container, width=300, height=60, highlightthickness=0)
                cursor_canvas.place(in_=waveform_container, x=0, y=0, relwidth=1, relheight=1)
                
                self.output_config_fields[field["name"]] = {
                    "waveform": waveform_canvas,
                    "cursor": cursor_canvas,
                    "container": waveform_container,
                    "start_time": None,
                    "duration": None,
                    "is_playing": False
                }
                continue

            if field["type"] == "slider":
                label = ttk.Label(self.output_fields_container, text=field["label"], style="Label.TLabel")
                label.pack(anchor="w", padx=5, pady=(10, 5))
                
                # Create slider frame
                slider_frame = ttk.Frame(self.output_fields_container, style="Fields.TFrame")
                slider_frame.pack(fill="x", pady=(0, 10), padx=5)
                
                slider_var = tk.DoubleVar(value=field.get("default", 50))
                slider = ttk.Scale(slider_frame, from_=field.get("min", 0), to=field.get("max", 100), 
                                 variable=slider_var, orient="horizontal", command=lambda v, f=field: self.on_slider_change(f, v))
                slider.pack(side="left", fill="x", expand=True)
                
                value_label = ttk.Label(slider_frame, text=f"{int(slider_var.get())}", style="Label.TLabel")
                value_label.pack(side="right", padx=(10, 0))
                
                self.output_config_fields[field["name"]] = {
                    "slider": slider,
                    "var": slider_var,
                    "label": value_label
                }
                continue

            label = ttk.Label(self.output_fields_container, text=field["label"], style="Label.TLabel")
            label.pack(anchor="w", padx=5, pady=(10, 5))
            entry = ttk.Entry(self.output_fields_container, style="Entry.TEntry")
            entry.insert(0, field.get("default", ""))
            entry.pack(fill="x", pady=(0, 10), padx=5)

            # Trigger GUI save + waveform refresh on change
            entry.bind("<KeyRelease>", lambda e: (self.on_change(), self.refresh_output_module_and_waveform()))
            self.output_config_fields[field["name"]] = entry

            if field["name"] == "file_path":
                entry.bind("<Double-Button-1>", lambda e, ent=entry: self.browse_file(ent))
                # Also trigger waveform generation when the file path changes
                entry.bind("<KeyRelease>", lambda e: self.on_file_path_change())

        # Stop any existing output instance before creating a new one
        if self.output_instance and hasattr(self.output_instance, "stop"):
            self.logger.verbose("🛑 Stopping existing output instance...")
            self.output_instance.stop()
            
        # Create output instance
        try:
            self.output_instance = self.loader.create_instance(
                module_name,
                self.get_output_config(),
                log_callback=self.logger.output_trigger
            )
            
            # Set up cursor callback for audio output
            if hasattr(self.output_instance, 'set_cursor_callback'):
                self.output_instance.set_cursor_callback(self.start_audio_playback)
            
            self.connect_modules()
            
            # Refresh waveform on startup
            self.logger.verbose("✅ Refreshing waveform on startup...")
            self.refresh_output_module_and_waveform()
        except Exception as e:
            self.logger.show_mode(f"⚠️ Failed to create output instance: {e}")

    def refresh_output_module_and_waveform(self):
        """Restore waveform rendering and keep cursor animation."""
        self.logger.verbose(f"🔁 Refreshing waveform and canvas")
        module_name = self.output_var.get()
        config = self.get_output_config()
        try:
            # Create a temporary instance just for waveform generation, don't start it
            instance = self.loader.create_instance(module_name, config, log_callback=self.logger.verbose)
            if hasattr(instance, "get_waveform_image_path"):
                # Try to generate waveform if it doesn't exist
                if hasattr(instance, "generate_waveform"):
                    file_path = config.get("file_path", "")
                    if file_path:
                        instance.generate_waveform(file_path)
                        img_path = instance.get_waveform_image_path()
                    else:
                        img_path = None
                else:
                    img_path = None
                if img_path and os.path.isfile(img_path):
                    try:
                        from PIL import Image, ImageTk
                        img = Image.open(img_path)
                        img = img.resize((300, 60))
                        photo = ImageTk.PhotoImage(img)
                        waveform_widget = self.output_config_fields.get("waveform")
                        if waveform_widget and isinstance(waveform_widget, dict) and "waveform" in waveform_widget:
                            waveform_canvas = waveform_widget["waveform"]
                            waveform_canvas.delete("all")
                            waveform_canvas.create_image(0, 0, anchor="nw", image=photo)
                            waveform_canvas.image = photo  # Keep a reference
                            waveform_canvas.configure(width=300, height=60)
                            self.logger.verbose(f"✅ Waveform image loaded and displayed on canvas")
                            
                            # Also update cursor canvas size to match
                            if "cursor" in waveform_widget:
                                cursor_canvas = waveform_widget["cursor"]
                                cursor_canvas.configure(width=300, height=60)
                            
                        else:
                            self.logger.verbose(f"⚠️ No waveform widget found in output config fields")
                    except ImportError as e:
                        self.logger.show_mode(f"⚠️ PIL not available: {e}")
                    except Exception as e:
                        self.logger.show_mode(f"⚠️ Failed to load waveform image: {e}")
                else:
                    self.logger.verbose(f"⚠️ Waveform file not found: {img_path}")
                    if img_path:
                        self.logger.verbose(f"💡 File exists: {os.path.exists(img_path)}")
            else:
                self.logger.verbose(f"⚠️ Module {module_name} doesn't have waveform support")
        except Exception as e:
            self.logger.show_mode(f"⚠️ Failed to refresh waveform: {e}")

    def browse_file(self, entry_widget):
        file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav *.mp3 *.ogg")])
        if file_path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, file_path)
            self.on_change()
            self.logger.show_mode(f"✅ File selected, refreshing waveform...")
            # Refresh waveform after file selection
            self.refresh_output_module_and_waveform()
            
    def on_file_path_change(self):
        """Called when the file path is changed manually"""
        self.on_change()
        self.logger.verbose(f"✅ File path changed, refreshing waveform...")
        # Refresh waveform after manual path change
        self.refresh_output_module_and_waveform()

    def trigger_output(self):
        output_module = self.output_var.get()
        if not output_module:
            self.logger.show_mode("⚠️ No output module selected")
            return

        try:
            instance = self.loader.create_instance(output_module, self.get_output_config(), log_callback=self.logger.output_trigger)
            
            # Set cursor callback on the instance
            if hasattr(instance, "set_cursor_callback"):
                self.logger.verbose(f"🎵 Setting cursor callback on manual trigger instance")
                instance.set_cursor_callback(self.start_audio_playback)
            
            instance.start()
            instance.handle_event({})
        except Exception as e:
            self.logger.show_mode(f"💥 Failed to trigger output: {e}")

    def handle_button_action(self, name):
        self.logger.output_trigger(f"🔘 Button action triggered: {name}")
        
        # Update input instance config before handling button action
        if self.input_instance and hasattr(self.input_instance, "update_config"):
            self.input_instance.update_config(self.get_input_config())
            
        if self.input_instance and hasattr(self.input_instance, "handle_button_action"):
            self.input_instance.handle_button_action(name)
            
        # Update output instance config before handling button action  
        if self.output_instance and hasattr(self.output_instance, "update_config"):
            self.output_instance.update_config(self.get_output_config())
            
        if self.output_instance and hasattr(self.output_instance, "handle_button_action"):
            self.output_instance.handle_button_action(name)

    def to_dict(self):
        return {
            "input": {
                "module": self.input_var.get(),
                "config": self.get_input_config()
            },
            "output": {
                "module": self.output_var.get(),
                "config": self.get_output_config()
            }
        }

    def load_from_preset(self, preset):
        input_module = preset.get("input", {}).get("module", "")
        output_module = preset.get("output", {}).get("module", "")

        self.input_var.set(input_module)
        self.output_var.set(output_module)

        if input_module in self.loader.module_registry:
            # First populate the GUI fields with saved values (don't create instance yet)
            self.draw_input_fields(create_instance=False)
            for k, v in preset["input"].get("config", {}).items():
                if k in self.input_config_fields:
                    self.input_config_fields[k].delete(0, tk.END)
                    self.input_config_fields[k].insert(0, v)
            
            # Now create instance with the populated config values
            self.input_instance = self.loader.create_instance(
                input_module,
                self.get_input_config(),
                log_callback=self.logger.show_mode
            )
            if self.input_instance:
                self.input_instance.start()
        else:
            self.logger.output_trigger(f"⚠️ Invalid input module: '{input_module}'")

        if output_module in self.loader.module_registry:
            self.draw_output_fields()
            for k, v in preset["output"].get("config", {}).items():
                if k in self.output_config_fields:
                    field = self.output_config_fields[k]
                    if isinstance(field, tk.Entry):
                        # Handle Entry widgets (like file_path)
                        field.delete(0, tk.END)
                        field.insert(0, v)
                    elif isinstance(field, dict) and "var" in field:
                        # Handle sliders
                        field["var"].set(v)
                    elif isinstance(field, dict) and "waveform" in field:
                        # Handle waveform fields (no value to set)
                        pass
                    else:
                        # Handle other field types
                        self.logger.output_trigger(f"⚠️ Unknown field type for {k}: {type(field)}")
            
            self.output_instance = self.loader.create_instance(
                output_module,
                self.get_output_config(),
                log_callback=self.logger.output_trigger
            )
            
            # Set up cursor callback for audio output
            if hasattr(self.output_instance, 'set_cursor_callback'):
                self.output_instance.set_cursor_callback(self.start_audio_playback)
            
            # Connection is handled by draw_output_fields() via connect_modules()
            
            # Refresh waveform on startup
            self.logger.verbose("✅ Refreshing waveform on startup...")
            self.refresh_output_module_and_waveform()
        else:
            self.logger.output_trigger(f"⚠️ Invalid output module: '{output_module}'")
    
    def get_input_config(self):
        return {k: v.get() for k, v in self.input_config_fields.items() if isinstance(v, tk.Entry)}

    def get_output_config(self):
        config = {}
        for k, v in self.output_config_fields.items():
            if k == "waveform":
                continue  # Don't save waveform field!
            if isinstance(v, tk.Entry):
                config[k] = v.get()
            elif isinstance(v, dict) and "var" in v:
                # Handle sliders
                config[k] = v["var"].get()
            else:
                # Handle other field types
                config[k] = v
        self.logger.show_mode(f"�� Debug - get_output_config() returning: {config}")
        return config
        
    def connect_modules(self):
        """Connect input and output modules if both exist"""
        if self.input_instance and self.output_instance:
            # Create a dynamic callback that always uses current config
            def dynamic_event_callback(data):
                # Get current config from GUI
                current_config = self.get_output_config()
                self.logger.output_trigger(f"🔗 OSC event received, using current config: {current_config}")
                
                # Update output instance with current config
                if self.output_instance and hasattr(self.output_instance, "update_config"):
                    self.output_instance.update_config(current_config)
                
                # Ensure cursor callback is set on the output instance
                if self.output_instance and hasattr(self.output_instance, "set_cursor_callback"):
                    self.logger.verbose(f"🎵 Setting cursor callback on output instance")
                    self.output_instance.set_cursor_callback(self.start_audio_playback)
                else:
                    self.logger.verbose(f"⚠️ Output instance or set_cursor_callback not available")
                    
                # Also ensure the output instance is started
                if self.output_instance and hasattr(self.output_instance, "start"):
                    self.output_instance.start()
                    
                # Call the output instance's handle_event
                if self.output_instance:
                    self.output_instance.handle_event(data)
            
            self.input_instance.set_event_callback(dynamic_event_callback)
            self.logger.show_mode("🔗 Connected input to output with dynamic config")

    def on_slider_change(self, field, value):
        """Called when a slider value changes"""
        volume = float(value)
        
        # Update the label
        if field["name"] in self.output_config_fields:
            self.output_config_fields[field["name"]]["label"].config(text=f"{int(volume)}")
        
        # Update the output instance if it exists
        if self.output_instance and hasattr(self.output_instance, 'set_volume'):
            # Set individual volume (0.0 to 1.0)
            self.output_instance.set_volume(volume / 100.0)
        
        self.on_change()

    def start_audio_playback(self, duration):
        """Start audio playback tracking for cursor"""
        if "waveform" in self.output_config_fields:
            waveform_data = self.output_config_fields["waveform"]
            waveform_data["start_time"] = time.time()
            waveform_data["duration"] = duration
            waveform_data["is_playing"] = True
            self.logger.output_trigger(f"🎵 Started cursor animation: duration={duration:.2f}s at {time.strftime('%H:%M:%S')}")
        else:
            self.logger.verbose(f"⚠️ No waveform field found for cursor animation")

    def update_waveform_cursor(self, position):
        """Legacy method - now handled by cursor thread"""
        pass  # Cursor animation is now handled by the thread

class InteractionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Interaction App")
        
        # Load app config
        self.app_config = load_app_config()
        
        # Setup modern styling
        self.setup_styles()
        
        # Build the GUI first (creates log_text widget)
        self.build_gui()
        
        # Initialize logger after GUI is built
        self.log_level = LogLevel.SHOW_MODE
        self.logger = Logger(self._write_to_log, self.log_level)
        
        # Load log level from config and set the combobox
        saved_log_level = self.app_config.get("log_level", "Show Mode")
        self.log_level_var.set(saved_log_level)
        
        # Apply the loaded log level
        self._apply_log_level(saved_log_level)
        
        # Update OSC manager to use our logger
        update_osc_manager_logger(self.logger)
        
        self.loader = ModuleLoader()
        self.loader.discover_modules(log_callback=self.logger.show_mode)

        self.blocks = []
        self.installation_label = None

        self.load_config()

    def _write_to_log(self, msg):
        """Internal method to write to the log text widget"""
        self.log_text.insert(tk.END, f"{msg}\n")
        self.log_text.see(tk.END)
        # Limit log entries to prevent memory issues
        if int(self.log_text.index('end-1c').split('.')[0]) > 1000:
            self.log_text.delete('1.0', '500.0')

    def log(self, msg, level=LogLevel.SHOW_MODE):
        """Log a message with the specified level"""
        self.logger.log(msg, level)

    def setup_styles(self):
        """Setup modern black and white styling"""
        style = ttk.Style()
        
        # Configure the root window
        self.root.configure(bg='#1a1a1a')
        
        # Modern color scheme
        style.theme_use('clam')
        
        # Configure styles
        style.configure('Main.TFrame', background='#1a1a1a')
        style.configure('Header.TFrame', background='#2a2a2a')
        style.configure('Block.TFrame', background='#2a2a2a', relief='flat')
        style.configure('Section.TLabelframe', background='#2a2a2a', foreground='white', relief='solid', borderwidth=1)
        style.configure('Section.TLabelframe.Label', background='#2a2a2a', foreground='white', font=('Inter', 10, 'bold'))
        style.configure('Fields.TFrame', background='#2a2a2a')
        
        # Labels
        style.configure('Header.TLabel', background='#2a2a2a', foreground='white', font=('Inter', 14, 'bold'))
        style.configure('Label.TLabel', background='#2a2a2a', foreground='#e0e0e0', font=('Inter', 9))
        
        # Buttons
        style.configure('Add.TButton', background='#404040', foreground='white', font=('Inter', 10, 'bold'))
        style.configure('Remove.TButton', background='#d32f2f', foreground='white', font=('Inter', 9, 'bold'))
        style.configure('Action.TButton', background='#2196f3', foreground='white', font=('Inter', 9, 'bold'))
        
        # Entry fields
        style.configure('Entry.TEntry', fieldbackground='#404040', foreground='white', font=('Inter', 9))
        
        # Combobox
        style.configure('Combo.TCombobox', fieldbackground='#404040', foreground='white', font=('Inter', 9))
        style.map('Combo.TCombobox', fieldbackground=[('readonly', '#404040')])

    def build_gui(self):
        # Main container
        main_container = ttk.Frame(self.root, style="Main.TFrame")
        main_container.pack(fill="both", expand=True)

        # Header with installation name, IP, and master volume
        header = ttk.Frame(main_container, style="Header.TFrame")
        header.pack(fill="x", padx=20, pady=15)

        # Installation name (editable)
        self.installation_label = EditableLabel(
            header, 
            self.app_config.get("installation_name", "Default Installation"),
            ("Inter", 16, "bold"),
            self.on_installation_name_change
        )

        # Master volume control
        volume_frame = ttk.Frame(header, style="Header.TFrame")
        volume_frame.pack(side="right", padx=(0, 20))
        
        ttk.Label(volume_frame, text="Master Volume:", style="Header.TLabel").pack(side="left", padx=(0, 10))
        self.master_volume_var = tk.DoubleVar(value=self.app_config.get("master_volume", 100))
        master_volume_slider = ttk.Scale(volume_frame, from_=0, to=100, variable=self.master_volume_var, 
                                       orient="horizontal", length=150, command=self.on_master_volume_change)
        master_volume_slider.pack(side="left")
        
        volume_label = ttk.Label(volume_frame, text=f"{int(self.master_volume_var.get())}%", style="Header.TLabel")
        volume_label.pack(side="left", padx=(10, 0))
        self.master_volume_label = volume_label

        # IP address
        local_ip = get_local_ip()
        ttk.Label(header, text=f"IP: {local_ip}", style="Header.TLabel").pack(side="right")

        # Add interaction button
        ttk.Button(header, text="+ Add Interaction", command=self.add_block, style="Add.TButton").pack(side="right", padx=(0, 20))

        # Content area
        content_frame = ttk.Frame(main_container, style="Main.TFrame")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Canvas for scrollable content
        self.canvas = tk.Canvas(content_frame, bg='#1a1a1a', highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas, style="Main.TFrame")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Log area
        log_frame = ttk.Frame(main_container, style="Main.TFrame")
        log_frame.pack(fill="x", padx=20, pady=(0, 20))

        # Log level control
        log_control_frame = ttk.Frame(log_frame, style="Main.TFrame")
        log_control_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Label(log_control_frame, text="Log Level:", style="Label.TLabel").pack(side="left", padx=(0, 10))
        self.log_level_var = tk.StringVar(value="Show Mode")
        log_level_combo = ttk.Combobox(log_control_frame, textvariable=self.log_level_var, 
                                      values=["No Log", "Only Output Triggers", "Show Mode", "Verbose"], 
                                      state="readonly", width=20, style="Combo.TCombobox")
        log_level_combo.pack(side="left")
        log_level_combo.bind("<<ComboboxSelected>>", self.on_log_level_change)

        self.log_text = tk.Text(log_frame, height=8, bg="#2a2a2a", fg="#00ff00", 
                               font=("Consolas", 10), relief="flat", bd=0)
        self.log_text.pack(fill="both")

    def on_installation_name_change(self, new_name):
        """Called when installation name is changed"""
        self.app_config["installation_name"] = new_name
        save_app_config(self.app_config)
        self.log(f"💾 Installation name saved: {new_name}", LogLevel.SHOW_MODE)

    def on_master_volume_change(self, value):
        """Called when master volume slider changes"""
        volume = round(float(value), 1)  # Round to 1 decimal place
        self.master_volume_label.config(text=f"{int(volume)}%")
        self.app_config["master_volume"] = volume
        save_app_config(self.app_config)
        
        # Update all audio output instances
        for block in self.blocks:
            if hasattr(block, 'output_instance') and block.output_instance:
                if hasattr(block.output_instance, 'set_master_volume'):
                    block.output_instance.set_master_volume(volume / 100.0)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def add_block(self, preset=None):
        block = InteractionBlock(self.scrollable_frame, self.loader, self.logger, self.save_config, self.remove_block, preset)
        self.blocks.append(block)
        self.save_config()

    def remove_block(self, block):
        if block in self.blocks:
            # Stop any running instances before removing
            if hasattr(block, 'input_instance') and block.input_instance:
                if hasattr(block.input_instance, 'stop'):
                    block.input_instance.stop()
            if hasattr(block, 'output_instance') and block.output_instance:
                if hasattr(block.output_instance, 'stop'):
                    block.output_instance.stop()
            
            self.blocks.remove(block)
            self.save_config()

    def refresh_osc_status(self):
        """Refresh OSC server status display"""
        self.log(f"📡 OSC Status: {osc_manager.get_status()}", LogLevel.VERBOSE)

    def save_config(self):
        valid_blocks = [b for b in self.blocks if b.is_valid()]
        config = {
            "interactions": [b.to_dict() for b in valid_blocks]
        }
        
        try:
            with open("config/interactions/interactions.json", "w") as f:
                json.dump(config, f, indent=2)
            self.log("💾 Configuration saved", LogLevel.VERBOSE)
        except Exception as e:
            self.log(f"💥 Failed to save config: {e}", LogLevel.SHOW_MODE)

    def load_config(self):
        try:
            with open("config/interactions/interactions.json", "r") as f:
                config = json.load(f)
            
            for interaction in config.get("interactions", []):
                self.add_block(preset=interaction)
        except FileNotFoundError:
            self.log("📄 No existing config found, starting fresh", LogLevel.SHOW_MODE)
        except Exception as e:
            self.log(f"💥 Failed to load config: {e}", LogLevel.SHOW_MODE)

    def on_log_level_change(self, event=None):
        """Called when the log level dropdown changes"""
        selected_level = self.log_level_var.get()
        self._apply_log_level(selected_level)
        
        # Save to app config
        self.app_config["log_level"] = selected_level
        save_app_config(self.app_config)
        
        self.log(f"🔧 Log level set to: {selected_level}", LogLevel.SHOW_MODE)

    def _apply_log_level(self, level_str):
        """Applies the selected log level to the logger and OSC manager"""
        if level_str == "No Log":
            self.logger.set_level(LogLevel.NO_LOG)
        elif level_str == "Only Output Triggers":
            self.logger.set_level(LogLevel.OUTPUT_TRIGGERS_ONLY)
        elif level_str == "Show Mode":
            self.logger.set_level(LogLevel.SHOW_MODE)
        elif level_str == "Verbose":
            self.logger.set_level(LogLevel.VERBOSE)
        
        # Update OSC manager to use our logger
        update_osc_manager_logger(self.logger)

    def cleanup(self):
        """Clean up resources before shutdown"""
        self.log("🛑 Shutting down OSC servers...", LogLevel.SHOW_MODE)
        osc_manager.shutdown_all()
        
        # Stop all blocks
        for block in self.blocks:
            if hasattr(block, 'input_instance') and block.input_instance:
                if hasattr(block.input_instance, 'stop'):
                    block.input_instance.stop()
            if hasattr(block, 'output_instance') and block.output_instance:
                if hasattr(block.output_instance, 'stop'):
                    block.output_instance.stop()
        
        self.log("✅ Cleanup completed", LogLevel.SHOW_MODE)

def launch_gui():
    root = tk.Tk()
    app = InteractionGUI(root)
    
    # Set up cleanup on window close
    def on_closing():
        print("🔄 Closing Interaction App...")
        app.cleanup()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
