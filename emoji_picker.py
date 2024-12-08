import os
import json
import threading
import keyboard
import requests
from io import BytesIO
from PIL import Image, ImageTk
import customtkinter as ctk
import tkinter as tk
import win32gui
import win32api
import win32con
import pyperclip
import pystray
import webbrowser
from urllib.parse import urlparse
import tkinter as tk
from tkinter import messagebox
import time
import win32process
import hashlib
from pystray import Icon, Menu, MenuItem
from fuzzywuzzy import fuzz
import sys

class AddEmojiWindow(ctk.CTkToplevel):
    def __init__(self, parent, category=None):
        super().__init__(parent)
        self.title("Add Emoji")
        self.geometry("300x200")
        self.resizable(False, False)
        
        # Name Frame
        name_frame = ctk.CTkFrame(self)
        name_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(name_frame, text="Name:").pack(side="left", padx=5)
        self.name_entry = ctk.CTkEntry(name_frame)
        self.name_entry.pack(side="left", expand=True, fill="x", padx=5)
        
        # Enable paste in name entry
        self.name_entry.bind('<<Paste>>', self.paste_text)
        self.name_entry.bind('<Button-3>', self.show_context_menu)
        
        # URL Frame
        url_frame = ctk.CTkFrame(self)
        url_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(url_frame, text="URL:").pack(side="left", padx=5)
        self.url_entry = ctk.CTkEntry(url_frame)
        self.url_entry.pack(side="left", expand=True, fill="x", padx=5)
        
        # Enable paste in URL entry
        self.url_entry.bind('<<Paste>>', self.paste_text)
        self.url_entry.bind('<Button-3>', self.show_context_menu)
        
        # Preview Frame
        self.preview_frame = ctk.CTkFrame(self)
        self.preview_frame.pack(fill="x", padx=10, pady=5)
        self.preview_label = ctk.CTkLabel(self.preview_frame, text="Preview will appear here")
        self.preview_label.pack(pady=10)
        
        # Preview button
        preview_btn = ctk.CTkButton(
            self,
            text="Preview",
            command=self.preview_emoji
        )
        preview_btn.pack(pady=5)
        
        # Add button
        add_btn = ctk.CTkButton(
            self,
            text="Add Emoji",
            command=self.add_emoji
        )
        add_btn.pack(side="bottom", pady=10)
        
        # Set focus to name entry
        self.name_entry.focus()

    def paste_text(self, event):
        widget = event.widget
        try:
            widget.delete("sel.first", "sel.last")
        except:
            pass
        widget.insert("insert", widget.clipboard_get())
        return "break"

    def show_context_menu(self, event):
        widget = event.widget
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Paste", command=lambda: self.paste_to_widget(widget))
        menu.tk_popup(event.x_root, event.y_root)

    def paste_to_widget(self, widget):
        widget.delete(0, "end")
        widget.insert(0, self.clipboard_get())

    def preview_emoji(self):
        url = self.url_entry.get()
        if not url:
            return
            
        try:
            response = requests.get(url)
            img = Image.open(BytesIO(response.content))
            img = img.resize((64, 64), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            self.preview_label.configure(image=photo, text="")
            self.preview_label.image = photo
        except Exception as e:
            self.preview_label.configure(text=f"Error loading preview: {str(e)}", image="")

    def add_emoji(self):
        url = self.url_entry.get()
        name = self.name_entry.get()
        
        if not url or not name:
            return
            
        if "emojis" not in self.parent.emojis:
            self.parent.emojis["emojis"] = []
            
        self.parent.emojis["emojis"].append({
            "name": name,
            "url": url
        })
        
        self.parent.save_emojis()
        self.parent.display_emojis()
        self.destroy()

class AddAliasWindow(ctk.CTkToplevel):
    def __init__(self, parent, emoji):
        super().__init__(parent)
        self.title("Add Alias")
        self.geometry("250x120")
        self.resizable(False, False)
        
        self.parent = parent
        self.emoji = emoji
        
        # Create main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Alias entry
        alias_label = ctk.CTkLabel(main_frame, text="Alternative name:")
        alias_label.pack(pady=(0, 5))
        
        self.alias_entry = ctk.CTkEntry(main_frame)
        self.alias_entry.pack(fill="x", pady=(0, 10))
        
        # Save button
        save_btn = ctk.CTkButton(main_frame, text="Save", command=self.save_alias)
        save_btn.pack(pady=5)
        
        # Center window
        self.center_window()
        
    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
        
    def save_alias(self):
        alias = self.alias_entry.get().strip()
        if alias:
            if "aliases" not in self.emoji:
                self.emoji["aliases"] = []
            self.emoji["aliases"].append(alias)
            self.parent.save_emojis()
            self.destroy()

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("350x450")
        self.resizable(False, False)
        
        self.parent = parent
        
        # Set window font
        self.window_font = ctk.CTkFont(family=parent.settings.get("font", {}).get("family", "Segoe UI"), 
                                     size=parent.settings.get("font", {}).get("size", 12))
        
        # Create tabs directly without extra space
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add tabs
        self.tabview.add("General")
        self.tabview.add("Templates")
        self.tabview.add("Appearance")
        
        self.create_settings_ui()
    
    def create_settings_ui(self):
        # General Settings Tab
        general_frame = self.tabview.tab("General")
        
        # Hotkey
        hotkey_label = ctk.CTkLabel(general_frame, text="Hotkey:", font=self.window_font)
        hotkey_label.pack(anchor="w", pady=(0, 5))
        
        self.hotkey_entry = ctk.CTkEntry(general_frame, font=self.window_font)
        self.hotkey_entry.pack(fill="x", pady=(0, 10))
        self.hotkey_entry.insert(0, self.parent.settings.get("hotkey", "ctrl+shift+e"))
        
        # Paste delay
        delay_label = ctk.CTkLabel(general_frame, text="Paste delay (ms):", font=self.window_font)
        delay_label.pack(anchor="w", pady=(0, 5))
        
        self.delay_entry = ctk.CTkEntry(general_frame, font=self.window_font)
        self.delay_entry.pack(fill="x", pady=(0, 10))
        self.delay_entry.insert(0, str(self.parent.settings.get("paste_delay_ms", 100)))
        
        # Start with Windows
        self.start_with_windows_var = tk.BooleanVar(value=self.parent.settings.get("start_with_windows", False))
        start_with_windows_cb = ctk.CTkCheckBox(
            general_frame,
            text="Start with Windows",
            variable=self.start_with_windows_var,
            font=self.window_font
        )
        start_with_windows_cb.pack(anchor="w", pady=5)
        
        # Minimize to tray
        self.minimize_to_tray_var = tk.BooleanVar(value=self.parent.settings.get("minimize_to_tray", True))
        minimize_to_tray_cb = ctk.CTkCheckBox(
            general_frame,
            text="Minimize to tray",
            variable=self.minimize_to_tray_var,
            font=self.window_font
        )
        minimize_to_tray_cb.pack(anchor="w", pady=5)
        
        # Templates Tab
        templates_frame = self.tabview.tab("Templates")
        
        # Template list
        self.template_frame = ctk.CTkScrollableFrame(templates_frame)
        self.template_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Add template button
        add_template_btn = ctk.CTkButton(
            templates_frame,
            text="Add Template",
            command=self.add_template,
            font=self.window_font
        )
        add_template_btn.pack(fill="x")
        
        # Load existing templates
        self.load_templates()
        
        # Appearance Tab
        appearance_frame = self.tabview.tab("Appearance")
        
        # Font family
        font_label = ctk.CTkLabel(appearance_frame, text="Font Family:", font=self.window_font)
        font_label.pack(anchor="w", pady=(0, 5))
        
        font_families = ["Segoe UI", "Arial", "Helvetica", "Times New Roman", "Courier New"]
        self.font_family_var = tk.StringVar(value=self.parent.settings.get("font", {}).get("family", "Segoe UI"))
        font_dropdown = ctk.CTkOptionMenu(
            appearance_frame,
            values=font_families,
            variable=self.font_family_var,
            font=self.window_font
        )
        font_dropdown.pack(fill="x", pady=(0, 10))
        
        # Font size
        size_label = ctk.CTkLabel(appearance_frame, text="Font Size:", font=self.window_font)
        size_label.pack(anchor="w", pady=(0, 5))
        
        self.font_size_var = tk.StringVar(value=str(self.parent.settings.get("font", {}).get("size", 12)))
        size_entry = ctk.CTkEntry(
            appearance_frame,
            textvariable=self.font_size_var,
            font=self.window_font
        )
        size_entry.pack(fill="x", pady=(0, 10))
        
        # Save button
        save_btn = ctk.CTkButton(self, text="Save", command=self.save_settings, font=self.window_font)
        save_btn.pack(side="bottom", pady=10)

    def load_templates(self):
        for widget in self.template_frame.winfo_children():
            widget.destroy()
        
        self.template_vars = []
        
        templates = self.parent.settings.get("custom_templates", [])
        for i, template in enumerate(templates):
            frame = ctk.CTkFrame(self.template_frame)
            frame.pack(fill="x", pady=2)
            
            name_entry = ctk.CTkEntry(frame, placeholder_text="Template name", font=self.window_font)
            name_entry.insert(0, template["name"])
            name_entry.pack(side="left", padx=5)
            
            template_entry = ctk.CTkEntry(frame, placeholder_text="Template", font=self.window_font)
            template_entry.insert(0, template["template"])
            template_entry.pack(side="left", padx=5, expand=True, fill="x")
            
            delete_btn = ctk.CTkButton(
                frame,
                text="✕",
                width=30,
                command=lambda idx=i: self.delete_template(idx),
                font=self.window_font
            )
            delete_btn.pack(side="right", padx=5)
            
            self.template_vars.append((name_entry, template_entry))

    def add_template(self):
        templates = self.parent.settings.get("custom_templates", [])
        templates.append({
            "name": "New Template",
            "template": "{url}",
            "is_default": False
        })
        self.parent.settings["custom_templates"] = templates
        self.load_templates()

    def delete_template(self, idx):
        templates = self.parent.settings.get("custom_templates", [])
        if len(templates) > 1:
            del templates[idx]
            self.parent.settings["custom_templates"] = templates
            self.load_templates()

    def save_settings(self):
        # Get current settings
        settings = {
            "hotkey": self.hotkey_entry.get(),
            "start_with_windows": self.start_with_windows_var.get(),
            "minimize_to_tray": self.minimize_to_tray_var.get(),
            "paste_delay_ms": int(self.delay_entry.get()),
            "font": {
                "family": self.font_family_var.get(),
                "size": int(self.font_size_var.get())
            },
            "custom_templates": []
        }
        
        # Save templates
        for name_entry, template_entry in self.template_vars:
            settings["custom_templates"].append({
                "name": name_entry.get(),
                "template": template_entry.get()
            })
        
        # Update parent settings
        self.parent.settings = settings
        self.parent.save_settings()
        
        # Update font
        self.parent.update_font()
        
        # Close window
        self.destroy()

class EmojiPicker(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Create cache directory if it doesn't exist
        self.cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Load settings
        self.settings_file = "settings.json"
        self.settings = self.load_settings()
        
        # Load emojis
        self.emojis_file = "emojis.json"
        self.emojis = self.load_emojis()
        
        # Initialize UI
        self.title("Emoji Picker")
        self.geometry("330x400")
        self.resizable(False, False)
        self.withdraw()  # Hide window initially
        
        # Create system tray
        self.create_tray()
        
        # Create UI
        self.create_ui()
        
        # Register hotkey
        keyboard.add_hotkey(self.settings["hotkey"], self.show_window)
        
        # Store emoji buttons
        self.emoji_buttons = []
        self.current_focus = -1
        
        # Display emojis
        self.display_emojis()

    def create_tray(self):
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        
        menu = pystray.Menu(
            pystray.MenuItem("Show", self.show_from_tray),
            pystray.MenuItem("Exit", self.quit_app)
        )
        
        self.tray_icon = pystray.Icon(
            "emoji_picker",
            Image.open(icon_path),
            "Emoji Picker",
            menu
        )
        
        # Start tray icon in a separate thread
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_from_tray(self, icon, item):
        self.after(0, self.show_window)

    def quit_app(self, icon, item):
        self.tray_icon.stop()
        self.quit()

    def load_emoji_image(self, url, size=(48, 48)):
        # Generate cache filename from URL
        cache_filename = hashlib.md5(url.encode()).hexdigest() + ".png"
        cache_path = os.path.join(self.cache_dir, cache_filename)
        
        try:
            # Try to load from cache first
            if os.path.exists(cache_path):
                image = Image.open(cache_path)
            else:
                # Download and cache if not found
                response = requests.get(url)
                image = Image.open(BytesIO(response.content))
                image.save(cache_path)
            
            # Resize image
            image = image.resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(image)
        except Exception as e:
            print(f"Error loading emoji image: {e}")
            return None

    def load_emojis(self):
        try:
            with open(self.emojis_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            default_emojis = {
                "emojis": [
                    {"name": "Example", "url": "https://example.com/emoji.png"}
                ]
            }
            with open(self.emojis_file, "w", encoding="utf-8") as f:
                json.dump(default_emojis, f, indent=4)
            return default_emojis

    def display_emojis(self, search_term=""):
        # Clear existing emojis
        for widget in self.emoji_frame.winfo_children():
            widget.destroy()
        
        self.emoji_buttons = []
        row = col = 0
        max_cols = 5
        
        # Get all emojis from the list
        all_emojis = self.emojis.get("emojis", [])
            
        # Filter emojis if search term exists
        filtered_emojis = [
            emoji for emoji in all_emojis
            if not search_term or self.emoji_matches_search(emoji, search_term)
        ]
        
        # Display emojis in grid
        for emoji in filtered_emojis:
            photo = self.load_emoji_image(emoji["url"])
            
            button = ctk.CTkButton(
                self.emoji_frame,
                text="",
                image=photo,
                width=50,
                height=50,
                command=lambda e=emoji: self.select_emoji(e)
            )
            button.grid(row=row, column=col, padx=2, pady=2)
            button.emoji = emoji
            
            # Bind hover events
            button.bind("<Enter>", lambda e, em=emoji: self.show_emoji_preview(em))
            button.bind("<Leave>", self.hide_emoji_preview)
            button.bind("<Button-3>", lambda e, em=emoji, b=button: self.show_context_menu(e, em, b))
            
            self.emoji_buttons.append(button)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # Add "+" button at the end if not searching
        if not search_term:
            if col == 0:
                current_row = row
                current_col = col
            else:
                current_row = row
                current_col = col
            
            add_button = ctk.CTkButton(
                self.emoji_frame,
                text="+",
                width=50,
                height=50,
                command=self.open_add_emoji
            )
            add_button.grid(row=current_row, column=current_col, padx=2, pady=2)
        
        # Update focus if needed
        if self.current_focus >= len(self.emoji_buttons):
            self.current_focus = len(self.emoji_buttons) - 1
        self.update_focus()

    def show_context_menu(self, event, emoji, button):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Copy URL", command=lambda: self.copy_emoji_url(emoji))
        menu.add_command(label="Add Alias", command=lambda: self.add_emoji_alias(emoji))
        menu.add_command(label="Delete", command=lambda: self.delete_emoji(emoji, button))
        
        # Show menu at event position
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def copy_emoji_url(self, emoji):
        pyperclip.copy(emoji["url"])

    def add_emoji_alias(self, emoji):
        alias_window = AddAliasWindow(self, emoji)
        alias_window.focus()

    def delete_emoji(self, emoji, button):
        if messagebox.askyesno("Delete Emoji", "Are you sure you want to delete this emoji?"):
            self.emojis["emojis"].remove(emoji)
            self.save_emojis()
            button.destroy()

    def show_emoji_preview(self, emoji):
        photo = self.load_emoji_image(emoji["url"], size=(32, 32))
        self.preview_label.configure(image=photo)
        self.preview_label.image = photo  # Keep a reference to prevent garbage collection
        self.name_label.configure(text=f"{emoji['name']}  ")  # Added space for right padding

    def hide_emoji_preview(self, event=None):
        self.preview_label.configure(image="")
        self.name_label.configure(text="")

    def update_focus(self):
        for i, button in enumerate(self.emoji_buttons):
            if i == self.current_focus:
                button.configure(fg_color=("gray70", "gray30"))
                self.show_emoji_preview(button.emoji)
            else:
                button.configure(fg_color=("gray75", "gray25"))

    def next_emoji(self, event):
        if self.emoji_buttons:
            self.current_focus = (self.current_focus + 1) % len(self.emoji_buttons)
            self.update_focus()
        return "break"

    def prev_emoji(self, event):
        if self.emoji_buttons:
            self.current_focus = (self.current_focus - 1) % len(self.emoji_buttons)
            self.update_focus()
        return "break"

    def select_focused_emoji(self, event):
        if 0 <= self.current_focus < len(self.emoji_buttons):
            self.select_emoji(self.emoji_buttons[self.current_focus].emoji)
        return "break"

    def emoji_matches_search(self, emoji, search_term):
        # Check main name
        if fuzz.partial_ratio(search_term.lower(), emoji["name"].lower()) > 70:
            return True
        
        # Check aliases
        if "aliases" in emoji:
            for alias in emoji["aliases"]:
                if fuzz.partial_ratio(search_term.lower(), alias.lower()) > 70:
                    return True
        
        return False

    def on_search(self, *args):
        search_term = self.search_var.get()
        self.display_emojis(search_term)
        
        # Update focus to first emoji if exists
        if self.emoji_buttons:
            self.current_focus = 0
            self.update_focus()

    def clear_search(self):
        self.search_var.set("")
        self.search_entry.focus()

    def open_add_emoji(self, category=None):
        add_window = AddEmojiWindow(self, category)
        add_window.focus()

    def save_emojis(self):
        with open(self.emojis_file, 'w', encoding="utf-8") as f:
            json.dump(self.emojis, f, indent=4)

    def load_settings(self):
        default_settings = {
            "hotkey": "ctrl+shift+e",
            "start_with_windows": False,
            "minimize_to_tray": True,
            "paste_delay_ms": 100,
            "font": {
                "family": "Segoe UI",
                "size": 12
            },
            "custom_templates": [
                {
                    "name": "URL only",
                    "template": "{url}",
                    "is_default": True
                },
                {
                    "name": "Hidden character",
                    "template": "[⠀]({url})",
                    "is_default": False
                }
            ]
        }
        
        try:
            with open(self.settings_file, 'r', encoding="utf-8") as f:
                settings = json.load(f)
                # Merge with defaults to ensure all fields exist
                return {**default_settings, **settings}
        except FileNotFoundError:
            # Create settings file if it doesn't exist
            with open(self.settings_file, 'w', encoding="utf-8") as f:
                json.dump(default_settings, f, indent=4)
            return default_settings

    def save_settings(self):
        with open(self.settings_file, 'w', encoding="utf-8") as f:
            json.dump(self.settings, f)

    def show_window(self):
        def force_foreground():
            try:
                # Store the current foreground window
                self.last_active_window = win32gui.GetForegroundWindow()
                
                # Show window first
                self.deiconify()
                self.lift()
                
                # Get our window handle
                hwnd = self.winfo_id()
                
                # Try multiple focus methods
                try:
                    # Method 1: Simple Windows API call
                    win32gui.SetForegroundWindow(hwnd)
                except:
                    try:
                        # Method 2: Simulate Alt key press
                        win32api.keybd_event(0x12, 0, 0, 0)  # Alt press
                        win32gui.SetForegroundWindow(hwnd)
                        win32api.keybd_event(0x12, 0, win32con.KEYEVENTF_KEYUP, 0)  # Alt release
                    except:
                        try:
                            # Method 3: Using mouse click
                            cursor_pos = win32gui.GetCursorPos()
                            win32api.SetCursorPos((x + 10, y + 10))
                            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                            win32api.SetCursorPos(cursor_pos)
                        except:
                            pass
                
                # Force focus using Tkinter methods
                self.focus_force()
                self.search_entry.focus_force()
                
            except Exception as e:
                print(f"Focus error: {e}")
        
        # Position window near mouse cursor
        x, y = win32api.GetCursorPos()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        window_width = 300
        window_height = 400
        
        if x + window_width > screen_width:
            x = screen_width - window_width
        if y + window_height > screen_height:
            y = screen_height - window_height
        
        self.geometry(f"+{x}+{y}")
        
        # Clear previous search
        self.search_var.set("")
        
        # Force focus with a small delay
        self.after(10, force_foreground)

    def select_emoji(self, emoji):
        # Get the default template
        templates = self.settings.get("custom_templates", [])
        default_template = next(
            (t for t in templates if t.get("is_default", True)),
            templates[0] if templates else {"template": "{url}"}
        )
        
        # Format the URL using the template
        text_to_paste = default_template["template"].replace("{url}", emoji["url"])
        
        # Hide window
        self.withdraw()
        
        # Copy to clipboard
        pyperclip.copy(text_to_paste)
        
        # Add delay before paste
        time.sleep(self.settings.get("paste_delay_ms", 100) / 1000)
        
        # Restore focus and paste
        if hasattr(self, 'last_active_window'):
            try:
                # Try multiple methods to restore focus
                try:
                    # Method 1: Direct Windows API call
                    win32gui.SetForegroundWindow(self.last_active_window)
                except:
                    try:
                        # Method 2: Alt key simulation
                        win32api.keybd_event(0x12, 0, 0, 0)  # Alt press
                        win32gui.SetForegroundWindow(self.last_active_window)
                        win32api.keybd_event(0x12, 0, win32con.KEYEVENTF_KEYUP, 0)  # Alt release
                    except:
                        pass
                
                # Small delay to ensure focus is restored
                time.sleep(0.05)
                keyboard.send("ctrl+v")
            except Exception as e:
                print(f"Paste error: {e}")
                # Fallback paste method
                keyboard.send("ctrl+v")

    def open_settings(self, *args):
        settings_window = SettingsWindow(self)
        settings_window.focus()

    def center_window(self):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = 300
        window_height = 400
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"+{x}+{y}")

    def create_ui(self):
        # Configure font
        self.default_font = ctk.CTkFont(family=self.settings.get("font", {}).get("family", "Segoe UI"), 
                                      size=self.settings.get("font", {}).get("size", 12))
        
        # Main container (no padding on right side)
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=(10, 0), pady=(10, 0))
        
        # Top bar frame
        self.top_bar = ctk.CTkFrame(self.main_container)
        self.top_bar.pack(fill="x", pady=(0, 10))
        
        # Search frame (left side of top bar)
        self.search_frame = ctk.CTkFrame(self.top_bar)
        self.search_frame.pack(side="left", fill="x", expand=True)
        
        # Search entry
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.after(100, self.on_search))
        self.search_entry = ctk.CTkEntry(
            self.search_frame, 
            placeholder_text="Search emojis...",
            textvariable=self.search_var,
            font=self.default_font
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        
        # Bind Enter key to select first emoji
        self.search_entry.bind("<Return>", self.select_first_emoji)
        
        # Clear search button
        self.clear_button = ctk.CTkButton(
            self.search_frame,
            text="✕",
            width=30,
            command=self.clear_search,
            font=self.default_font
        )
        self.clear_button.pack(side="right", padx=(5, 0))
        
        # Add emoji button
        self.add_button = ctk.CTkButton(
            self.top_bar,
            text="+",
            width=30,
            command=self.open_add_emoji,
            font=self.default_font
        )
        self.add_button.pack(side="right", padx=(5, 0))
        
        # Settings button
        self.settings_button = ctk.CTkButton(
            self.top_bar,
            text="⚙",
            width=30,
            command=self.open_settings,
            font=self.default_font
        )
        self.settings_button.pack(side="right", padx=(5, 0))
        
        # Emoji display area (no padding on right side)
        self.emoji_frame = ctk.CTkScrollableFrame(self.main_container)
        self.emoji_frame.pack(fill="both", expand=True, padx=(0, 0))
        
        # Status bar
        self.status_frame = ctk.CTkFrame(self)
        self.status_frame.pack(fill="x", padx=10, pady=5)
        self.status_frame.configure(height=40)
        self.status_frame.pack_propagate(False)
        
        self.preview_label = ctk.CTkLabel(self.status_frame, text="", image=None, font=self.default_font)
        self.preview_label.pack(side="left", padx=5)
        
        self.name_label = ctk.CTkLabel(self.status_frame, text="", anchor="e", font=self.default_font)
        self.name_label.pack(side="right", padx=10)

    def select_first_emoji(self, event=None):
        if self.emoji_buttons:
            self.select_emoji(self.emoji_buttons[0].emoji)
            # Clear search after selection
            self.search_var.set("")

    def on_closing(self):
        if self.settings.get("minimize_to_tray", True):
            self.withdraw()
        else:
            self.quit_app(None, None)

    def update_font(self):
        self.default_font.configure(
            family=self.settings.get("font", {}).get("family", "Segoe UI"),
            size=self.settings.get("font", {}).get("size", 12)
        )

if __name__ == "__main__":
    app = EmojiPicker()
    app.mainloop()
