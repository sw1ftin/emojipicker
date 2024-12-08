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
        self.geometry("400x300")
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
        self.geometry("500x600")
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
        hotkey_frame = ctk.CTkFrame(general_frame)
        hotkey_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        hotkey_label = ctk.CTkLabel(hotkey_frame, text="Hotkey:", font=self.window_font)
        hotkey_label.pack(side="left", padx=5)
        
        self.hotkey_var = ctk.StringVar(value=self.parent.settings.get("hotkey", "ctrl+shift+e"))
        self.hotkey_entry = ctk.CTkEntry(hotkey_frame, textvariable=self.hotkey_var, font=self.window_font)
        self.hotkey_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # Startup option
        self.startup_var = ctk.BooleanVar(value=self.parent.settings.get("start_with_windows", False))
        startup_cb = ctk.CTkCheckBox(general_frame, text="Start with Windows", 
                                   variable=self.startup_var, font=self.window_font)
        startup_cb.pack(fill="x", padx=10, pady=5)
        
        # Minimize to tray option
        self.minimize_var = ctk.BooleanVar(value=self.parent.settings.get("minimize_to_tray", True))
        minimize_cb = ctk.CTkCheckBox(general_frame, text="Minimize to tray", 
                                    variable=self.minimize_var, font=self.window_font)
        minimize_cb.pack(fill="x", padx=10, pady=5)
        
        # Paste delay
        delay_frame = ctk.CTkFrame(general_frame)
        delay_frame.pack(fill="x", padx=10, pady=5)
        
        delay_label = ctk.CTkLabel(delay_frame, text="Paste delay (ms):", font=self.window_font)
        delay_label.pack(side="left", padx=5)
        
        self.delay_var = ctk.StringVar(value=str(self.parent.settings.get("paste_delay_ms", 100)))
        delay_entry = ctk.CTkEntry(delay_frame, textvariable=self.delay_var, font=self.window_font)
        delay_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # Templates Tab
        templates_frame = self.tabview.tab("Templates")
        
        # Default template selection
        default_template_frame = ctk.CTkFrame(templates_frame)
        default_template_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        default_template_label = ctk.CTkLabel(default_template_frame, text="Default Template:", font=self.window_font)
        default_template_label.pack(side="left", padx=5)
        
        self.default_template_var = ctk.StringVar(value=self.parent.settings.get("default_template", "URL Only"))
        self.default_template_menu = ctk.CTkOptionMenu(
            default_template_frame,
            variable=self.default_template_var,
            values=[template["name"] for template in self.parent.settings.get("custom_templates", [])],
            font=self.window_font
        )
        self.default_template_menu.pack(side="left", fill="x", expand=True, padx=5)
        
        # Template list
        self.template_list = []
        for template in self.parent.settings.get("custom_templates", []):
            template_frame = self.create_template_frame(templates_frame, template)
            self.template_list.append(template_frame)
        
        # Add template button
        add_template_btn = ctk.CTkButton(
            templates_frame,
            text="Add Template",
            command=self.add_template,
            font=self.window_font
        )
        add_template_btn.pack(fill="x", padx=10, pady=10)
        
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

    def create_template_frame(self, parent, template):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=10, pady=2)
        
        name_label = ctk.CTkLabel(frame, text="Name:", font=self.window_font)
        name_label.pack(side="left", padx=5)
        
        name_entry = ctk.CTkEntry(frame, placeholder_text="Template name", font=self.window_font)
        name_entry.insert(0, template["name"])
        name_entry.pack(side="left", padx=5)
        
        template_label = ctk.CTkLabel(frame, text="Template:", font=self.window_font)
        template_label.pack(side="left", padx=5)
        
        template_entry = ctk.CTkEntry(frame, placeholder_text="Template", font=self.window_font)
        template_entry.insert(0, template["template"])
        template_entry.pack(side="left", padx=5, expand=True, fill="x")
        
        delete_btn = ctk.CTkButton(
            frame,
            text="✕",
            width=30,
            command=lambda idx=len(self.template_list): self.delete_template(idx),
            font=self.window_font
        )
        delete_btn.pack(side="right", padx=5)
        
        return frame

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

    def save_settings(self):
        # Get current settings
        settings = {
            "hotkey": self.hotkey_var.get(),
            "start_with_windows": self.startup_var.get(),
            "minimize_to_tray": self.minimize_var.get(),
            "paste_delay_ms": int(self.delay_var.get()),
            "default_template": self.default_template_var.get(),
            "font": {
                "family": self.font_family_var.get(),
                "size": int(self.font_size_var.get())
            },
            "custom_templates": []
        }
        
        # Save templates
        for template_frame in self.template_list:
            name_entry = template_frame.winfo_children()[1]
            template_entry = template_frame.winfo_children()[3]
            template = {
                "name": name_entry.get(),
                "template": template_entry.get()
            }
            settings["custom_templates"].append(template)
        
        # Save to file
        with open(self.parent.settings_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        
        # Update parent settings
        old_hotkey = self.parent.settings.get("hotkey")
        self.parent.settings = settings
        
        # Update parent configuration
        if old_hotkey != settings["hotkey"]:
            self.parent.update_hotkey(settings["hotkey"])
        
        # Update font
        self.parent.default_font = ctk.CTkFont(
            family=settings["font"]["family"],
            size=settings["font"]["size"]
        )
        
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
        self.create_system_tray()
        
        # Initialize variables
        self.emoji_buttons = []
        self.current_focus = -1
        self.preview_photo = None
        
        # Register hotkey
        self.register_hotkey()
        
        # Create UI
        self.create_ui()
        
        # Center window
        self.center_window()
    
    def register_hotkey(self):
        try:
            hotkey = self.settings.get("hotkey", "ctrl+shift+e")
            keyboard.add_hotkey(hotkey, self.on_hotkey)
        except Exception as e:
            print(f"Failed to register hotkey: {e}")
    
    def unregister_hotkey(self):
        try:
            hotkey = self.settings.get("hotkey")
            if hotkey:
                keyboard.remove_hotkey(hotkey)
        except Exception as e:
            print(f"Failed to unregister hotkey: {e}")
    
    def update_hotkey(self, new_hotkey):
        self.unregister_hotkey()
        self.settings["hotkey"] = new_hotkey
        self.register_hotkey()
    
    def on_hotkey(self):
        self.toggle_window()

    def create_system_tray(self):
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

    def display_emojis(self, emojis=None):
        # Clear existing emojis
        for widget in self.emoji_frame.winfo_children():
            widget.destroy()
            
        # Calculate grid layout
        max_cols = 5
        
        # Get all emojis from the list
        all_emojis = emojis if emojis is not None else self.emojis.get("emojis", [])
        
        # Display emojis in grid
        row = 0
        col = 0
        self.emoji_buttons = []
        
        for emoji in all_emojis:
            if isinstance(emoji, str):
                continue  # Skip if emoji is just a string
                
            photo = self.load_emoji_image(emoji["url"])
            
            button = ctk.CTkButton(
                self.emoji_frame,
                text="",
                image=photo,
                width=50,
                height=50,
                command=lambda e=emoji: self.select_emoji(e)
            )
            button.image = photo
            button.emoji = emoji  # Store emoji data in button
            
            # Bind events
            button.bind("<Enter>", lambda e, em=emoji: self.show_emoji_preview(em))
            button.bind("<Leave>", self.hide_emoji_preview)
            button.bind("<Button-3>", lambda e, em=emoji, b=button: self.show_context_menu(e, em, b))
            
            button.grid(row=row, column=col, padx=2, pady=2)
            self.emoji_buttons.append(button)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # Add "+" button at the end if not searching
        if emojis is None:
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
        if self.emoji_buttons:
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
        try:
            # Reset all buttons to default color
            for i, button in enumerate(self.emoji_buttons):
                try:
                    if button.winfo_exists():  # Check if button still exists
                        button.configure(fg_color=("gray70", "gray30"))
                except Exception:
                    continue

            # Set focused button color
            if 0 <= self.current_focus < len(self.emoji_buttons):
                try:
                    button = self.emoji_buttons[self.current_focus]
                    if button.winfo_exists():  # Check if button still exists
                        button.configure(fg_color=("gray75", "gray25"))
                except Exception:
                    pass
        except Exception as e:
            print(f"Error updating focus: {e}")
            
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
        search_text = self.search_var.get().lower()
        
        # Clear previous results
        for widget in self.emoji_frame.winfo_children():
            widget.destroy()
        
        if not search_text:
            self.display_emojis()
            return
            
        # Convert search text to both layouts
        en_chars = "qwertyuiop[]asdfghjkl;'zxcvbnm,.`"
        ru_chars = "йцукенгшщзхъфывапролджэячсмитьбюё"
        
        en_to_ru = str.maketrans(en_chars, ru_chars)
        ru_to_en = str.maketrans(ru_chars, en_chars)
        
        # Try both layouts
        search_ru = search_text.translate(en_to_ru) if all(c in en_chars for c in search_text.lower()) else search_text
        search_en = search_text.translate(ru_to_en) if all(c in ru_chars for c in search_text.lower()) else search_text
        
        matching_emojis = []
        for emoji in self.emojis.get("emojis", []):
            if isinstance(emoji, str):
                continue  # Skip if emoji is just a string
                
            name = emoji.get("name", "").lower()
            aliases = [alias.lower() for alias in emoji.get("aliases", [])]
            
            # Check both layouts
            if any(search in name for search in [search_text, search_ru, search_en]) or \
               any(any(search in alias for search in [search_text, search_ru, search_en]) for alias in aliases):
                matching_emojis.append(emoji)
        
        self.display_emojis(matching_emojis)
        
        # Update focus to first emoji if exists
        if self.emoji_buttons:
            self.current_focus = 0
            self.update_focus()

    def clear_search(self):
        self.search_var.set("")
        self.search_entry.focus()
        self.display_emojis()

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
            "default_template": "URL Only",
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

    def toggle_window(self):
        if self.winfo_viewable():
            if self.settings.get("minimize_to_tray", True):
                self.withdraw()
            else:
                self.iconify()
            
            # Store current window for later focus
            try:
                self.last_active_window = win32gui.GetForegroundWindow()
            except:
                self.last_active_window = None
        else:
            self.show_window()
    
    def show_window(self):
        try:
            # Show window
            self.deiconify()
            
            # Position window near cursor first
            x, y = win32api.GetCursorPos()
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            
            # Window dimensions
            window_width = 330
            window_height = 400
            
            # Adjust position to keep window on screen
            if x + window_width > screen_width:
                x = screen_width - window_width - 10
            if y + window_height > screen_height:
                y = screen_height - window_height - 10
                
            # Ensure window is not too close to screen edges
            x = max(10, min(x, screen_width - window_width - 10))
            y = max(10, min(y, screen_height - window_height - 10))
            
            # Set window position immediately
            self.geometry(f"+{x}+{y}")
            
            # Set always on top
            self.attributes('-topmost', True)
            self.lift()
            
            # Clear search
            if hasattr(self, 'search_var'):
                self.search_var.set("")
            
            # Force focus with multiple methods
            def force_focus():
                try:
                    hwnd = self.winfo_id()
                    
                    # Try multiple focus methods
                    methods = [
                        lambda: win32gui.SetForegroundWindow(hwnd),
                        lambda: (
                            win32api.keybd_event(0x12, 0, 0, 0),
                            win32gui.SetForegroundWindow(hwnd),
                            win32api.keybd_event(0x12, 0, win32con.KEYEVENTF_KEYUP, 0)
                        ),
                        lambda: win32gui.BringWindowToTop(hwnd)
                    ]
                    
                    for method in methods:
                        try:
                            method()
                            if win32gui.GetForegroundWindow() == hwnd:
                                break
                        except:
                            continue
                        
                    self.focus_force()
                    if hasattr(self, 'search_entry'):
                        self.search_entry.focus_force()
                        
                except Exception as e:
                    print(f"Focus error: {e}")
            
            # Schedule focus forcing
            self.after(50, force_focus)
            
            # Update focus only if we have buttons
            if hasattr(self, 'emoji_buttons') and self.emoji_buttons:
                self.current_focus = 0
                self.after(100, self.update_focus)  # Delay focus update
                
        except Exception as e:
            print(f"Error showing window: {e}")
            
    def select_emoji(self, emoji):
        # Get the selected template
        template_name = self.settings.get("default_template", "URL Only")
        template = next(
            (t["template"] for t in self.settings.get("custom_templates", []) if t["name"] == template_name),
            "{url}"  # Default template if not found
        )
        
        # Format the emoji text
        emoji_text = template.replace("{url}", emoji["url"])
        
        try:
            # Copy to clipboard
            pyperclip.copy(emoji_text)
            
            # Hide window
            self.withdraw()
            
            # Restore previous window focus
            if hasattr(self, 'last_active_window') and self.last_active_window:
                try:
                    win32gui.SetForegroundWindow(self.last_active_window)
                except:
                    pass
            
            # Wait for focus restoration
            self.after(50, lambda: self.paste_with_delay())
            
        except Exception as e:
            print(f"Error copying emoji: {e}")
    
    def paste_with_delay(self):
        try:
            # Get paste delay from settings
            delay_ms = self.settings.get("paste_delay_ms", 100)
            
            # Schedule paste after delay
            self.after(delay_ms, lambda: keyboard.send('ctrl+v'))
        except Exception as e:
            print(f"Error pasting: {e}")
    
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
