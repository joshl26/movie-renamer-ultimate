# Movie Renamer Ultimate - Open Source Edition

A Python-based desktop application for automatically renaming movie files using TMDB (The Movie Database) metadata.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

![Movie Renamer Ultimate - Dark Theme](pics/Main%20app%20window%20-%20dark%20theme.PNG)

## Features

✅ **Core Functionality:**

- Automatic movie file and folder renaming using TMDB metadata
- Smart filename parsing (removes quality markers, release groups, etc.)
- Handles Roman numerals in sequel titles (Rocky IV, Blade II)
- Drag-and-drop support for files and folders
- Multi-threaded processing for large libraries
- Dark/light theme support

✅ **TMDB Integration:**

- Intelligent search with multiple fallback strategies
- Manual override - double-click any preview to select different TMDB match
- Caching for faster re-processing

✅ **User Interface:**

- Filter by status (Found/Not Found)
- Search bar for quick filtering
- Live preview before renaming
- Customizable naming patterns
- Multi-language support

## Screenshots

![Rename Preview](pics/main%20app%20window%20-%20rename%20preview%20before_after.PNG)
_Before/after rename preview with full TMDB metadata_

![Settings Panel](pics/main%20app%20window%20-%20settings%20panel.PNG)
_Settings panel with theme, language, and API key configuration_

![Successful Rename](pics/main%20app%20window%20-%20successful%20rename%20completion%20dialog.PNG)
_Rename completion dialog_

## What's NOT Included (Open Source Version)

This is a simplified version focused on core rename functionality. For advanced features, check out the **[full version at movie-renamer.joshlehman.ca](https://movie-renamer.joshlehman.ca)**:

- ❌ NFO file generation for media centers
- ❌ Automatic poster and fanart downloads
- ❌ Kodi library integration
- ❌ Backup system with undo functionality
- ❌ Folder cleaning tools
- ❌ Processing statistics
- ❌ Operation history logging

## Installation

### Prerequisites

- Python 3.8 or higher
- TMDB API key (free - get it at [themoviedb.org/settings/api](https://www.themoviedb.org/settings/api))

### Steps

1. **Clone the repository:**

```bash
   git clone https://github.com/joshl26/movie-renamer-ultimate.git
   cd movie-renamer-ultimate
```

2. **Install dependencies:**

```bash
   pip install -r requirements_opensource.txt
```

3. **Configure your TMDB API key:**

   Create a `.env` file in the project directory:

```bash
   cp .env.example .env
```

Edit `.env` and add your API key:

```
   TMDB_API_KEY=your_actual_api_key_here
```

4. **Run the application:**

```bash
   python main.py
```

## Usage

### Basic Workflow

1. **Load Movies:**
   - Click "Browse Files" to select individual video files
   - Click "Browse Folder" to scan an entire directory
   - Or drag-and-drop files/folders directly into the window

2. **Review Matches:**
   - Green entries = successful TMDB match
   - Red entries = no match found
   - Double-click any entry to manually select the correct movie

3. **Apply Renaming:**
   - Click "Apply Renaming" to process all matched files
   - Files and their parent folders will be renamed according to your pattern

### Supported File Formats

- `.mp4` `.mkv` `.avi` `.mov` `.flv`

### Naming Patterns

Customize the output format in Settings:

- `{title} ({year})` → `The Dark Knight (2008).mkv`
- `{title} - {year}` → `The Dark Knight - 2008.mkv`

Available variables: `{title}`, `{year}`

## Example

**Before:**

```
The.Dark.Knight.2008.1080p.BluRay.x264-YIFY/
└── The.Dark.Knight.2008.1080p.BluRay.x264-YIFY.mkv
```

**After:**

```
The Dark Knight (2008)/
└── The Dark Knight (2008).mkv
```

## Filename Parsing

The app intelligently cleans filenames by removing:

- Quality markers (1080p, 4K, BluRay, etc.)
- Codec information (x264, HEVC, etc.)
- Release groups (YIFY, RARBG, etc.)
- Audio formats (AAC, DTS, etc.)

It also handles:

- Year extraction from filenames
- Roman numerals in titles (Rocky IV → searches both "Rocky IV" and "Rocky 4")
- Multi-word titles with separators

## Configuration

### Settings (accessible via Settings button)

- **TMDB API Key:** Your API key for movie lookups
- **Naming Pattern:** Output filename format
- **Language:** Metadata language (en, es, fr, de, pt, ja, zh)
- **Dark Mode:** Toggle light/dark theme

### Persistent Data

Configuration files stored in your home directory:

- `~/.movie_renamer_config` - Last used folder
- `~/.movie_renamer_settings.json` - App settings
- `~/.movie_renamer_theme` - Theme preference
- `~/.movie_renamer_window` - Window position/size

## Keyboard Shortcuts

- `Ctrl+Enter` - Apply renaming
- `Ctrl+O` - Browse folder
- `Ctrl+S` - Open settings

## Troubleshooting

### "API key not configured"

- Make sure your `.env` file exists and contains a valid TMDB API key
- Restart the application after adding the key

### "No video files found"

- Ensure files have supported extensions (mp4, mkv, avi, mov, flv)
- Check that files aren't locked by another application
- On Windows, try running as administrator

### "Permission denied"

- Run the application with appropriate file system permissions
- Check that files aren't locked by another application
- On Windows, try running as administrator

### "No TMDB results found"

- Verify internet connection
- Check that the filename contains recognizable movie information
- Try manually selecting the correct movie (double-click the entry)

## Development

Built with:

- **Python 3.x** - Core application
- **tkinter** - GUI framework
- **tkinterdnd2** - Drag-and-drop support
- **requests** - TMDB API client
- **python-dotenv** - Environment configuration

## Contributing

Contributions are welcome! Feel free to:

- Report bugs
- Suggest features
- Submit pull requests

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Full Version

Want more features? The **[complete version](https://movie-renamer.joshlehman.ca)** includes:

- 🎬 NFO file generation (Kodi/Plex/Jellyfin compatible)
- 🖼️ Automatic poster and fanart downloads
- 🔄 Kodi library integration
- 💾 Backup system with one-click undo
- 🧹 Folder cleaning tools
- 📊 Processing statistics
- 📝 Full operation history

Available at **[movie-renamer.joshlehman.ca](https://movie-renamer.joshlehman.ca)** - $19.99 one-time purchase.

## Support

- **Issues:** [GitHub Issues](https://github.com/joshl26/movie-renamer-ultimate/issues)
- **Discussions:** [GitHub Discussions](https://github.com/joshl26/movie-renamer-ultimate/discussions)

---

**Note:** This project uses The Movie Database (TMDB) API but is not endorsed or certified by TMDB.

<p align="center">
  <a href="https://www.themoviedb.org/">
    <img src="https://www.themoviedb.org/assets/2/v4/logos/v2/blue_short-8e7b30f73a4020692ccca9c88bafe5dcb6f8a62a4c6bc55cd9ba82bb2cd95f6c.svg" width="150">
  </a>
</p>
