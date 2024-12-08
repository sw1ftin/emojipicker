# EmojiPicker

A lightweight desktop emoji picker for Windows with Discord-style emoji management.

## Features

- 🚀 Quick emoji access with customizable hotkey (default: Ctrl+Shift+E)
- 🔍 Fast fuzzy search
- ✨ Support for custom emojis
- 📋 Multiple paste templates
- 🖼️ Emoji preview
- 🎯 Cursor-following window
- 🎨 Customizable font
- 🔄 System tray integration
- ⌨️ Full keyboard navigation

## Installation

1. Install Python 3.8 or higher
2. Install requirements:
```bash
pip install -r requirements.txt
```
3. Run the application:
```bash
python emoji_picker.py
```

## Usage

1. Press `Ctrl+Shift+E` (default) to open the picker
2. Type to search emojis
3. Click or press Enter to select
4. Right-click on emoji for options:
   - Copy URL
   - Add alias
   - Delete emoji

## Settings

Access settings by clicking ⚙️:

- **General**
  - Hotkey configuration
  - Startup options
  - Paste delay

- **Templates**
  - URL only: `{url}`
  - Hidden character: `[⠀]({url})`
  - Add custom templates

- **Appearance**
  - Font family
  - Font size

## Compiling to EXE

1. Install PyInstaller:
```bash
pip install pyinstaller
```

2. Create the executable:
```bash
pyinstaller --noconfirm --onefile --windowed --icon "icon.ico" --add-data "icon.ico;." --name "EmojiPicker" emoji_picker.py
```

The executable will be created in the `dist` folder.

## Requirements

- Windows OS
- Python 3.8+
- Required packages (see requirements.txt)

## License

MIT License
