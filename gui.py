import tkinter as tk
from tkinter import ttk, filedialog
import os
import socket
import time
from module_loader import ModuleLoader
import threading
from PIL import Image, ImageTk
from modules.audio_output.audio_output import AudioOutputModule
from module_loader import input_event_router
from module_loader import create_and_start_module
from module_loader import get_config, save_config
from message_router import get_message_router
import traceback
import json  # Only for formatting, not for config loading

# Logging system with different verbosity levels
class LogLevel:
    NO_LOG = 0
    OSC = 1
    SERIAL = 2
    OUTPUTS = 3
    VERBOSE = 4

class Logger:
    def __init__(self, log_callback=None, level=LogLevel.OUTPUTS):
        self.log_callback = log_callback
        self.level = level
    
    def set_level(self, level):
        self.level = level
    
    def log(self, message, level=LogLevel.OUTPUTS):
        """Log a message if the current level allows it"""
        if self.level >= level and self.log_callback:
            self.log_callback(message)
    
    def no_log(self, message):
        """Log only when level is VERBOSE"""
        self.log(message, LogLevel.VERBOSE)
    
    def osc(self, message):
        """Log OSC messages with timestamp, port, address, and message"""
        if self.level >= LogLevel.OSC:
            timestamp = time.strftime('%H:%M:%S')
            self.log(f"[{timestamp}] 📡 {message}", LogLevel.OSC)
    
    def serial(self, message):
        """Log serial messages with timestamp, port, and value"""
        if self.level >= LogLevel.SERIAL:
            timestamp = time.strftime('%H:%M:%S')
            self.log(f"[{timestamp}] 🔌 {message}", LogLevel.SERIAL)
    
    def outputs(self, message):
        """Log output triggers with timestamp, module name, and file"""
        if self.level >= LogLevel.OUTPUTS:
            timestamp = time.strftime('%H:%M:%S')
            self.log(f"[{timestamp}] 🎵 {message}", LogLevel.OUTPUTS)
    
    def verbose(self, message):
        """Log only when level is VERBOSE"""
        self.log(message, LogLevel.VERBOSE)

# Import the OSC server manager
from modules.osc_input_trigger.osc_server_manager import osc_manager

# Update the OSC manager to use our logger
def update_osc_manager_logger(logger):
    """Update the OSC manager to use our logger"""
    osc_manager.log = logger.osc

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
    """Load app-level configuration with caching"""
    default_config = {
        "installation_name": "Default Installation",
        "theme": "dark",
        "version": "1.0.0",
        "log_level": "Outputs"
    }
    return get_config(APP_CONFIG_PATH, default_config)

def save_app_config(config):
    """Save app-level configuration with caching"""
    save_config(APP_CONFIG_PATH, config)

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

    def __init__(self, parent, loader, logger, on_change_callback, remove_callback, preset=None, current_log_level=None, gui_ref=None):
        logger.verbose(f"[InteractionBlock] __init__ start for preset: {preset}")
        try:
            self.parent = parent
            self.loader = loader
            self.logger = logger
            self.on_change_callback = on_change_callback
            self.remove_callback = remove_callback
            self.gui_ref = gui_ref  # Store reference to InteractionGUI
            self.input_var = tk.StringVar()
            self.output_var = tk.StringVar()
            self.input_instance = None
            self.output_instance = None
            self.input_config_fields = {}
            self.output_config_fields = {}
            self.input_mode = None  # Store mode for input module
            self.output_mode = None  # Store mode for output module
            self.cursor_running = True
            # Use optimized thread pool for cursor animation
            from module_loader import get_thread_pool
            thread_pool = get_thread_pool()
            self.cursor_thread = thread_pool.submit_realtime(self._cursor_animation_loop)
            if self.gui_ref and hasattr(self.gui_ref, 'threads'):
                self.gui_ref.threads.append(self.cursor_thread)
            self.osc_input_key = None
            self.osc_callback = None
            self.input_event_callback = None
            self.input_event_key = None
            self._initialized = False
            self._output_initialized = False
            self._last_output_module = None
            self._last_protocol = None
            self.frame_received_once = False
            self.frame_last_value = None
            self.output_config_memory = {}  # <-- Memory-backed config for output fields
            if preset is None:
                self.build_block()
                self._initialized = True
            else:
                self.preset = preset
                self.current_log_level = current_log_level
                self.logger.verbose(f"[InteractionBlock] Calling initialize_from_preset for preset: {preset}")
                self.initialize_from_preset()
            self.logger.verbose(f"[InteractionBlock] __init__ end for preset: {preset}")
        except Exception as e:
            logger.verbose(f"[InteractionBlock] __init__ exception for preset: {preset}\nReason: {e}\n{traceback.format_exc()}")
            raise

    def initialize_from_preset(self):
        self.logger.verbose(f"[InteractionBlock] initialize_from_preset start for preset: {self.preset}")
        try:
            if self._initialized:
                return  # Prevent double initialization
            self._initialized = True
            preset = self.preset or {}
            input_data = preset.get("input") or {}
            output_data = preset.get("output") or {}
            input_module = input_data.get("module", "")
            output_module = output_data.get("module", "")
            self.input_var.set(input_module)
            self.output_var.set(output_module)
            # --- Memory-backed config: store full output config ---
            self.output_config_memory = output_data.get("config", {}).copy() if output_data.get("config") else {}
            original_on_change_callback = self.on_change_callback
            self.on_change_callback = None
            self.build_block()  # Now build the UI (only once)
            # Populate input fields
            if self.loader.load_manifest(input_module) is not None:
                self.draw_input_fields(create_instance=False)
                for k, v in input_data.get("config", {}).items():
                    if k in self.input_config_fields:
                        field = self.input_config_fields[k]
                        if isinstance(field, tk.Entry):
                            field.delete(0, tk.END)
                            field.insert(0, v)
                        elif isinstance(field, tk.StringVar):
                            field.set(v)
            self.draw_output_fields()  # Draw output fields from memory
            self._output_initialized = False  # Force recreation
            self.create_output_instance(
                self.output_var.get(),
                self.loader.load_manifest(self.output_var.get()),
                self.get_output_config()
            )
            self.on_change_callback = original_on_change_callback
            if input_module:
                try:
                    self.input_instance = self.loader.create_module_instance(
                        input_module,
                        self.get_input_config(),
                        log_callback=self.logger.verbose
                    )
                    self.input_instance.start()
                except Exception as e:
                    self.logger.verbose(f"[InteractionBlock] Exception creating input_instance for {input_module}: {e}\n{traceback.format_exc()}")
            self.logger.verbose(f"[InteractionBlock] initialize_from_preset end for preset: {self.preset}")
        except Exception as e:
            self.logger.verbose(f"[InteractionBlock] initialize_from_preset exception for preset: {self.preset}\nReason: {e}\n{traceback.format_exc()}")
            raise

    def draw_output_fields(self, event=None):
        for widget in self.output_fields_container.winfo_children():
            widget.destroy()
        module_name = self.output_var.get()
        manifest = self.loader.load_manifest(module_name)
        if manifest is None:
            return
        if self._last_output_module != module_name:
            self._output_initialized = False
            self._last_output_module = module_name
        current_config = self.output_config_memory.copy()  # Use memory-backed config
        current_protocol = current_config.get('protocol', 'sacn')
        fields = self.get_protocol_dependent_fields(manifest, current_protocol)
        self.output_config_fields = {}
        for field in fields:
            if not self.should_show_field(field, current_config):
                continue
            value = current_config.get(field["name"], field.get("default"))
            if field["type"] == "button":
                action = field.get("action", field["name"])
                button = ttk.Button(self.output_fields_container, text=field["label"], 
                                  command=lambda name=action: self.handle_button_action(name), style="Action.TButton")
                button.pack(fill="x", pady=5, padx=5)
                continue
            if field["type"] == "waveform":
                waveform_label = ttk.Label(self.output_fields_container, text="Waveform", style="Label.TLabel")
                waveform_label.pack(anchor="w", padx=5, pady=(10, 5))
                waveform_container = ttk.Frame(self.output_fields_container, style="Fields.TFrame")
                waveform_container.pack(fill="x", pady=(0, 10), padx=5)
                waveform_canvas = tk.Canvas(waveform_container, width=300, height=60, bg="#111", highlightthickness=0)
                waveform_canvas.pack(fill="x")
                cursor_canvas = tk.Canvas(waveform_container, width=300, height=60, highlightthickness=0)
                cursor_canvas.place(in_=waveform_container, x=0, y=0, relwidth=1, relheight=1)
                self.output_config_fields[field["name"]] = {
                    "waveform": waveform_canvas,
                    "cursor": cursor_canvas,
                    "container": waveform_container,
                    "label": waveform_label,
                    "start_time": None,
                    "duration": None,
                    "is_playing": False
                }
                continue
            if field["type"] == "slider":
                label = ttk.Label(self.output_fields_container, text=field["label"], style="Label.TLabel")
                label.pack(anchor="w", padx=5, pady=(10, 5))
                slider_frame = ttk.Frame(self.output_fields_container, style="Fields.TFrame")
                slider_frame.pack(fill="x", pady=(0, 10), padx=5)
                slider_var = tk.DoubleVar(value=value)
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
            elif field["type"] == "select":
                label = ttk.Label(self.output_fields_container, text=field["label"], style="Label.TLabel")
                label.pack(anchor="w", padx=5, pady=(10, 5))
                options = field.get("options", [])
                option_values = [opt.get("value", opt.get("label", "")) for opt in options]
                option_labels = [opt.get("label", opt.get("value", "")) for opt in options]
                current_label = value
                if "value_map" in dict(zip(option_labels, option_values)):
                    value_map = dict(zip(option_labels, option_values))
                    for label, val in value_map.items():
                        if val == value:
                            current_label = label
                            break
                # Special handling for dmx_output_streaming serial_port dropdown
                if field["name"] == "serial_port" and module_name == "dmx_output_streaming":
                    try:
                        from modules.dmx_output.dmx_output_streaming import get_available_serial_ports
                        port_options = get_available_serial_ports()
                        if not port_options:
                            port_options = ["No ports available"]
                        option_labels = port_options
                        option_values = port_options
                    except Exception as e:
                        option_labels = ["Error getting ports"]
                        option_values = ["Error getting ports"]
                combo_var = tk.StringVar(value=current_label)
                combo = ttk.Combobox(self.output_fields_container, textvariable=combo_var, 
                                   values=option_labels, state="readonly", style="Combo.TCombobox")
                combo.pack(fill="x", pady=(0, 10), padx=5)
                self.output_config_fields[field["name"]] = {
                    "combo": combo,
                    "var": combo_var,
                    "value_map": dict(zip(option_labels, option_values))
                }
                # Bind change events for protocol selection
                if field["name"] == "protocol":
                    def on_protocol_change(event=None, self=self, combo_var=combo_var):
                        value = combo_var.get()
                        if value:
                            field_widget = self.output_config_fields[field["name"]]
                            if isinstance(field_widget, dict) and "value_map" in field_widget:
                                value_map = field_widget["value_map"]
                                protocol_value = value_map.get(value, value)
                            else:
                                protocol_value = value
                            self.output_config_memory[field["name"]] = protocol_value
                            self.draw_output_fields()
                            if self.on_change_callback:
                                self.on_change_callback()
                    combo.bind("<<ComboboxSelected>>", on_protocol_change)
                elif field["name"] == "serial_port":
                    def on_serial_port_change(event=None, self=self, combo_var=combo_var):
                        value = combo_var.get()
                        if value:
                            # Always save to 'serial_port' key, never to 'current_frame' or any other key
                            self.output_config_memory["serial_port"] = value
                            if self.on_change_callback:
                                self.on_change_callback()
                    combo.bind("<<ComboboxSelected>>", on_serial_port_change)
                else:
                    combo.bind("<<ComboboxSelected>>", lambda e: self.on_output_change())
                continue
            elif field["type"] == "file":
                label = ttk.Label(self.output_fields_container, text=field["label"], style="Label.TLabel")
                label.pack(anchor="w", padx=5, pady=(10, 5))
                file_frame = ttk.Frame(self.output_fields_container, style="Fields.TFrame")
                file_frame.pack(fill="x", pady=(0, 10), padx=5)
                entry = ttk.Entry(file_frame, style="Entry.TEntry")
                entry.insert(0, value)
                entry.pack(side="left", fill="x", expand=True)
                button = ttk.Button(file_frame, text="Browse", 
                                  command=lambda e=entry, ft=field.get("file_types", []): self.browse_csv_file(e, ft))
                button.pack(side="right", padx=(5, 0))
                self.output_config_fields[field["name"]] = entry
                entry.bind("<FocusOut>", lambda e, name=field["name"], entry=entry: self._on_output_entry_change(name, entry))
                entry.bind("<Return>", lambda e, name=field["name"], entry=entry: self._on_output_entry_change(name, entry))
                continue
            elif field["type"] == "text":
                label = ttk.Label(self.output_fields_container, text=field["label"], style="Label.TLabel")
                label.pack(anchor="w", padx=5, pady=(10, 5))
                entry = ttk.Entry(self.output_fields_container, style="Entry.TEntry")
                entry.insert(0, value)
                entry.pack(fill="x", pady=(0, 10), padx=5)
                self.output_config_fields[field["name"]] = entry
                entry.bind("<FocusOut>", lambda e, name=field["name"], entry=entry: self._on_output_entry_change(name, entry))
                entry.bind("<Return>", lambda e, name=field["name"], entry=entry: self._on_output_entry_change(name, entry))
                continue
            elif field["type"] == "number":
                label = ttk.Label(self.output_fields_container, text=field["label"], style="Label.TLabel")
                label.pack(anchor="w", padx=5, pady=(10, 5))
                entry = ttk.Entry(self.output_fields_container, style="Entry.TEntry")
                entry.insert(0, value)
                entry.pack(fill="x", pady=(0, 10), padx=5)
                self.output_config_fields[field["name"]] = entry
                entry.bind("<FocusOut>", lambda e, name=field["name"], entry=entry: self._on_output_entry_change(name, entry))
                entry.bind("<Return>", lambda e, name=field["name"], entry=entry: self._on_output_entry_change(name, entry))
                continue
            elif field["type"] == "display":
                label = ttk.Label(self.output_fields_container, text=f"{field['label']}: {value}", style="Label.TLabel")
                label.pack(anchor="w", padx=5, pady=(10, 5))
                self.output_config_fields[field["name"]] = label
                continue

    def _on_output_entry_change(self, name, entry):
        # Only update config for editable fields, never for display fields
        manifest = self.loader.load_manifest(self.output_var.get())
        field_type = None
        if manifest:
            for f in manifest.get('fields', []):
                if f['name'] == name:
                    field_type = f.get('type')
                    break
        if field_type == 'display':
            return  # Never save display fields to config
        value = entry.get()
        self.output_config_memory[name] = value
        if self.on_change_callback:
            self.on_change_callback()

    def on_output_change(self):
        # Update output_config_memory for all fields, but skip display-only fields
        for k, field in self.output_config_fields.items():
            # Skip display fields (e.g., current_frame)
            manifest = self.loader.load_manifest(self.output_var.get())
            field_type = None
            if manifest:
                for f in manifest.get('fields', []):
                    if f['name'] == k:
                        field_type = f.get('type')
                        break
            if field_type == 'display':
                continue  # Never save display fields to config
            if isinstance(field, dict) and "var" in field:
                self.output_config_memory[k] = field["var"].get()
            elif isinstance(field, tk.Entry):
                self.output_config_memory[k] = field.get()
        if self.output_instance and hasattr(self.output_instance, 'update_config'):
            self.output_instance.update_config(self.get_output_config())
        self.refresh_output_module_and_waveform()
        self.update_input_modules_based_on_output()
        if self.on_change_callback:
            self.on_change_callback()

    def get_output_config(self, include_all_fields=False):
        # Always return the full memory-backed config
        return self.output_config_memory.copy()

    def sync_output_fields_to_config(self):
        config = self.get_output_config()
        for k, v in config.items():
            field = self.output_config_fields.get(k)
            if not field:
                continue
            # Handle dropdowns (combos)
            if isinstance(field, dict) and "var" in field:
                combo = field.get("combo")
                if combo and v not in combo["values"]:
                    values = list(combo["values"])
                    values.append(v)
                    combo["values"] = values
                field["var"].set(v)
            # Handle text entries
            elif isinstance(field, tk.Entry):
                field.delete(0, tk.END)
                field.insert(0, v)

    def is_valid(self):
        return bool(self.input_var.get() and self.output_var.get())

    def on_change(self):
        # Only trigger save if not loading/initializing
        if hasattr(self.parent, 'loading') and (self.parent.loading or getattr(self.parent, 'initializing', False)):
            return
        if self.on_change_callback:
            self.on_change_callback()
        # Don't recreate instances on every change - just save config

    def on_input_change(self):
        """Called when an input field changes. Update config and save."""
        if hasattr(self.parent, 'loading') and (self.parent.loading or getattr(self.parent, 'initializing', False)):
            return
        if self.on_change_callback:
            self.on_change_callback()
        # Only recreate instance if module type actually changed
        if hasattr(self, 'input_instance') and self.input_instance:
            # Update existing instance config instead of recreating
            if hasattr(self.input_instance, 'update_config'):
                self.input_instance.update_config(self.get_input_config())

    def on_input_module_selected(self, event=None):
        if hasattr(self, 'frame') and self.frame:
            self.frame.destroy()
        new_input_module = self.input_var.get()
        new_preset = {
            "input": {"module": new_input_module, "config": {}},
            "output": {"module": self.output_var.get(), "config": self.output_config_memory.copy()}
        }
        self.preset = new_preset
        self._initialized = False
        self.initialize_from_preset()

    def on_output_module_selected(self, event=None):
        if hasattr(self, 'frame') and self.frame:
            self.frame.destroy()
        new_output_module = self.output_var.get()
        new_preset = {
            "input": {"module": self.input_var.get(), "config": self.get_input_config()},
            "output": {"module": new_output_module, "config": {}}
        }
        self.preset = new_preset
        self._initialized = False
        self.initialize_from_preset()

    def start_clock_display_update(self):
        """[REMOVED] Polling-based clock display update. Use event-driven updates instead."""
        # TODO: Implement event/callback-driven update for clock display if needed
        pass

    def start_serial_display_update(self):
        """[REMOVED] Polling-based serial display update. Use event-driven updates instead."""
        # TODO: Implement event/callback-driven update for serial input if needed
        pass

    def start_serial_trigger_display_update(self):
        """[REMOVED] Polling-based serial trigger display update. Use event-driven updates instead."""
        # TODO: Implement event/callback-driven update for serial trigger if needed
        pass

    def start_sacn_frames_display_update(self):
        """[REMOVED] Polling-based sACN frames display update. Use event-driven updates instead."""
        # TODO: Implement event/callback-driven update for sACN frames if needed
        pass

    def start_dmx_display_update(self):
        """Start periodic updates for DMX output module display only (not frames input)."""
        def update_dmx_display():
            try:
                # Update DMX output display
                if self.output_var.get() == "dmx_output_streaming":
                    # Update current frame label
                    current_frame_label = self.output_config_fields.get('current_frame')
                    if current_frame_label and self.output_instance and hasattr(current_frame_label, 'winfo_exists') and current_frame_label.winfo_exists():
                        # Get current frame from the module
                        display_data = self.output_instance.get_display_data()
                        current_frame = display_data.get('current_frame', 'No frame received')
                        current_frame_label.config(text=f"Current Frame: {current_frame}")
                    # Also refresh protocol-dependent fields if needed
                    try:
                        current_config = self.get_output_config()
                        current_protocol = current_config.get('protocol', 'sacn')
                        if hasattr(self, '_last_protocol') and self._last_protocol != current_protocol:
                            self._last_protocol = current_protocol
                            self.refresh_protocol_fields()
                        elif not hasattr(self, '_last_protocol'):
                            self._last_protocol = current_protocol
                    except Exception as e:
                        # Ignore config errors during display updates
                        pass
                # Only schedule next update for DMX output
                if self.output_var.get() == "dmx_output_streaming":
                    self.frame.after(100, update_dmx_display)
            except Exception as e:
                # If there's an error, stop the update cycle
                pass
        # Start the update cycle immediately
        update_dmx_display()

    def remove_self(self):
        self.cursor_running = False
        if hasattr(self, 'cursor_thread') and self.cursor_thread:
            # Cancel the thread pool task instead of joining
            if hasattr(self.cursor_thread, 'cancel'):
                self.cursor_thread.cancel()
            self.cursor_thread = None
        # Unregister input event callback if any
        if self.input_event_key and self.input_event_callback:
            input_event_router.unregister(*self.input_event_key, self.input_event_callback)
            self.input_event_key = None
            self.input_event_callback = None
        # Remove our callback from the shared OSC input instance if needed
        if self.osc_input_key and self.osc_callback:
            shared = InteractionGUI.osc_input_registry.get(self.osc_input_key)
            if shared:
                shared.remove_event_callback(self.osc_callback)
                InteractionGUI.osc_input_refcounts[self.osc_input_key] -= 1
                if InteractionGUI.osc_input_refcounts[self.osc_input_key] <= 0:
                    shared.stop()
                    del InteractionGUI.osc_input_registry[self.osc_input_key]
                    del InteractionGUI.osc_input_refcounts[self.osc_input_key]
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
            self.logger.verbose(f"⚠️ Waveform error: {e}")
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
            cursor_path = os.path.join(os.path.dirname(__file__), "modules", "audio_output_trigger", "cursor.png")
            try:
                img = Image.open(cursor_path)
                InteractionBlock.cursor_img = ImageTk.PhotoImage(img)
            except Exception as e:
                self.logger.verbose(f"⚠️ Failed to load cursor image: {e}")
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
                                cursor_path = os.path.join(os.path.dirname(__file__), "modules", "audio_output_trigger", "cursor.png")
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

        # Main content area - horizontal layout
        content_frame = ttk.Frame(self.frame, style="Block.TFrame")
        content_frame.pack(fill="x")

        # Input section (left)
        input_frame = ttk.LabelFrame(content_frame, text="Input", style="Section.TLabelframe")
        input_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        ttk.Label(input_frame, text="Module:", style="Label.TLabel").pack(anchor="w", padx=10, pady=(10, 5))
        input_combo = ttk.Combobox(input_frame, textvariable=self.input_var, state="readonly", style="Combo.TCombobox")
        input_combo.pack(fill="x", padx=10, pady=(0, 10))
        input_combo.bind("<<ComboboxSelected>>", self.on_input_module_selected)
        self.input_combo = input_combo  # Store direct reference

        # Populate input modules (raw names only)
        input_modules = self.loader.get_modules_by_type("input")
        input_combo["values"] = input_modules

        self.input_fields_container = ttk.Frame(input_frame, style="Fields.TFrame")
        self.input_fields_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Output section (middle)
        output_frame = ttk.LabelFrame(content_frame, text="Output", style="Section.TLabelframe")
        output_frame.pack(side="left", fill="both", expand=True, padx=5)

        ttk.Label(output_frame, text="Module:", style="Label.TLabel").pack(anchor="w", padx=10, pady=(10, 5))
        output_combo = ttk.Combobox(output_frame, textvariable=self.output_var, state="readonly", style="Combo.TCombobox")
        output_combo.pack(fill="x", padx=10, pady=(0, 10))
        output_combo.bind("<<ComboboxSelected>>", self.on_output_module_selected)

        # Populate output modules (raw names only)
        output_modules = self.loader.get_modules_by_type("output")
        output_combo["values"] = output_modules

        self.output_fields_container = ttk.Frame(output_frame, style="Fields.TFrame")
        self.output_fields_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Control section (right)
        control_frame = ttk.LabelFrame(content_frame, text="Controls", style="Section.TLabelframe")
        control_frame.pack(side="left", fill="y", padx=(5, 0))

        # Only show trigger button for 'trigger' or 'adaptive' output modules
        output_module = self.output_var.get()
        manifest = self.loader.load_manifest(output_module)
        if manifest and manifest.get("classification", "") in ["trigger", "adaptive"]:
            ttk.Button(control_frame, text="▶ Trigger", command=self.trigger_output, 
                       style="Action.TButton").pack(padx=10, pady=(20, 10), fill="x")
        
        # Remove button (in control section)
        ttk.Button(control_frame, text="🗑 Remove", command=self.remove_self, 
                  style="Remove.TButton").pack(padx=10, pady=(0, 20), fill="x")

    def draw_input_fields(self, event=None, create_instance=True):
        for widget in self.input_fields_container.winfo_children():
            widget.destroy()

        module_name = self.input_var.get()
        manifest = self.loader.load_manifest(module_name)
        if manifest is None:
            # handle error or skip
            return

        fields = manifest.get("fields", [])

        self.input_config_fields = {}
        for field in fields:
            if field["type"] == "button":
                action = field.get("action", field["name"])
                button = ttk.Button(self.input_fields_container, text=field["label"], 
                                  command=lambda name=action: self.handle_button_action(name), style="Action.TButton")
                button.pack(fill="x", pady=5, padx=5)
                continue
            if field["type"] == "label":
                # Handle label type fields (display only)
                if module_name == "serial_input_trigger":
                    if field["name"] == "current_value":
                        # Only add the Current Value label
                        label = ttk.Label(self.input_fields_container, text=f"{field['label']}: {field.get('default', '')}", style="Label.TLabel")
                        label.pack(anchor="w", padx=5, pady=(10, 0))
                        self.input_config_fields[field["name"]] = label
                        continue
                    elif field["name"] == "trigger_status":
                        # Skip adding Trigger Status label
                        continue
                elif field["name"] == "ip_address":
                    # Get local IP address
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        s.connect(("8.8.8.8", 80))
                        local_ip = s.getsockname()[0]
                        s.close()
                    except Exception:
                        local_ip = "127.0.0.1"
                    label = ttk.Label(self.input_fields_container, text=f"{field['label']}: {local_ip}", style="Label.TLabel")
                    label.pack(anchor="w", padx=5, pady=(10, 5))
                    self.input_config_fields[field["name"]] = label
                elif field["name"] == "current_time":
                    # Create a label for the current time
                    from datetime import datetime
                    current_time = datetime.now().strftime('%H:%M:%S')
                    current_time_label = ttk.Label(self.input_fields_container, text=f"Current Time: {current_time}", style="Label.TLabel")
                    current_time_label.pack(anchor="w", padx=5, pady=(10, 5))
                    self.input_config_fields[field["name"]] = current_time_label
                elif field["name"] == "countdown":
                    # Create a label for the countdown
                    countdown_label = ttk.Label(self.input_fields_container, text="Time Until Target: --:--:--", style="Label.TLabel")
                    countdown_label.pack(anchor="w", padx=5, pady=(10, 5))
                    self.input_config_fields[field["name"]] = countdown_label
                elif field["name"] == "connection_status":
                    # Create a label for connection status
                    connection_status_label = ttk.Label(self.input_fields_container, text=f"{field['label']}: {field.get('default', 'Disconnected')}", style="Label.TLabel")
                    connection_status_label.pack(anchor="w", padx=5, pady=(10, 5))
                    self.input_config_fields[field["name"]] = connection_status_label
                elif field["name"] == "incoming_data":
                    # Create a label for incoming data
                    incoming_data_label = ttk.Label(self.input_fields_container, text=f"{field['label']}: {field.get('default', 'No data received')}", style="Label.TLabel")
                    incoming_data_label.pack(anchor="w", padx=5, pady=(10, 5))
                    self.input_config_fields[field["name"]] = incoming_data_label
                elif field["name"] == "frame_number":
                    # Create a label for frame number (sACN or frames_input_streaming module)
                    initial_text = f"{field['label']}: No frame received"
                    frame_number_label = ttk.Label(self.input_fields_container, text=initial_text, style="Label.TLabel")
                    frame_number_label.pack(anchor="w", padx=5, pady=(10, 5))
                    self.input_config_fields[field["name"]] = frame_number_label
                    # For frames_input_streaming, do NOT poll/update label except in event callback
                    if self.input_var.get() == "frames_input_streaming":
                        self.frame_received_once = False
                        self.frame_last_value = None
                    continue
                else:
                    # For other label fields, show the default value
                    default_value = field.get("default", "")
                    label = ttk.Label(self.input_fields_container, text=f"{field['label']}: {default_value}", style="Label.TLabel")
                    label.pack(anchor="w", padx=5, pady=(10, 5))
                    self.input_config_fields[field["name"]] = label
                continue
            elif field["type"] == "dropdown":
                # Handle dropdown fields
                label = ttk.Label(self.input_fields_container, text=field["label"], style="Label.TLabel")
                label.pack(anchor="w", padx=5, pady=(10, 5))
                
                # Get options for the dropdown
                options = field.get("options", [])
                
                # Special handling for serial port dropdown
                if field["name"] == "port" and (module_name == "serial_input_streaming" or module_name == "serial_input_trigger"):
                    try:
                        # Import and get available ports
                        if module_name == "serial_input_streaming":
                            from modules.serial_input_streaming.serial_input import SerialInputModule
                        else:
                            from modules.serial_input_trigger.serial_trigger import SerialTriggerModule
                        options = SerialInputModule.get_available_ports() if module_name == "serial_input_streaming" else SerialTriggerModule.get_available_ports()
                        if not options:
                            options = ["No ports available"]
                    except Exception as e:
                        self.logger.verbose(f"⚠️ Error getting serial ports: {e}")
                        options = ["Error getting ports"]
                
                # Create combobox
                combo_var = tk.StringVar(value=field.get("default", ""))
                combo = ttk.Combobox(self.input_fields_container, textvariable=combo_var, 
                                   values=options, state="readonly", style="Combo.TCombobox")
                combo.pack(fill="x", pady=(0, 10), padx=5)
                
                # Bind change events
                if field["name"] == "port":
                    def on_serial_port_change(event=None, self=self, combo_var=combo_var):
                        value = combo_var.get()
                        if value and value != "No ports available" and value != "Error getting ports":
                            self.update_input_instance_with_new_serial_port(value)
                    combo.bind("<<ComboboxSelected>>", on_serial_port_change)
                elif field["name"] == "baud_rate":
                    def on_baud_change(event=None, self=self, combo_var=combo_var):
                        value = combo_var.get()
                        if value:
                            self.update_input_instance_with_new_baud_rate(value)
                    combo.bind("<<ComboboxSelected>>", on_baud_change)
                elif field["name"] == "logic_operator":
                    def on_logic_operator_change(event=None, self=self, combo_var=combo_var):
                        value = combo_var.get()
                        if value:
                            self.update_input_instance_with_new_logic_operator(value)
                    combo.bind("<<ComboboxSelected>>", on_logic_operator_change)
                else:
                    combo.bind("<<ComboboxSelected>>", lambda e: self.on_input_change())
                
                self.input_config_fields[field["name"]] = combo_var
                continue
            # For all other field types, create label + entry
            label = ttk.Label(self.input_fields_container, text=field["label"], style="Label.TLabel")
            label.pack(anchor="w", padx=5, pady=(10, 5))
            entry = ttk.Entry(self.input_fields_container, style="Entry.TEntry")
            entry.insert(0, field.get("default", ""))
            entry.pack(fill="x", pady=(0, 10), padx=5)
            if field["name"] == "port":
                def on_port_change(event=None, self=self, entry=entry):
                    value = entry.get()
                    try:
                        port = int(value)
                        self.update_input_instance_with_new_port(port)
                    except ValueError:
                        pass
                entry.bind("<FocusOut>", on_port_change)
                entry.bind("<Return>", on_port_change)
            elif field["name"] == "address":
                def on_address_change(event=None, self=self, entry=entry):
                    value = entry.get()
                    if value:
                        self.update_input_instance_with_new_address(value)
                entry.bind("<FocusOut>", on_address_change)
                entry.bind("<Return>", on_address_change)
            elif field["name"] == "target_time":
                # Special handling for target_time - don't recreate instance on every keystroke
                def on_target_time_change(event=None, self=self, entry=entry):
                    value = entry.get()
                    if value:
                        self.update_input_instance_with_new_target_time(value)
                entry.bind("<FocusOut>", on_target_time_change)
                entry.bind("<Return>", on_target_time_change)
            elif field["name"] == "threshold_value":
                # Special handling for threshold_value - don't recreate instance on every keystroke
                def on_threshold_value_change(event=None, self=self, entry=entry):
                    value = entry.get()
                    if value:
                        self.update_input_instance_with_new_threshold_value(value)
                entry.bind("<FocusOut>", on_threshold_value_change)
                entry.bind("<Return>", on_threshold_value_change)
            else:
                entry.bind("<KeyRelease>", lambda e: self.on_input_change())
            self.input_config_fields[field["name"]] = entry

        if create_instance:
            # Unregister previous input event callback if any
            if self.input_event_key and self.input_event_callback:
                input_event_router.unregister(*self.input_event_key, self.input_event_callback)
                self.input_event_key = None
                self.input_event_callback = None
            # Stop any existing input instance before creating a new one
            if self.input_instance and hasattr(self.input_instance, "stop"):
                self.logger.verbose("🛑 Stopping existing input instance...")
                self.input_instance.stop()
                self.logger.verbose(f"[DEBUG] input_instance stopped and set to None (was: {self.input_instance})")
                self.input_instance = None
            # Create or reuse shared input instance
            module_name = self.input_var.get()
            config = self.get_input_config()
            if module_name == "osc_input_trigger":
                port_val = config.get("port", 8000)
                try:
                    port = int(port_val)
                except Exception:
                    self.logger.verbose(f"⚠️ Invalid port: {port_val}")
                    return
                address = config.get("address", "/trigger")
                key = ("osc_input_trigger", {"port": port, "address": address})
                def block_event_callback(data):
                    self.update_fields_from_event(data, field_type='input')
                    self.connect_modules()
                    if self.output_instance:
                        self.output_instance.handle_event(data)
                input_event_router.register("osc_input_trigger", {"port": port, "address": address}, block_event_callback)
                self.input_event_key = ("osc_input_trigger", {"port": port, "address": address})
                self.input_event_callback = block_event_callback
                shared = InteractionGUI.osc_input_registry.get((port, address))
                if shared is None:
                    try:
                        shared = self.loader.create_module_instance(
                            module_name,
                            {**config, "port": port, "address": address},
                            log_callback=self.logger.verbose
                        )
                        shared.start()
                        InteractionGUI.osc_input_registry[(port, address)] = shared
                        InteractionGUI.osc_input_refcounts[(port, address)] = 0
                        self.logger.verbose(f"🔗 Created new shared OSCInputModule for {(port, address)}")
                    except Exception as e:
                        self.logger.verbose(f"⚠️ Failed to create shared OSC input instance: {e}")
                        return
                self.input_instance = shared
                InteractionGUI.osc_input_refcounts[(port, address)] += 1
            elif module_name == "clock_input_trigger":
                # Handle Clock input module
                def block_event_callback(data):
                    self.update_fields_from_event(data, field_type='input')
                    self.logger.verbose(f"🔔 Clock event received: {data}")
                    current_time_label = self.input_config_fields.get('current_time')
                    countdown_label = self.input_config_fields.get('countdown')
                    if current_time_label:
                        current_time = data.get('current_time', '--:--:--')
                        self.frame.after(0, lambda: current_time_label.config(text=f"Current Time: {current_time}") if current_time_label.winfo_exists() else None)
                    if countdown_label:
                        countdown = data.get('countdown', '--:--:--')
                        self.frame.after(0, lambda: countdown_label.config(text=f"Time Until Target: {countdown}") if countdown_label.winfo_exists() else None)
                    if data.get('trigger', False):
                        if self.logger.level == "verbose":
                            self.logger.verbose(f"🔔 Clock: Trigger event, sending to output_instance")
                        if self.output_instance:
                            if hasattr(self.output_instance, "update_config"):
                                self.output_instance.update_config(self.get_output_config())
                            if hasattr(self.output_instance, "set_cursor_callback"):
                                self.output_instance.set_cursor_callback(self.start_audio_playback)
                            self.output_instance.handle_event(data)
                            if self.logger.level == "verbose":
                                self.logger.verbose(f"✅ Clock: handle_event call completed")
                        else:
                            if self.logger.level == "verbose":
                                self.logger.verbose(f"⚠️ Clock: No output instance to send event to")
            elif module_name == "serial_input_streaming":
                # Handle Serial input module
                def block_event_callback(data):
                    self.update_fields_from_event(data, field_type='input')
                    self.logger.verbose(f"📡 Serial event received: {data}")
                    incoming_data_label = self.input_config_fields.get('incoming_data')
                    if incoming_data_label:
                        value = data.get('value', 'No data received')
                        incoming_data_label.config(text=f"Incoming Data: {value}")
                    if self.output_instance:
                        if hasattr(self.output_instance, "update_config"):
                            self.output_instance.update_config(self.get_output_config())
                        if hasattr(self.output_instance, "set_cursor_callback"):
                            self.output_instance.set_cursor_callback(self.start_audio_playback)
                        self.output_instance.handle_event(data)
                    else:
                        self.logger.verbose(f"⚠️ Serial: No output instance to send event to")
                
                try:
                    self.input_instance = self.loader.create_module_instance(
                        module_name,
                        config,
                        log_callback=self.logger.verbose
                    )
                    # Add the event callback directly to the Serial module
                    self.input_instance.add_event_callback(block_event_callback)
                    self.logger.verbose(f"🔗 Serial: Added event callback to module")
                    
                    self.input_instance.start()
                    self.logger.verbose(f"🚀 Serial: Module started")
                    # Start the display update immediately
                    self.start_serial_display_update()
                except Exception as e:
                    self.logger.verbose(f"⚠️ Failed to create serial input instance: {e}")
            elif module_name == "serial_input_trigger":
                # Handle Serial Trigger input module
                def block_event_callback(data):
                    self.update_fields_from_event(data, field_type='input')
                    self.logger.verbose(f"🎯 Serial trigger event received: {data}")
                    current_value_label = self.input_config_fields.get('current_value')
                    if current_value_label and self.input_instance:
                        value = data.get('value', 'No data')
                        self.frame.after(0, lambda: current_value_label.config(text=f"Value: {value}") if current_value_label.winfo_exists() else None)
                        self.logger.verbose(f"🎯 Serial trigger: Updated GUI label to '{value}'")
                    
                    # Send actual triggers to the output module
                    if data.get('trigger', False):
                        self.logger.verbose(f"🎯 Serial trigger: Processing trigger event")
                        # Direct connection to output module for Serial Trigger
                        if self.output_instance:
                            # Update output instance with current config
                            if hasattr(self.output_instance, "update_config"):
                                self.output_instance.update_config(self.get_output_config())
                            # Ensure cursor callback is set
                            if hasattr(self.output_instance, "set_cursor_callback"):
                                self.output_instance.set_cursor_callback(self.start_audio_playback)
                            # Send event to output
                            self.output_instance.handle_event(data)
                            self.logger.verbose(f"🎯 Serial trigger: Sent event to output module")
                        else:
                            self.logger.verbose(f"⚠️ Serial Trigger: No output instance to send event to")
                    else:
                        self.logger.verbose(f"🎯 Serial trigger: Non-trigger event (GUI update only)")
                
                try:
                    self.input_instance = self.loader.create_module_instance(
                        module_name,
                        config,
                        log_callback=self.logger.verbose
                    )
                    # Add the event callback directly to the Serial Trigger module
                    self.input_instance.add_event_callback(block_event_callback)
                    self.logger.verbose(f"🔗 Serial Trigger: Added event callback to module")
                    
                    self.input_instance.start()
                    self.logger.verbose(f"🚀 Serial Trigger: Module started")
                    # Start the display update immediately
                    self.start_serial_trigger_display_update()
                except Exception as e:
                    self.logger.verbose(f"⚠️ Failed to create serial trigger input instance: {e}")
            elif module_name == "sacn_frames_input_trigger":
                # Handle sACN Frames input module
                def block_event_callback(data):
                    self.update_fields_from_event(data, field_type='input')
                    self.logger.verbose(f"🎬 sACN frame event received: {data}")
                    frame_number_label = self.input_config_fields.get('frame_number')
                    if frame_number_label and self.input_instance:
                        frame_number = data.get('frame_number', 0)
                        self.frame.after(0, lambda: frame_number_label.config(text=f"Frame Number: {frame_number}") if frame_number_label.winfo_exists() else None)
                    
                    # Send triggers to the output module
                    if data.get('trigger', False):
                        self.logger.verbose(f"🎬 sACN: Processing trigger event")
                        # Direct connection to output module for sACN Frames
                        if self.output_instance:
                            # Update output instance with current config
                            if hasattr(self.output_instance, "update_config"):
                                self.output_instance.update_config(self.get_output_config())
                            # Ensure cursor callback is set
                            if hasattr(self.output_instance, "set_cursor_callback"):
                                self.output_instance.set_cursor_callback(self.start_audio_playback)
                            # Send event to output
                            self.output_instance.handle_event(data)
                            self.logger.verbose(f"🎬 sACN: Sent event to output module")
                        else:
                            self.logger.verbose(f"⚠️ sACN: No output instance to send event to")
                    else:
                        self.logger.verbose(f"🎬 sACN: Non-trigger event (GUI update only)")
                
                try:
                    self.input_instance = self.loader.create_module_instance(
                        module_name,
                        config,
                        log_callback=self.logger.verbose
                    )
                    # Add the event callback directly to the sACN Frames module
                    self.input_instance.add_event_callback(block_event_callback)
                    self.logger.verbose(f"🔗 sACN Frames: Added event callback to module")
                    
                    self.input_instance.start()
                    self.logger.verbose(f"🚀 sACN Frames: Module started")
                    # Start the display update immediately
                    self.start_sacn_frames_display_update()
                except Exception as e:
                    self.logger.verbose(f"⚠️ Failed to create sACN frames input instance: {e}")
            elif module_name == "frames_input_trigger":
                # Handle frames input module
                def block_event_callback(data):
                    self.update_fields_from_event(data, field_type='input')
                    self.logger.verbose(f"🎬 Frames input event received: {data}")
                    frame_number_label = self.input_config_fields.get('frame_number')
                    if frame_number_label and self.input_instance:
                        frame_number = data.get('frame_number', 0)
                        self.frame.after(0, lambda: frame_number_label.config(text=f"Frame Number: {frame_number}") if frame_number_label.winfo_exists() else None)
                    # Send triggers to the output module
                    if data.get('trigger', False):
                        self.logger.verbose(f"🎬 Frames input: Processing trigger event")
                        if self.output_instance:
                            if hasattr(self.output_instance, "update_config"):
                                self.output_instance.update_config(self.get_output_config())
                            if hasattr(self.output_instance, "set_cursor_callback"):
                                self.output_instance.set_cursor_callback(self.start_audio_playback)
                            self.output_instance.handle_event(data)
                            self.logger.verbose(f"🎬 Frames input: Sent event to output module")
                        else:
                            self.logger.verbose(f"⚠️ Frames input: No output instance to send event to")
                    else:
                        self.logger.verbose(f"🎬 Frames input: Non-trigger event (GUI update only)")
                try:
                    self.input_instance = self.loader.create_module_instance(
                        module_name,
                        config,
                        log_callback=self.logger.verbose
                    )
                    self.input_instance.add_event_callback(block_event_callback)
                    self.logger.verbose(f"🔗 Frames input: Added event callback to module")
                    self.input_instance.start()
                    self.logger.verbose(f"🚀 Frames input: Module started")
                except Exception as e:
                    self.logger.verbose(f"⚠️ Failed to create frames input instance: {e}")
            elif module_name == "time_input_trigger":
                # Handle Time input module
                def block_event_callback(data):
                    self.update_fields_from_event(data, field_type='input')
                    self.logger.verbose(f"🔔 Time event received: {data}")
                    current_time_label = self.input_config_fields.get('current_time')
                    countdown_label = self.input_config_fields.get('countdown')
                    if current_time_label:
                        current_time = data.get('current_time', '--:--:--')
                        self.frame.after(0, lambda: current_time_label.config(text=f"Current Time: {current_time}") if current_time_label.winfo_exists() else None)
                    if countdown_label:
                        countdown = data.get('countdown', '--:--:--')
                        self.frame.after(0, lambda: countdown_label.config(text=f"Time Until Target: {countdown}") if countdown_label.winfo_exists() else None)
                    # --- Patch: On trigger, send event to output module ---
                    if data.get('trigger', False):
                        self.logger.verbose(f"🔔 Time: Trigger event, sending to output_instance")
                        if self.output_instance:
                            if hasattr(self.output_instance, "update_config"):
                                self.output_instance.update_config(self.get_output_config())
                            if hasattr(self.output_instance, "set_cursor_callback"):
                                self.output_instance.set_cursor_callback(self.start_audio_playback)
                            self.output_instance.handle_event(data)
                            self.logger.verbose(f"✅ Time: handle_event call completed")
                        else:
                            self.logger.verbose(f"⚠️ Time: No output instance to send event to")
                try:
                    self.input_instance = self.loader.create_module_instance(
                        self.input_var.get(),
                        self.get_input_config(),
                        log_callback=self.logger.verbose
                    )
                    self.input_instance.add_event_callback(self.time_event_callback)
                    self.input_instance.start()
                except Exception as e:
                    self.logger.verbose(f"⚠️ Failed to create time input instance: {e}")
            else:
                try:
                    current_module_name = self.input_var.get()
                    current_config = self.get_input_config()
                    self.input_instance = self.loader.create_module_instance(
                        current_module_name,
                        current_config,
                        log_callback=self.logger.verbose
                    )
                    self.connect_modules()
                except Exception as e:
                    self.logger.verbose(f"⚠️ Failed to create input instance: {e}")

    def update_input_instance_with_new_port(self, port):
        config = self.get_input_config()
        config["port"] = port
        address = config.get("address", "/trigger")
        self._update_input_instance(port, address)
        if self.on_change_callback:
            self.on_change_callback()

    def update_input_instance_with_new_address(self, address):
        config = self.get_input_config()
        port_val = config.get("port", 8000)
        try:
            port = int(port_val)
        except Exception:
            self.logger.verbose(f"⚠️ Invalid port: {port_val}")
            return
        config["address"] = address
        self._update_input_instance(port, address)
        if self.on_change_callback:
            self.on_change_callback()

    def update_input_instance_with_new_target_time(self, target_time):
        """Update the Time module's target time."""
        if self.input_var.get() == "time_input_trigger":
            # Update the module's config directly
            if self.input_instance and hasattr(self.input_instance, 'update_config'):
                config = self.get_input_config()
                config["target_time"] = target_time
                self.input_instance.update_config(config)
                self.logger.verbose(f"⚙️ Time module config updated: target_time = {target_time}")
            if self.on_change_callback:
                self.on_change_callback()

    def update_input_instance_with_new_serial_port(self, port):
        """Update the Serial module's port."""
        if self.input_var.get() == "serial_input_streaming":
            # Update the module's config directly
            if self.input_instance and hasattr(self.input_instance, 'update_config'):
                config = self.get_input_config()
                config["port"] = port
                self.input_instance.update_config(config)
                self.logger.verbose(f"⚙️ Serial module config updated: port = {port}")
            # Trigger config save
            if self.on_change_callback:
                self.on_change_callback()

    def update_input_instance_with_new_baud_rate(self, baud_rate):
        """Update the Serial module's baud rate."""
        if self.input_var.get() == "serial_input_streaming":
            # Update the module's config directly
            if self.input_instance and hasattr(self.input_instance, 'update_config'):
                config = self.get_input_config()
                config["baud_rate"] = baud_rate
                self.input_instance.update_config(config)
                self.logger.verbose(f"⚙️ Serial module config updated: baud_rate = {baud_rate}")
            # Trigger config save
            if self.on_change_callback:
                self.on_change_callback()

    def update_input_instance_with_new_logic_operator(self, logic_operator):
        """Update the Serial Trigger module's logic operator."""
        if self.input_var.get() == "serial_input_trigger":
            # Update the module's config directly
            if self.input_instance and hasattr(self.input_instance, 'update_config'):
                config = self.get_input_config()
                config["logic_operator"] = logic_operator
                self.input_instance.update_config(config)
                self.logger.verbose(f"⚙️ Serial Trigger module config updated: logic_operator = {logic_operator}")
            # Trigger config save
            if self.on_change_callback:
                self.on_change_callback()

    def update_input_instance_with_new_threshold_value(self, threshold_value):
        """Update the Serial Trigger module's threshold value."""
        if self.input_var.get() == "serial_input_trigger":
            # Update the module's config directly
            if self.input_instance and hasattr(self.input_instance, 'update_config'):
                config = self.get_input_config()
                config["threshold_value"] = threshold_value
                self.input_instance.update_config(config)
                self.logger.verbose(f"⚙️ Serial Trigger module config updated: threshold_value = {threshold_value}")
            # Trigger config save
            if self.on_change_callback:
                self.on_change_callback()

    def update_output_instance_with_new_ip(self, ip_address):
        """Update the OSC output module's IP address."""
        if self.output_var.get() == "osc_output_streaming":
            # Update the module's config directly
            if self.output_instance and hasattr(self.output_instance, 'update_config'):
                config = self.get_output_config()
                config["ip_address"] = ip_address
                self.output_instance.update_config(config)
                self.logger.verbose(f"⚙️ OSC output module config updated: ip_address = {ip_address}")
            # Trigger config save
            if self.on_change_callback:
                self.on_change_callback()

    def update_output_instance_with_new_port(self, port):
        """Update the OSC output module's port."""
        if self.output_var.get() == "osc_output_streaming":
            # Update the module's config directly
            if self.output_instance and hasattr(self.output_instance, 'update_config'):
                config = self.get_output_config()
                config["port"] = port
                self.output_instance.update_config(config)
                self.logger.verbose(f"⚙️ OSC output module config updated: port = {port}")
            # Trigger config save
            if self.on_change_callback:
                self.on_change_callback()

    def update_output_instance_with_new_osc_address(self, osc_address):
        """Update the OSC output module's OSC address."""
        if self.output_var.get() == "osc_output_streaming":
            # Update the module's config directly
            if self.output_instance and hasattr(self.output_instance, 'update_config'):
                config = self.get_output_config()
                config["osc_address"] = osc_address
                self.output_instance.update_config(config)
                self.logger.verbose(f"⚙️ OSC output module config updated: osc_address = {osc_address}")
            # Trigger config save
            if self.on_change_callback:
                self.on_change_callback()

    def _update_input_instance(self, port, address):
        module_name = self.input_var.get()
        if module_name == "osc_input_trigger":
            key = ("osc_input_trigger", {"port": port, "address": address})
            def block_event_callback(data):
                self.update_fields_from_event(data, field_type='input')
                self.connect_modules()
                if self.output_instance:
                    self.output_instance.handle_event(data)
            # Register the new callback FIRST
            input_event_router.register("osc_input_trigger", {"port": port, "address": address}, block_event_callback)
            # Now unregister the old callback (if any)
            if self.input_event_key and self.input_event_callback:
                input_event_router.unregister(*self.input_event_key, self.input_event_callback)
            self.input_event_key = ("osc_input", {"port": port, "address": address})
            self.input_event_callback = block_event_callback
            shared = InteractionGUI.osc_input_registry.get((port, address))
            if shared is None:
                try:
                    shared = self.loader.create_module_instance(
                        module_name,
                        {**self.get_input_config(), "port": port, "address": address},
                        log_callback=self.logger.verbose
                    )
                    shared.start()
                    InteractionGUI.osc_input_registry[(port, address)] = shared
                    InteractionGUI.osc_input_refcounts[(port, address)] = 0
                    self.logger.verbose(f"🔗 Created new shared OSCInputModule for {(port, address)}")
                except Exception as e:
                    self.logger.verbose(f"⚠️ Failed to create shared OSC input instance: {e}")
                    return
            self.input_instance = shared
            InteractionGUI.osc_input_refcounts[(port, address)] += 1
        else:
            # For non-OSC input modules
            if self.input_event_key and self.input_event_callback:
                input_event_router.unregister(*self.input_event_key, self.input_event_callback)
            try:
                self.input_instance = self.loader.create_module_instance(
                    module_name,
                    self.get_input_config(),
                    log_callback=self.logger.verbose
                )
                self.connect_modules()
            except Exception as e:
                self.logger.verbose(f"⚠️ Failed to create input instance: {e}")

    def create_output_instance(self, module_name, manifest, new_config):
        """
        Create the output module instance only once per block/module change.
        """
        if self._output_initialized:
            self.logger.verbose(f"[DEBUG] Output instance already initialized for module: {module_name}")
            return
        self.logger.verbose(f"[DEBUG] Creating output instance for module: {module_name}")
        # Stop any existing output instance before creating a new one
        if self.output_instance and hasattr(self.output_instance, 'stop'):
            self.logger.verbose("🛑 Stopping existing output instance...")
            self.output_instance.stop()
        try:
            # Use appropriate logging method based on module type
            if module_name == "osc_output_trigger" or module_name == "osc_output_streaming":
                log_callback = self.logger.osc
            else:
                log_callback = self.logger.verbose
            self.output_instance = create_and_start_module(
                self.loader,
                module_name,
                new_config,
                event_callback=lambda data: None,  # Output modules don't need event callbacks
                log_callback=log_callback
            )
            # Set log level for the new module
            if hasattr(self.output_instance, 'log_level'):
                self.output_instance.log_level = 'info'
            # Set up cursor callback for audio output
            if hasattr(self.output_instance, 'set_cursor_callback'):
                self.output_instance.set_cursor_callback(self.start_audio_playback)
            
            # Set input classification for adaptive output modules
            if hasattr(self.output_instance, "set_input_classification"):
                input_module = self.input_var.get()
                if input_module:
                    input_manifest = self.loader.load_manifest(input_module)
                    if input_manifest:
                        input_classification = input_manifest.get("classification", "unknown")
                        self.output_instance.set_input_classification(input_classification)
                        self.logger.verbose(f"🔗 Set input classification '{input_classification}' for adaptive output module")
            
            self._output_initialized = True  # Mark output as initialized
            self._last_output_module = module_name
        except Exception as e:
            self.logger.verbose(f"⚠️ Failed to create output instance: {e}")

    def should_show_field(self, field, current_config):
        """Check if a field should be shown based on conditional display rules."""
        if "show_if" not in field:
            return True
        
        show_condition = field["show_if"]
        condition_field = show_condition.get("field")
        condition_value = show_condition.get("value")
        
        if condition_field not in current_config:
            return True  # Show if condition field doesn't exist
        
        current_value = current_config[condition_field]
        
        if isinstance(condition_value, list):
            return current_value in condition_value
        else:
            return current_value == condition_value

    def get_protocol_dependent_fields(self, manifest, current_protocol):
        """Get fields that should be shown for the current protocol."""
        fields = manifest.get("fields", [])
        protocol_fields = []
        
        for field in fields:
            # Always show fields without show_if conditions
            if "show_if" not in field:
                protocol_fields.append(field)
                continue
            
            # Check if field should be shown for current protocol
            show_condition = field["show_if"]
            condition_field = show_condition.get("field")
            condition_value = show_condition.get("value")
            
            if condition_field == "protocol":
                if isinstance(condition_value, list):
                    if current_protocol in condition_value:
                        protocol_fields.append(field)
                else:
                    if current_protocol == condition_value:
                        protocol_fields.append(field)
            else:
                # For other conditions, include the field (will be filtered later)
                protocol_fields.append(field)
        
        return protocol_fields

    def on_slider_change(self, field, value):
        """Called when a slider value changes"""
        volume = int(float(value))  # Convert to integer for volume slider
        
        # Update the label
        if field["name"] in self.output_config_fields:
            self.output_config_fields[field["name"]]["label"].config(text=f"{volume}")
        
        # Update the output instance if it exists
        if self.output_instance and hasattr(self.output_instance, 'update_config'):
            # Update the config with the new volume value
            config = self.get_output_config()
            config[field["name"]] = volume
            self.output_instance.update_config(config)
        
        # Save config
        if self.on_change_callback:
            self.on_change_callback()

    def start_audio_playback(self, duration):
        """Start audio playback tracking for cursor"""
        if "waveform" in self.output_config_fields:
            waveform_data = self.output_config_fields["waveform"]
            waveform_data["start_time"] = time.time()
            waveform_data["duration"] = duration
            waveform_data["is_playing"] = True
            self.logger.verbose(f"🎵 Started cursor animation: duration={duration:.2f}s at {time.strftime('%H:%M:%S')}")
        else:
            self.logger.verbose(f"⚠️ No waveform field found for cursor animation")

    def update_waveform_cursor(self, position):
        """Legacy method - now handled by cursor thread"""
        pass  # Cursor animation is now handled by the thread

    def start_modules(self):
        """Start input and output module instances if they exist."""
        if hasattr(self, 'input_instance') and self.input_instance:
            if hasattr(self.input_instance, 'start'):
                self.input_instance.start()
        if hasattr(self, 'output_instance') and self.output_instance:
            if hasattr(self.output_instance, 'start'):
                self.output_instance.start()

    def set_fields_from_config(self, preset):
        # Set all GUI fields from config, no callbacks
        input_data = preset.get("input", {})
        output_data = preset.get("output", {})
        input_module = input_data.get("module", "")
        output_module = output_data.get("module", "")
        self.input_var.set(input_module)
        self.output_var.set(output_module)
        self.draw_input_fields(create_instance=False)
        for k, v in input_data.get("config", {}).items():
            if k in self.input_config_fields:
                field = self.input_config_fields[k]
                if isinstance(field, tk.Entry):
                    field.delete(0, tk.END)
                    field.insert(0, v)
                elif isinstance(field, tk.StringVar):
                    field.set(v)
        self.draw_output_fields()
        for k, v in output_data.get("config", {}).items():
            if k in self.output_config_fields:
                field = self.output_config_fields[k]
                if isinstance(field, tk.Entry):
                    field.delete(0, tk.END)
                    field.insert(0, v)
                elif isinstance(field, dict) and "var" in field:
                    if "value_map" in field:
                        value_map = field["value_map"]
                        for label, value in value_map.items():
                            if value == v:
                                field["var"].set(label)
                                break
                        else:
                            field["var"].set(v)
                    else:
                        field["var"].set(v)
    def instantiate_modules_from_gui(self):
        # Instantiate modules after all fields are set
        input_module = self.input_var.get()
        output_module = self.output_var.get()
        input_config = self.get_input_config()
        output_config = self.get_output_config(include_all_fields=True)
        if input_module:
            try:
                self.input_instance = self.loader.create_module_instance(
                    input_module, input_config, log_callback=self.logger.verbose)
                if self.input_instance is not None and hasattr(self.input_instance, 'start'):
                    self.input_instance.start()
            except Exception as e:
                self.logger.verbose(f"⚠️ Failed to create input instance: {e}")
        if output_module:
            try:
                self.output_instance = self.loader.create_module_instance(
                    output_module, output_config, log_callback=self.logger.verbose)
                
                # Set input classification for adaptive output modules
                if hasattr(self.output_instance, "set_input_classification"):
                    input_module = self.input_var.get()
                    if input_module:
                        input_manifest = self.loader.load_manifest(input_module)
                        if input_manifest:
                            input_classification = input_manifest.get("classification", "unknown")
                            self.output_instance.set_input_classification(input_classification)
                            self.logger.verbose(f"🔗 Set input classification '{input_classification}' for adaptive output module")
                
                if self.output_instance is not None and hasattr(self.output_instance, 'start'):
                    self.output_instance.start()
            except Exception as e:
                self.logger.verbose(f"⚠️ Failed to create output instance: {e}")
        # Ensure event/callback registration and input→output connection
        self.connect_modules()
    def enable_callbacks(self):
        # Enable callbacks for user changes after initialization
        if self.gui_ref is not None:
            self.on_change_callback = self.gui_ref.save_config
        else:
            self.on_change_callback = None

    def on_event_received(self, data):
        # Update GUI fields based on event data
        # Example: update frame number, time, etc.
        if 'frame_number' in data:
            label = self.input_config_fields.get('frame_number')
            if label:
                value = data.get('frame_number', 'No frame received')
                label.config(text=f"Frame Number: {value}")
        if 'current_time' in data:
            label = self.input_config_fields.get('current_time')
            if label:
                value = data.get('current_time', '--:--:--')
                label.config(text=f"Current Time: {value}")
        if 'countdown' in data:
            label = self.input_config_fields.get('countdown')
            if label:
                value = data.get('countdown', '--:--:--')
                label.config(text=f"Time Until Target: {value}")
        # Add more field updates as needed for your modules

    def on_state_change(self, state):
        # Optionally update block appearance based on state
        if hasattr(self, 'frame'):
            color = {
                'ready': '#d4ffd4',
                'error': '#ffd4d4',
                'starting': '#ffffd4',
                'stopped': '#f0f0f0',
                'configured': '#d4e0ff',
            }.get(state, '#ffffff')
            self.frame.config(bg=color)
            for child in self.frame.winfo_children():
                try:
                    child.config(bg=color)
                except Exception:
                    pass

    def trigger_output(self, *args, **kwargs):
        # Default trigger_output to prevent AttributeError; override in subclasses or set dynamically if needed
        if hasattr(self, 'logger'):
            self.logger.verbose('[InteractionBlock] trigger_output called (default/no-op)')
        pass

    def get_input_config(self, *args, **kwargs):
        # Return a dict of all input field values for the selected input module
        config = {}
        for k, field in self.input_config_fields.items():
            if isinstance(field, dict) and "var" in field:
                config[k] = field["var"].get()
            elif isinstance(field, tk.Entry):
                config[k] = field.get()
            elif isinstance(field, tk.StringVar):
                config[k] = field.get()
        return config

    def handle_button_action(self, name, *args, **kwargs):
        # Stub: handle button actions as needed
        if hasattr(self, 'logger'):
            self.logger.verbose(f'[InteractionBlock] handle_button_action called (stub) for {name}')
        pass

    def browse_csv_file(self, *args, **kwargs):
        # Stub: implement file dialog as needed
        if hasattr(self, 'logger'):
            self.logger.verbose('[InteractionBlock] browse_csv_file called (stub)')
        pass

    def refresh_output_module_and_waveform(self, *args, **kwargs):
        # Stub: refresh output module and waveform as needed
        if hasattr(self, 'logger'):
            self.logger.verbose('[InteractionBlock] refresh_output_module_and_waveform called (stub)')
        pass

    def update_input_modules_based_on_output(self, *args, **kwargs):
        # Stub: update input modules as needed
        if hasattr(self, 'logger'):
            self.logger.verbose('[InteractionBlock] update_input_modules_based_on_output called (stub)')
        pass

    def update_output_modules_based_on_input(self, *args, **kwargs):
        # Stub: update output modules as needed
        if hasattr(self, 'logger'):
            self.logger.verbose('[InteractionBlock] update_output_modules_based_on_input called (stub)')
        pass

    def connect_modules(self, *args, **kwargs):
        # Stub: connect modules as needed
        if hasattr(self, 'logger'):
            self.logger.verbose('[InteractionBlock] connect_modules called (stub)')
        pass

    def refresh_protocol_fields(self, *args, **kwargs):
        # Stub: refresh protocol fields as needed
        if hasattr(self, 'logger'):
            self.logger.verbose('[InteractionBlock] refresh_protocol_fields called (stub)')
        pass

    def purge_display_fields_from_output_config_memory(self):
        """Remove all display fields from output_config_memory before saving."""
        manifest = self.loader.load_manifest(self.output_var.get())
        if not manifest:
            return
        display_fields = [f['name'] for f in manifest.get('fields', []) if f.get('type') == 'display']
        for field in display_fields:
            if field in self.output_config_memory:
                del self.output_config_memory[field]

    def to_dict(self):
        # Purge display fields before saving config
        self.purge_display_fields_from_output_config_memory()
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

    def time_event_callback(self, data):
        # Update current time and countdown labels
        current_time_label = self.input_config_fields.get('current_time')
        countdown_label = self.input_config_fields.get('countdown')
        if current_time_label:
            current_time = data.get('current_time', '--:--:--')
            self.frame.after(0, lambda: current_time_label.config(text=f"Current Time: {current_time}") if current_time_label.winfo_exists() else None)
        if countdown_label:
            countdown = data.get('countdown', '--:--:--')
            self.frame.after(0, lambda: countdown_label.config(text=f"Time Until Target: {countdown}") if countdown_label.winfo_exists() else None)
        # --- Patch: On trigger, send event to output module ---
        if data.get('trigger', False):
            self.logger.verbose(f"🔔 Time: Trigger event, sending to output_instance")
            if self.output_instance:
                if hasattr(self.output_instance, "update_config"):
                    self.output_instance.update_config(self.get_output_config())
                if hasattr(self.output_instance, "set_cursor_callback"):
                    self.output_instance.set_cursor_callback(self.start_audio_playback)
                self.output_instance.handle_event(data)
                self.logger.verbose(f"✅ Time: handle_event call completed")
            else:
                self.logger.verbose(f"⚠️ Time: No output instance to send event to")

    def update_fields_from_event(self, event_dict, field_type='input'):
        """
        Update GUI fields (input or output) at runtime from an event dict.
        Only fields tagged with 'runtime_update': true in the manifest will be updated.
        Args:
            event_dict: dict of field_name -> value
            field_type: 'input' or 'output'
        """
        if field_type == 'input':
            manifest = self.loader.load_manifest(self.input_var.get())
            fields = self.input_config_fields
        else:
            manifest = self.loader.load_manifest(self.output_var.get())
            fields = self.output_config_fields
        if not manifest:
            return
        for field in manifest.get('fields', []):
            if not field.get('runtime_update'):
                continue
            name = field['name']
            if name not in event_dict or name not in fields:
                continue
            value = event_dict[name]
            widget = fields[name]
            # Handle label fields
            if isinstance(widget, tk.Label):
                widget.config(text=f"{field.get('label', name)}: {value}")
            # Handle entry fields
            elif isinstance(widget, tk.Entry):
                widget.delete(0, tk.END)
                widget.insert(0, value)
            # Handle StringVar fields (e.g., dropdowns)
            elif isinstance(widget, tk.StringVar):
                widget.set(value)
            # Handle dict fields with 'var' (e.g., dropdowns)
            elif isinstance(widget, dict) and 'var' in widget:
                widget['var'].set(value)

class InteractionGUI:
    # Shared registry for OSC input modules: (port, address) -> OSCInputModule instance
    osc_input_registry = {}
    osc_input_refcounts = {}

    def __init__(self, root):
        self.root = root
        self.logger = Logger(self._write_to_log)
        self.loader = ModuleLoader()
        self.blocks = []
        self.threads = []
        self.loading = False
        self.initializing = False
        self.current_log_level = LogLevel.OUTPUTS
        self.event_router = get_message_router()  # Use the optimized event router
        self.app_config = load_app_config()
        self.closing = False
        self.setup_styles()
        self.build_gui()
        self._apply_log_level(self.log_level_var.get())
        self._show_initializing_overlay()
        threading.Thread(target=self._startup_barrier, daemon=True).start()
        # Subscribe to module events and state changes
        # self.event_router.subscribe('module_event', self._on_module_event)
        # self.event_router.register_state_subscriber(None, self._on_module_state_change)
        # Add a debugging panel for live event/state flow
        self._init_debug_panel()

    def _show_initializing_overlay(self):
        # Destroy any existing overlay before creating a new one
        if hasattr(self, 'init_overlay') and self.init_overlay:
            try:
                self.init_overlay.destroy()
                self.logger.verbose("[_show_initializing_overlay] Previous init_overlay destroyed before creating new one.")
            except Exception as e:
                self.logger.verbose(f"[_show_initializing_overlay] Exception destroying previous init_overlay: {e}")
            self.init_overlay = None
        self.logger.verbose("[_show_initializing_overlay] Creating initializing overlay.")
        self.init_overlay = tk.Toplevel(self.root)
        self.init_overlay.title('Initializing...')
        self.init_overlay.geometry('400x100+300+300')
        self.init_overlay.transient(self.root)
        self.init_overlay.grab_set()
        self.init_overlay_label = tk.Label(self.init_overlay, text='Initializing modules, please wait...', font=('Inter', 14))
        self.init_overlay_label.pack(expand=True, fill='both')
        self.init_overlay.update()

    def _hide_initializing_overlay(self):
        self.logger.verbose("[_hide_initializing_overlay] Hiding initializing overlay.")
        # Destroy both possible overlay attributes
        if hasattr(self, 'init_overlay') and self.init_overlay:
            try:
                self.init_overlay.destroy()
                self.logger.verbose("[_hide_initializing_overlay] init_overlay destroyed.")
            except Exception as e:
                self.logger.verbose(f"[_hide_initializing_overlay] Exception destroying init_overlay: {e}")
            self.init_overlay = None
        if hasattr(self, 'initializing_overlay') and self.initializing_overlay:
            try:
                self.initializing_overlay.destroy()
                self.logger.verbose("[_hide_initializing_overlay] initializing_overlay destroyed.")
            except Exception as e:
                self.logger.verbose(f"[_hide_initializing_overlay] Exception destroying initializing_overlay: {e}")
            self.initializing_overlay = None
        # Also destroy debug panel if it exists and is a Toplevel
        if hasattr(self, 'debug_panel') and self.debug_panel:
            try:
                self.debug_panel.destroy()
                self.logger.verbose("[_hide_initializing_overlay] debug_panel destroyed.")
            except Exception as e:
                self.logger.verbose(f"[_hide_initializing_overlay] Exception destroying debug_panel: {e}")
            self.debug_panel = None
        # Enumerate all Toplevel windows after hiding overlays
        self._log_all_toplevels()

    def _log_all_toplevels(self):
        # Helper to log all Toplevel windows for debugging stray popups
        import tkinter
        toplevels = []
        for widget in self.root.winfo_children():
            if isinstance(widget, tkinter.Toplevel):
                try:
                    title = widget.title()
                except Exception:
                    title = '<unknown>'
                toplevels.append(title)
        self.logger.verbose(f"[OverlayDebug] Remaining Toplevel windows: {toplevels}")

    def _startup_barrier(self):
        # Load config and instantiate modules, but do not enable GUI/event flow yet
        self.logger.verbose("[StartupBarrier] Waiting for all modules to be ready...")
        self.loading = True
        self.initializing = True
        self._show_initializing_overlay()
        self.blocks = []
        self.threads = []
        self._modules_ready = set()
        self._modules_total = set()
        # Load config and create blocks
        try:
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
            for interaction in config:
                block = self.add_block_atomic(preset=interaction)
                if block is None:
                    self.logger.verbose(f"[StartupBarrier] Skipping invalid block for interaction: {interaction}")
                    continue
                if block.input_instance:
                    self._modules_total.add(block.input_instance)
                    self.logger.verbose(f"[StartupBarrier] Added input_instance to _modules_total: {repr(block.input_instance)} (id={id(block.input_instance)})")
                if block.output_instance:
                    self._modules_total.add(block.output_instance)
                    self.logger.verbose(f"[StartupBarrier] Added output_instance to _modules_total: {repr(block.output_instance)} (id={id(block.output_instance)})")
            self.logger.verbose(f"[StartupBarrier] Modules to wait for: {len(self._modules_total)}")
        except Exception as e:
            self.logger.verbose(f"[StartupBarrier] Failed to load config: {e}")
        # Wait for all modules to be ready
        def on_state_change(module, state):
            self.logger.verbose(f"[StartupBarrier] State change: {module} (id={id(module)}) -> {state}")
            if state == 'ready':
                self._modules_ready.add(module)
            # Log the ids and reprs of both sets
            total_ids = [id(m) for m in self._modules_total]
            ready_ids = [id(m) for m in self._modules_ready]
            self.logger.verbose(f"[StartupBarrier] _modules_total ids: {total_ids}")
            self.logger.verbose(f"[StartupBarrier] _modules_ready ids: {ready_ids}")
            self.logger.verbose(f"[StartupBarrier] _modules_total reprs: {[repr(m) for m in self._modules_total]}")
            self.logger.verbose(f"[StartupBarrier] _modules_ready reprs: {[repr(m) for m in self._modules_ready]}")
            if self._modules_ready == self._modules_total:
                self.logger.verbose("[StartupBarrier] All modules ready!")
                self._on_all_modules_ready()
            else:
                not_ready = self._modules_total - self._modules_ready
                self.logger.verbose(f"[StartupBarrier] Still waiting for: {not_ready}")
        self.event_router.register_state_subscriber(None, on_state_change)
        # Immediately check if all modules are already ready
        if all(getattr(m, 'state', None) == 'ready' for m in self._modules_total):
            self.logger.verbose("[StartupBarrier] All modules already ready after registration!")
            self._on_all_modules_ready()

    def _on_all_modules_ready(self):
        self.logger.verbose("[_on_all_modules_ready] All modules are ready. Hiding overlays and enabling GUI.")
        self._hide_initializing_overlay()
        self.loading = False
        self.initializing = False
        # System-level sync for dynamic output fields
        self.sync_all_dynamic_output_fields_to_config()
        # Update system state label to Ready
        if hasattr(self, 'status_label'):
            self.status_label.config(text="System State: Ready")
        # Optionally, log that GUI is now interactive
        self.logger.verbose("[_on_all_modules_ready] GUI is now interactive.")

    def sync_all_dynamic_output_fields_to_config(self):
        """After all modules are ready, ensure all dynamic output fields (e.g., serial_port) are set to their config values."""
        for block in self.blocks:
            if hasattr(block, 'output_config_fields') and hasattr(block, 'get_output_config'):
                config = block.get_output_config()
                for k, v in config.items():
                    field = block.output_config_fields.get(k)
                    if not field:
                        continue
                    # Handle dropdowns (combos)
                    if isinstance(field, dict) and "var" in field:
                        combo = field.get("combo")
                        if combo and v not in combo["values"]:
                            values = list(combo["values"])
                            values.append(v)
                            combo["values"] = values
                        field["var"].set(v)
                    # Handle text entries
                    elif isinstance(field, tk.Entry):
                        field.delete(0, tk.END)
                        field.insert(0, v)

    def _write_to_log(self, msg):
        """Internal method to write to the log text widget - thread-safe"""
        if getattr(self, 'closing', False):
            # If closing, do not update GUI, just print
            print(f"[LOG] {msg}")
            return
        try:
            # Use after() to schedule the update on the main thread
            self.root.after(0, self._write_to_log_safe, msg)
        except Exception:
            # Fallback to print if GUI is not available
            print(f"[LOG] {msg}")

    def _write_to_log_safe(self, msg):
        """Thread-safe method to write to log text widget (called on main thread)"""
        try:
            self.log_text.insert(tk.END, f"{msg}\n")
            self.log_text.see(tk.END)
            # Limit log entries to prevent memory issues
            if int(self.log_text.index('end-1c').split('.')[0]) > 1000:
                self.log_text.delete('1.0', '500.0')
        except Exception as e:
            # Fallback to print if widget operations fail
            print(f"[LOG ERROR] {e}: {msg}")

    def log(self, msg, level=LogLevel.OUTPUTS):
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

        # Master volume slider and label removed

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
        self.log_level_var = tk.StringVar(value=self.app_config.get("log_level", "Outputs"))
        log_level_combo = ttk.Combobox(log_control_frame, textvariable=self.log_level_var, 
                                      values=["No Logging", "OSC", "Serial", "Outputs", "Verbose/Debug"], 
                                      state="readonly", width=20, style="Combo.TCombobox")
        log_level_combo.pack(side="left")
        log_level_combo.bind("<<ComboboxSelected>>", self.on_log_level_change)
        # Add Clean Console button
        ttk.Button(log_control_frame, text="Clean Console", command=self.clean_console, style="Remove.TButton").pack(side="left", padx=(10, 0))
        self.log_text = tk.Text(log_frame, height=8, bg="#2a2a2a", fg="#00ff00", 
                               font=("Consolas", 10), relief="flat", bd=0)
        self.log_text.pack(fill="both")

        # Add a status label for system state at the bottom
        if not hasattr(self, 'status_label'):
            self.status_label = tk.Label(self.root, text="System State: Initializing", anchor="w", fg="gray")
            self.status_label.pack(side="bottom", fill="x")

    def on_installation_name_change(self, new_name):
        """Called when installation name is changed"""
        self.app_config["installation_name"] = new_name
        save_app_config(self.app_config)
        self.log(f"💾 Installation name saved: {new_name}", LogLevel.VERBOSE)

    # on_master_volume_change and all master volume logic removed

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def add_block(self, preset=None):
        try:
            block = InteractionBlock(self.scrollable_frame, self.loader, self.logger, self.save_config, self.remove_block, preset=preset, current_log_level=self.current_log_level, gui_ref=self)
            self.blocks.append(block)
            return block
        except Exception as e:
            self.logger.verbose(f"[add_block] Failed to create block for preset: {preset}\nReason: {e}")
            return None

    def remove_block(self, block):
        if block in self.blocks:
            # Stop any running instances before removing
            if hasattr(block, 'input_instance') and block.input_instance:
                if hasattr(block.input_instance, 'stop'):
                    block.input_instance.stop()
            if hasattr(block, 'output_instance') and block.output_instance:
                if hasattr(block.output_instance, 'stop'):
                    block.output_instance.stop()
            # Destroy the block's frame so it disappears from the GUI
            if hasattr(block, 'frame') and block.frame:
                block.frame.destroy()
            self.blocks.remove(block)
            # Only save config if not loading/initializing
            if not (self.loading or self.initializing):
                self.save_config()  # Save config only on explicit remove

    def refresh_osc_status(self):
        """Refresh OSC server status display"""
        self.log(f"📡 OSC Status: {osc_manager.get_status()}", LogLevel.VERBOSE)

    def save_config(self):
        # Only save config on explicit user actions or module events
        if getattr(self, 'loading', False) or getattr(self, 'initializing', False):
            return  # Prevent saving during loading/initializing
        valid_blocks = [b for b in self.blocks if b.is_valid()]
        config = {
            "installation_name": getattr(self, 'installation_name', 'Interactive Art Installation'),
            "interactions": [b.to_dict() for b in valid_blocks]
        }
        try:
            with open("config/interactions/interactions.json", "w") as f:
                json.dump(config, f, indent=2)
            self.log("💾 Configuration saved", LogLevel.VERBOSE)
        except Exception as e:
            self.log(f"💥 Failed to save config: {e}", LogLevel.VERBOSE)

    def load_config(self):
        self.loading = True  # <-- Set loading flag
        self.initializing = True  # <-- Begin atomic initialization
        try:
            with open("config/interactions/interactions.json", "r") as f:
                config = json.load(f)
            
            for interaction in config.get("interactions", []):
                block = self.add_block_atomic(preset=interaction)
                self.blocks.append(block)
        except FileNotFoundError:
            self.log("📄 No existing config found, starting fresh", LogLevel.VERBOSE)
        except Exception as e:
            self.log(f"💥 Failed to load config: {e}", LogLevel.VERBOSE)
        self.initializing = False  # <-- End atomic initialization
        self.loading = False  # <-- Unset loading flag after loading
        # Now enable callbacks for all blocks
        for block in self.blocks:
            block.enable_callbacks()

    def add_block_atomic(self, preset=None):
        block = InteractionBlock(self.scrollable_frame, self.loader, self.logger, self.save_config, self.remove_block, preset, current_log_level=self.log_level_var.get(), gui_ref=self)
        # Only call build_block if preset is None (i.e., new/empty block)
        if preset is None:
            block.build_block()
        self.blocks.append(block)
        return block

    def on_log_level_change(self, event=None):
        """Called when the log level dropdown changes"""
        selected_level = self.log_level_var.get()
        
        # Clear console when log level changes
        self.clean_console()
        
        self._apply_log_level(selected_level)
        
        # Save to app config
        self.app_config["log_level"] = selected_level
        save_app_config(self.app_config)
        
        self.log(f"🔧 Log level set to: {selected_level}", LogLevel.VERBOSE)

    def _apply_log_level(self, level_str):
        """Applies the selected log level to the logger and OSC manager"""
        if level_str == "No Logging":
            self.logger.set_level(LogLevel.NO_LOG)
        elif level_str == "OSC":
            self.logger.set_level(LogLevel.OSC)
        elif level_str == "Serial":
            self.logger.set_level(LogLevel.SERIAL)
        elif level_str == "Outputs":
            self.logger.set_level(LogLevel.OUTPUTS)
        elif level_str == "Verbose/Debug":
            self.logger.set_level(LogLevel.VERBOSE)
        
        # Update OSC manager to use our logger
        update_osc_manager_logger(self.logger)
        
        # Update log level for all existing modules
        self._update_module_log_levels(level_str)
    
    def _update_module_log_levels(self, level_str):
        """Update log level for all existing input and output modules"""
        for block in self.blocks:
            # Update input module log level
            if hasattr(block, 'input_instance') and block.input_instance:
                if hasattr(block.input_instance, 'log_level'):
                    block.input_instance.log_level = 'verbose' if level_str == "Verbose" else 'info'
            
            # Update output module log level
            if hasattr(block, 'output_instance') and block.output_instance:
                if hasattr(block.output_instance, 'log_level'):
                    block.output_instance.log_level = 'verbose' if level_str == "Verbose" else 'info'

    def clean_console(self):
        """Erase all content in the log_text widget (console)."""
        self.log_text.delete('1.0', tk.END)

    def cleanup(self):
        """Clean up resources before shutdown"""
        self.closing = True  # <-- Set closing flag to prevent GUI log updates
        self.log("🛑 Starting cleanup process...", LogLevel.VERBOSE)
        # Step 1: Stop cursor threads and all tracked threads
        self.log("🛑 Stopping all background threads...", LogLevel.VERBOSE)
        for i, thread in enumerate(self.threads):
            self.log(f"🛑 Joining thread {i}...", LogLevel.VERBOSE)
            if thread.is_alive():
                thread.join(timeout=2)
                if thread.is_alive():
                    self.log(f"⚠️ Thread {i} did not stop within timeout, continuing...", LogLevel.VERBOSE)
                else:
                    self.log(f"✅ Thread {i} stopped successfully", LogLevel.VERBOSE)
        self.threads.clear()
        # Step 2: Shutdown OSC servers
        self.log("🛑 Shutting down OSC servers...", LogLevel.VERBOSE)
        try:
            osc_manager.shutdown_all()
            self.log("✅ OSC servers shutdown completed", LogLevel.VERBOSE)
        except Exception as e:
            self.log(f"⚠️ Error shutting down OSC servers: {e}", LogLevel.VERBOSE)
        # Step 3: Stop input instances
        self.log("🛑 Stopping input instances...", LogLevel.VERBOSE)
        for i, block in enumerate(self.blocks):
            if hasattr(block, 'input_instance') and block.input_instance:
                self.log(f"🛑 Stopping input instance for block {i}...", LogLevel.VERBOSE)
                if hasattr(block.input_instance, 'stop'):
                    try:
                        block.input_instance.stop()
                        self.log(f"✅ Input instance {i} stopped", LogLevel.VERBOSE)
                    except Exception as e:
                        self.log(f"⚠️ Error stopping input instance {i}: {e}", LogLevel.VERBOSE)
        # Step 4: Stop output instances
        self.log("🛑 Stopping output instances...", LogLevel.VERBOSE)
        for i, block in enumerate(self.blocks):
            if hasattr(block, 'output_instance') and block.output_instance:
                self.log(f"🛑 Stopping output instance for block {i}...", LogLevel.VERBOSE)
                if hasattr(block.output_instance, 'stop'):
                    try:
                        block.output_instance.stop()
                        self.log(f"✅ Output instance {i} stopped", LogLevel.VERBOSE)
                    except Exception as e:
                        self.log(f"⚠️ Error stopping output instance {i}: {e}", LogLevel.VERBOSE)
        self.log("✅ Cleanup completed", LogLevel.VERBOSE)

    # def _on_module_event(self, event):
    #     # Called on any module event; update relevant GUI block
    #     def update_gui():
    #         # Find the block corresponding to the module and update its display
    #         module = event.get('module')
    #         data = event.get('data')
    #         for block in self.blocks:
    #             if block.input_instance == module or block.output_instance == module:
    #                 block.on_event_received(data)
    #     self.root.after(0, update_gui)

    # def _on_module_state_change(self, module, state):
    #     # Called on any module state change; update GUI indicators
    #     def update_gui():
    #         for block in self.blocks:
    #             if block.input_instance == module or block.output_instance == module:
    #                 block.on_state_change(state)
    #         # Optionally update a global status indicator
    #         if hasattr(self, 'status_label'):
    #             self.status_label.config(text=f"System State: {state}")
    #     self.root.after(0, update_gui)

    def _init_debug_panel(self):
        # Add a simple debug panel to visualize event/state flow
        if hasattr(self, 'debug_panel'):
            return
        self.debug_panel = tk.Toplevel(self.root)
        self.debug_panel.title("Event/State Debug Panel")
        self.debug_panel.geometry("400x300")
        self.debug_text = tk.Text(self.debug_panel, state='disabled', height=20)
        self.debug_text.pack(fill='both', expand=True)
        # Hook into EventRouter debug log
        def update_debug_log():
            self.debug_text.config(state='normal')
            self.debug_text.delete(1.0, tk.END)
            for event_type, meta in self.event_router.debug_log[-100:]:
                self.debug_text.insert(tk.END, f"{event_type}: {meta}\n")
            self.debug_text.config(state='disabled')
            self.debug_panel.after(1000, update_debug_log)
        update_debug_log()

def launch_gui():
    root = tk.Tk()
    root.geometry("700x900")  # Set a more compact window width
    root.resizable(width=False, height=True)  # Disable width resizing, allow height
    app = InteractionGUI(root)
    
    # Set up cleanup on window close
    def on_closing():
        print("🔄 Closing Interaction App...")
        try:
            # Add timeout to cleanup to prevent hanging
            import threading
            import time
            
            def cleanup_with_timeout():
                app.cleanup()
            
            cleanup_thread = threading.Thread(target=cleanup_with_timeout, daemon=True)
            cleanup_thread.start()
            cleanup_thread.join(timeout=5)  # Wait max 5 seconds for cleanup
            
            if cleanup_thread.is_alive():
                print("⚠️ Cleanup timed out, forcing exit...")
        except Exception as e:
            print(f"⚠️ Error during cleanup: {e}")
        
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
