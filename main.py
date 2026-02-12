import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import requests
from pathlib import Path
import threading
import json
import pickle

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("[DEBUG] python-dotenv not installed. Install with: pip install python-dotenv")

class MovieRenamer:
    def __init__(self, root, api_key):
        self.root = root
        self.root.title("Movie Renamer Ultimate - Open Source Edition")
        self.root.geometry("1200x800")
        self.api_key = api_key
        self.tmdb_base = "https://api.themoviedb.org/3"
        self.preview_data = []

        # Load configurations
        self.config_file = os.path.join(os.path.expanduser("~"), ".movie_renamer_config")
        self.settings_file = os.path.join(os.path.expanduser("~"), ".movie_renamer_settings.json")
        self.window_state_file = os.path.join(os.path.expanduser("~"), ".movie_renamer_window")

        self.last_folder = self.load_last_folder()

        # Processing state
        self.processing = False

        # Settings
        self.dark_mode = tk.BooleanVar(value=True)
        self.language = tk.StringVar(value="en")
        self.naming_pattern = tk.StringVar(value="{title} ({year})")

        self.load_settings()
        self.setup_theme()

        # TMDB cache for faster processing
        self.tmdb_cache = {}

        # Build UI
        self.setup_ui()
        self.load_window_state()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_theme(self):
        """Setup dark/light theme"""
        # Dark theme colors
        self.dark_bg = "#1e1e1e"
        self.dark_fg = "#ffffff"
        self.dark_listbox_bg = "#2d2d2d"
        self.dark_button_bg = "#0d47a1"
        self.dark_button_fg = "#ffffff"
        self.dark_entry_bg = "#3d3d3d"
        self.dark_entry_fg = "#ffffff"

        # Light theme colors
        self.light_bg = "#f0f0f0"
        self.light_fg = "#000000"
        self.light_listbox_bg = "#ffffff"
        self.light_button_bg = "#0d47a1"
        self.light_button_fg = "#ffffff"
        self.light_entry_bg = "#ffffff"
        self.light_entry_fg = "#000000"

        # Setup ttk styles for scrollbar and other widgets
        self.setup_styles()

        # Load theme preference
        self.load_theme_preference()
        self.apply_theme()

    def setup_styles(self):
        """Setup ttk styles for dark mode"""
        style = ttk.Style()

        # Dark scrollbar style
        style.theme_use('clam')
        style.configure('Dark.Vertical.TScrollbar',
            background="#3d3d3d",
            troughcolor="#1e1e1e",
            bordercolor="#1e1e1e",
            lightcolor="#3d3d3d",
            darkcolor="#2d2d2d",
            arrowcolor="#ffffff"
        )

        # Light scrollbar style
        style.configure('Light.Vertical.TScrollbar',
            background="#e0e0e0",
            troughcolor="#f0f0f0",
            bordercolor="#f0f0f0",
            lightcolor="#f0f0f0",
            darkcolor="#e0e0e0",
            arrowcolor="#000000"
        )

    def load_theme_preference(self):
        """Load saved theme preference"""
        try:
            theme_file = os.path.join(os.path.expanduser("~"), ".movie_renamer_theme")
            if os.path.exists(theme_file):
                with open(theme_file, 'r') as f:
                    self.dark_mode.set(f.read().strip() == "dark")
        except:
            self.dark_mode.set(True)

    def save_theme_preference(self):
        """Save theme preference"""
        try:
            theme_file = os.path.join(os.path.expanduser("~"), ".movie_renamer_theme")
            with open(theme_file, 'w') as f:
                f.write("dark" if self.dark_mode.get() else "light")
        except:
            pass

    def apply_status_color(self):
        """Apply accessible status text color based on theme"""
        if not hasattr(self, 'status_label'):
            return  # Label not created yet

        if self.dark_mode.get():
            # Light gray for dark theme (high contrast)
            self.status_label.config(fg="#e0e0e0")
        else:
            # Dark blue for light theme (high contrast)
            self.status_label.config(fg="#003d99")

    def apply_theme(self):
        """Apply theme colors"""
        if self.dark_mode.get():
            self.root.configure(bg=self.dark_bg)
        else:
            self.root.configure(bg=self.light_bg)
        self.apply_status_color()
        self.save_theme_preference()

    def get_colors(self):
        """Get current theme colors"""
        if self.dark_mode.get():
            return {
                'bg': self.dark_bg,
                'fg': self.dark_fg,
                'listbox_bg': self.dark_listbox_bg,
                'button_bg': self.dark_button_bg,
                'button_fg': self.dark_button_fg,
                'entry_bg': self.dark_entry_bg,
                'entry_fg': self.dark_entry_fg
            }
        else:
            return {
                'bg': self.light_bg,
                'fg': self.light_fg,
                'listbox_bg': self.light_listbox_bg,
                'button_bg': self.light_button_bg,
                'button_fg': self.light_button_fg,
                'entry_bg': self.light_entry_bg,
                'entry_fg': self.light_entry_fg
            }

    def setup_drag_drop(self):
        """Setup drag and drop support"""
        try:
            from tkinterdnd2 import DND_FILES
            print("[DEBUG] Setting up drag & drop...")

            # Register drop target on root window
            self.root.drop_target_register(DND_FILES)
            print("[DEBUG] Drop target registered")

            # Bind drop event
            self.root.dnd_bind('<<Drop>>', self.on_drop)
            print("[DEBUG] Drag & drop enabled - ready for files!")

        except ImportError:
            print("[DEBUG] tkinterdnd2 not installed - drag & drop disabled")
            print("[DEBUG] Install with: pip install tkinterdnd2")
        except AttributeError as e:
            print(f"[DEBUG] Root is not TkinterDnD widget: {e}")
            print("[DEBUG] Drag & drop will not work")
        except Exception as e:
            print(f"[DEBUG] Drag & drop setup error: {e}")

    def on_drop(self, event):
        """Handle drag & drop files"""
        print(f"[DEBUG] Drop event triggered: {event}")
        try:
            if not event or not event.data:
                print("[DEBUG] No data in drop event")
                return

            print(f"[DEBUG] Drop data type: {type(event.data)}")
            print(f"[DEBUG] Drop data: {event.data}")

            # Handle both Windows and Unix path formats
            if isinstance(event.data, str):
                # Try different splitting methods
                if '{' in event.data:
                    files = event.data.split('} {')
                    files = [f.strip('{}') for f in files]
                else:
                    files = event.data.split()
            else:
                files = event.data

            print(f"[DEBUG] Parsed files: {files}")

            clean_files = []
            for f in files:
                # Remove curly braces and quotes
                f = f.strip('{}').strip('"\'').strip()
                print(f"[DEBUG] Checking file: {f}")
                if os.path.exists(f):
                    clean_files.append(f)
                    print(f"[DEBUG] Path exists: {f}")

            # Handle both files and folders
            video_files = []
            for f in clean_files:
                if os.path.isfile(f) and f.lower().endswith(('.mp4', '.mkv', '.avi', '.mov', '.flv')):
                    video_files.append(f)
                    print(f"[DEBUG] Added video file: {f}")
                elif os.path.isdir(f):
                    # Recursively find video files in dropped folder
                    print(f"[DEBUG] Scanning folder for videos: {f}")
                    for ext in ('mp4', 'mkv', 'avi', 'mov', 'flv'):
                        found = list(Path(f).glob(f'**/*.{ext}'))
                        found.extend(list(Path(f).glob(f'**/*.{ext.upper()}')))
                        for vf in found:
                            video_files.append(str(vf))
                            print(f"[DEBUG] Found video: {vf}")

            video_files = list(set(video_files))  # Remove duplicates

            if video_files:
                print(f"[DEBUG] Processing {len(video_files)} video file(s)")
                self.process_files(video_files)
            else:
                print("[DEBUG] No video files found in dropped items")
                messagebox.showwarning("No Videos", "No video files found in dropped folder")

        except Exception as e:
            print(f"[DEBUG] Drag & drop error: {e}")
            import traceback
            traceback.print_exc()

    def setup_ui(self):
        """Setup the user interface"""
        colors = self.get_colors()

        # Setup drag and drop
        self.setup_drag_drop()

        # Top menu
        menu_frame = tk.Frame(self.root, bg=colors['bg'])
        menu_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(menu_frame, text="Select Movie Files or Folder:", bg=colors['bg'], fg=colors['fg']).pack(anchor="w")

        button_frame = tk.Frame(self.root, bg=colors['bg'])
        button_frame.pack(fill="x", padx=10, pady=3)

        # Simplified buttons - only core functionality
        buttons = [
            ("Browse Files", self.browse_files, "Open individual video files"),
            ("Browse Folder", self.browse_folder, "Scan entire folder for videos"),
            ("Settings", self.show_settings, "Configure app settings"),
            ("Clear", self.clear, "Clear preview list"),
            ("Exit", self.on_closing, "Exit application"),
        ]

        for text, cmd, tooltip in buttons:
            btn = tk.Button(button_frame, text=text, command=cmd, width=12, bg=colors['button_bg'], fg=colors['button_fg'])
            btn.pack(side="left", padx=2)
            self.create_tooltip(btn, tooltip)

        # Status bar
        self.status = tk.StringVar(value="Ready")
        status_label = tk.Label(self.root, textvariable=self.status, font=("Arial", 10), bg=colors['bg'])
        status_label.pack(anchor="w", padx=10, pady=5)
        self.status_label = status_label
        self.apply_status_color()

        # Progress bar
        self.progress = ttk.Progressbar(self.root, mode='determinate')
        self.progress.pack(fill="x", padx=10, pady=5)

        # Filter frame
        filter_frame = tk.Frame(self.root, bg=colors['bg'])
        filter_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(filter_frame, text="Filter:", bg=colors['bg'], fg=colors['fg']).pack(side="left", padx=5)

        self.filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var, values=["All", "Not Found", "Found"], width=15, state="readonly")
        filter_combo.pack(side="left", padx=5)
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())

        tk.Label(filter_frame, text="Search:", bg=colors['bg'], fg=colors['fg']).pack(side="left", padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.apply_filters())
        search_entry = tk.Entry(filter_frame, textvariable=self.search_var, bg=colors['entry_bg'], fg=colors['entry_fg'], width=30)
        search_entry.pack(side="left", fill="x", expand=True, padx=5)

        # Preview listbox
        tk.Label(self.root, text="Preview - Double-click to override TMDB match:", bg=colors['bg'], fg=colors['fg']).pack(anchor="w", padx=10, pady=(10, 5))
        frame = tk.Frame(self.root, bg=colors['bg'])
        frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Use ttk scrollbar with theming
        scrollbar_style = 'Dark.Vertical.TScrollbar' if self.dark_mode.get() else 'Light.Vertical.TScrollbar'
        scrollbar = ttk.Scrollbar(frame, style=scrollbar_style)
        scrollbar.pack(side="right", fill="y")

        self.preview_list = tk.Listbox(frame, yscrollcommand=scrollbar.set, font=("Courier", 9), bg=colors['listbox_bg'], fg=colors['fg'])
        self.preview_list.pack(side="left", fill="both", expand=True)
        self.preview_list.bind('<Double-Button-1>', self.on_preview_double_click)
        scrollbar.config(command=self.preview_list.yview)

        # Buttons
        button_frame = tk.Frame(self.root, bg=colors['bg'])
        button_frame.pack(pady=10)

        apply_btn = tk.Button(button_frame, text="Apply Renaming", command=self.apply, bg="green", fg="white")
        apply_btn.pack(side="left", padx=5)
        self.create_tooltip(apply_btn, "Process and rename selected movies (Ctrl+Enter)")
        self.apply_btn = apply_btn

        clear_btn = tk.Button(button_frame, text="Clear", command=self.clear, bg=colors['button_bg'], fg=colors['button_fg'])
        clear_btn.pack(side="left", padx=5)
        self.create_tooltip(clear_btn, "Clear preview list")
        self.clear_btn = clear_btn

        exit_btn = tk.Button(button_frame, text="Exit", command=self.on_closing, bg=colors['button_bg'], fg=colors['button_fg'])
        exit_btn.pack(side="left", padx=5)
        self.exit_btn = exit_btn

        # Bind keyboard shortcuts
        self.root.bind('<Control-Return>', lambda e: self.apply())
        self.root.bind('<Control-o>', lambda e: self.browse_folder())
        self.root.bind('<Control-s>', lambda e: self.show_settings())

    def create_tooltip(self, widget, text):
        """Create tooltip for widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, background="lightyellow", relief=tk.SOLID, borderwidth=1, font=("Arial", 9))
            label.pack()
            widget.tooltip = tooltip

        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip

        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)

    def load_window_state(self):
        """Load saved window position and size"""
        try:
            if os.path.exists(self.window_state_file):
                with open(self.window_state_file, 'rb') as f:
                    state = pickle.load(f)
                    self.root.geometry(f"{state['width']}x{state['height']}+{state['x']}+{state['y']}")
        except:
            pass

    def save_window_state(self):
        """Save window position and size"""
        try:
            state = {
                'width': self.root.winfo_width(),
                'height': self.root.winfo_height(),
                'x': self.root.winfo_x(),
                'y': self.root.winfo_y()
            }
            with open(self.window_state_file, 'wb') as f:
                pickle.dump(state, f)
        except:
            pass

    def apply_filters(self):
        """Apply search and status filters"""
        search_term = self.search_var.get().lower()
        filter_status = self.filter_var.get()

        self.preview_list.delete(0, tk.END)

        for filepath, new_name, tmdb_data, status in self.preview_data:
            # Apply status filter
            if filter_status == "Not Found" and status != "not_found":
                continue
            if filter_status == "Found" and status != "found":
                continue

            # Apply search filter
            if search_term:
                if not (search_term in new_name.lower() or
                        search_term in tmdb_data['title'].lower() or
                        search_term in os.path.basename(filepath).lower()):
                    continue

            self.display_preview_item(filepath, new_name, tmdb_data, status)

    def display_preview_item(self, filepath, new_name, tmdb_data, status="found"):
        """Display a single preview item"""
        filename = os.path.basename(filepath)
        sanitized_folder = self.sanitize_filename(f"{tmdb_data['title']} ({tmdb_data['year']})")

        self.preview_list.insert(tk.END, "=" * 80)
        self.preview_list.insert(tk.END, f"OLD: {filename}")
        self.preview_list.insert(tk.END, f"NEW: {new_name}")
        self.preview_list.insert(tk.END, f"FOLDER: {sanitized_folder}/")
        self.preview_list.insert(tk.END, "")

    def show_settings(self):
        """Show settings dialog"""
        settings = tk.Toplevel(self.root)
        settings.title("Settings")
        settings.geometry("450x400")
        colors = self.get_colors()
        settings.configure(bg=colors['bg'])

        # Create scrollable frame
        canvas = tk.Canvas(settings, bg=colors['bg'], highlightthickness=0)
        scrollbar_style = 'Dark.Vertical.TScrollbar' if self.dark_mode.get() else 'Light.Vertical.TScrollbar'
        scrollbar = ttk.Scrollbar(settings, orient="vertical", command=canvas.yview, style=scrollbar_style)
        scrollable_frame = tk.Frame(canvas, bg=colors['bg'])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Theme
        tk.Label(scrollable_frame, text="Appearance:", font=("Arial", 10, "bold"), bg=colors['bg'], fg=colors['fg']).pack(anchor="w", padx=10, pady=(10, 5))
        tk.Checkbutton(scrollable_frame, text="Dark Mode", variable=self.dark_mode, bg=colors['bg'], fg=colors['fg']).pack(anchor="w", padx=10, pady=2)

        # API Key
        tk.Label(scrollable_frame, text="TMDB API Key:", font=("Arial", 10, "bold"), bg=colors['bg'], fg=colors['fg']).pack(anchor="w", padx=10, pady=(15, 5))
        api_key_var = tk.StringVar(value=self.api_key)
        tk.Entry(scrollable_frame, textvariable=api_key_var, width=50, show="*", bg=colors['entry_bg'], fg=colors['entry_fg']).pack(padx=10, pady=5)
        tk.Label(scrollable_frame, text="Get at: themoviedb.org/settings/api", font=("Courier", 8), fg="gray", bg=colors['bg']).pack(anchor="w", padx=10)

        # Naming Pattern
        tk.Label(scrollable_frame, text="Naming Pattern:", font=("Arial", 10, "bold"), bg=colors['bg'], fg=colors['fg']).pack(anchor="w", padx=10, pady=(15, 5))
        tk.Entry(scrollable_frame, textvariable=self.naming_pattern, width=50, bg=colors['entry_bg'], fg=colors['entry_fg']).pack(padx=10, pady=5)
        tk.Label(scrollable_frame, text="Available: {title}, {year}", font=("Courier", 8), fg="gray", bg=colors['bg']).pack(anchor="w", padx=10)

        # Language
        tk.Label(scrollable_frame, text="Language:", font=("Arial", 10, "bold"), bg=colors['bg'], fg=colors['fg']).pack(anchor="w", padx=10, pady=(15, 5))
        lang_combo = ttk.Combobox(scrollable_frame, textvariable=self.language, values=["en", "es", "fr", "de", "pt", "ja", "zh"])
        lang_combo.pack(padx=10, pady=5)

        # Buttons
        button_frame = tk.Frame(scrollable_frame, bg=colors['bg'])
        button_frame.pack(pady=20)

        def save_settings():
            self.api_key = api_key_var.get()
            if not self.api_key:
                messagebox.showerror("Error", "API key cannot be empty")
                return

            self.save_settings()
            messagebox.showinfo("Saved", "Settings saved successfully")
            settings.destroy()

        tk.Button(button_frame, text="Save", command=save_settings, bg="green", fg="white").pack(side="left", padx=5)

    def on_preview_double_click(self, event):
        """Handle double-click on preview"""
        selection = self.preview_list.curselection()
        if selection:
            index = selection[0]
            movie_index = 0
            line_count = 0
            for i, item in enumerate(self.preview_data):
                line_count += 5  # Simplified preview has 5 lines per item
                if index < line_count:
                    movie_index = i
                    break

            if movie_index < len(self.preview_data):
                self.show_tmdb_override(movie_index)

    def show_tmdb_override(self, movie_index):
        """Show TMDB override dialog"""
        filepath, current_name, tmdb_result, _ = self.preview_data[movie_index]
        filename = os.path.basename(filepath)
        name, ext = os.path.splitext(filename)

        # Extract year from parentheses first (highest priority)
        year_match = re.search(r'\((\d{4})\)', name)
        year = year_match.group(1) if year_match else None

        # If no year in parentheses, look for standalone 4-digit year (1900-2100)
        if not year:
            year_match = re.search(r'(?:^|\D)([12]\d{3})(?:\D|$)', name)
            if year_match:
                year = year_match.group(1)

        # Clean the name step by step
        clean_name = re.sub(r'\(\d{4}\)', '', name).strip()  # Remove (YYYY)
        clean_name = re.sub(r'[\[\{].*?[\]\}]', '', clean_name).strip()  # Remove [brackets] and {braces}

        # Remove year numbers if not captured above (1900-2100)
        clean_name = re.sub(r'\b[12]\d{3}\b', '', clean_name).strip()

        # Remove common usernames/release groups (must be preceded by separator)
        clean_name = re.sub(r'[\._-](rarbg|anoXmous|scene|proper|rerip|remux)(?:\.|_|-|$)', ' ', clean_name, flags=re.IGNORECASE).strip()

        # Remove quality markers and common release tags
        quality_markers = r'\b(1080p|720p|480p|2160p|4k|uhd|bluray|blu-ray|bdrip|webrip|hdtv|dvdrip|h\.?264|x\.?264|hevc|h\.?265|x\.?265|aac|ac3|dts|amd64|x86_64|10bit|avc|vc1|mpeg2|aiff|flac|opus|vorbis|mp3|eac3|truehd|dts-hd|atmos|imax|remastered|extended|directors?cut|uncut|proper|rerip|remux|pdtv|dsr|ts|tc|r5|dvdscr|brrip|xvid|divx|h264|x264|web|web-dl|web-rip)\b'
        clean_name = re.sub(quality_markers, '', clean_name, flags=re.IGNORECASE).strip()

        clean_name = re.sub(r'[._-]+', ' ', clean_name).strip()  # Convert dots/dashes/underscores to spaces
        clean_name = ' '.join(clean_name.split())  # Collapse multiple spaces

        try:
            url = f"{self.tmdb_base}/search/movie"
            params = {
                'api_key': self.api_key,
                'query': clean_name,
                'page': 1,
                'language': self.language.get()
            }
            if year:
                params['year'] = year

            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            if not data['results']:
                messagebox.showwarning("No Results", "No TMDB results found")
                return

            override_window = tk.Toplevel(self.root)
            override_window.title(f"Select Correct Movie: {filename}")
            override_window.geometry("600x400")

            tk.Label(override_window, text="Double-click to select:").pack(anchor="w", padx=10, pady=5)

            listbox = tk.Listbox(override_window)
            listbox.pack(fill="both", expand=True, padx=10, pady=5)

            results = []
            for result in data['results'][:10]:
                year_str = result['release_date'][:4] if result.get('release_date') else 'N/A'
                rating = result.get('vote_average', 0)
                text = f"{result['title']} ({year_str}) - Rating: {rating}/10"
                listbox.insert("end", text)
                results.append(result)

            def on_select(event=None):
                selection = listbox.curselection()
                if selection:
                    selected = results[selection[0]]
                    new_result = {
                        'title': selected['title'],
                        'year': selected['release_date'][:4] if selected.get('release_date') else 'UNKNOWN',
                        'id': selected['id'],
                    }
                    self.preview_data[movie_index] = (filepath, self.build_filename(new_result, ext), new_result, "found")
                    override_window.destroy()
                    self.apply_filters()

            listbox.bind('<Double-Button-1>', on_select)
            tk.Button(override_window, text="Select", command=on_select).pack(pady=10)

        except Exception as e:
            messagebox.showerror("Error", f"Error fetching TMDB results: {e}")

    def load_last_folder(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    folder = f.read().strip()
                    if os.path.isdir(folder):
                        return folder
        except:
            pass
        return ""

    def save_last_folder(self, folder):
        try:
            with open(self.config_file, 'w') as f:
                f.write(folder)
        except:
            pass

    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    self.naming_pattern.set(data.get('naming_pattern', "{title} ({year})"))
                    self.language.set(data.get('language', "en"))
        except:
            pass

    def save_settings(self):
        try:
            data = {
                'naming_pattern': self.naming_pattern.get(),
                'language': self.language.get()
            }
            with open(self.settings_file, 'w') as f:
                json.dump(data, f)
        except:
            pass

    def sanitize_filename(self, filename):
        return re.sub(r'[<>:"/\\|?*]', '', filename).strip()

    def convert_roman_numerals(self, text):
        """Convert Roman numerals to Arabic numerals for better TMDB matching"""
        roman_map = {
            'IV': '4', 'IX': '9', 'XL': '40', 'XC': '90', 'CD': '400', 'CM': '900',
            'I': '1', 'V': '5', 'X': '10', 'L': '50', 'C': '100', 'D': '500', 'M': '1000'
        }

        # Replace longer numerals first to avoid partial replacements
        for roman, num in sorted(roman_map.items(), key=lambda x: len(x[0]), reverse=True):
            # Match whole words only (surrounded by spaces or word boundaries)
            text = re.sub(r'\b' + roman + r'\b', num, text, flags=re.IGNORECASE)

        return text

    def build_filename(self, tmdb_data, ext):
        pattern = self.naming_pattern.get()
        filename = pattern.format(
            title=self.sanitize_filename(tmdb_data['title']),
            year=tmdb_data['year']
        )
        return f"{filename}{ext}"

    def browse_files(self):
        files = filedialog.askopenfilenames(
            title="Select Movie Files",
            filetypes=[("Video Files", "*.mp4 *.mkv *.avi *.mov *.flv")],
            initialdir=self.last_folder if self.last_folder else None
        )
        if files:
            # Get the parent folder of the first selected file and set it as default
            selected_folder = os.path.dirname(files[0])
            self.last_folder = selected_folder
            self.save_last_folder(selected_folder)
            self.process_files(list(files))

    def browse_folder(self):
        folder = filedialog.askdirectory(
            title="Select Folder with Movies",
            initialdir=self.last_folder if self.last_folder else None
        )

        if folder:
            self.save_last_folder(folder)
            self.last_folder = folder
            files = []
            video_extensions = ('mp4', 'mkv', 'avi', 'mov', 'flv')

            for ext in video_extensions:
                files.extend(Path(folder).glob(f"**/*.{ext}"))
                files.extend(Path(folder).glob(f"**/*.{ext.upper()}"))

            files = list(set(files))

            if files:
                self.process_files([str(f) for f in files])
            else:
                messagebox.showwarning("No Files", "No video files found in folder")

    def process_files(self, files):
        """Process files in background thread"""
        thread = threading.Thread(target=self._process_files_thread, args=(files,), daemon=True)
        thread.start()

    def _process_files_thread(self, files):
        """Background thread for file processing"""
        self.status.set(f"Processing {len(files)} files...")
        self.progress['value'] = 0
        self.progress['maximum'] = len(files)
        self.root.update()

        self.preview_data = []
        self.preview_list.delete(0, tk.END)

        for idx, filepath in enumerate(files):
            if not os.path.exists(filepath):
                self.preview_list.insert(tk.END, f"✗ FILE NOT FOUND: {filepath}\n")
                self.progress['value'] = idx + 1
                self.root.update()
                continue

            filename = os.path.basename(filepath)
            name, ext = os.path.splitext(filename)

            print(f"[DEBUG] Processing: {filename}")
            print(f"[DEBUG] Name before cleaning: {name}")

            # Extract year from parentheses first (highest priority)
            year_match = re.search(r'\((\d{4})\)', name)
            year = year_match.group(1) if year_match else None

            # If no year in parentheses, look for standalone 4-digit year (1900-2100)
            if not year and re.search(r'[._\s-]([12]\d{3})[._\s-]', name):
                year_match = re.search(r'[._\s-]([12]\d{3})[._\s-]', name)
                if year_match:
                    year = year_match.group(1)
                    print(f"[DEBUG] Found year in filename: {year}")

            # Clean the name step by step
            clean_name = re.sub(r'\(\d{4}\)', '', name).strip()  # Remove (YYYY)
            clean_name = re.sub(r'[\[\{].*?[\]\}]', '', clean_name).strip()  # Remove [brackets] and {braces}

            # Remove year numbers if not captured above (1900-2100)
            clean_name = re.sub(r'\b[12]\d{3}\b', '', clean_name).strip()

            # Remove common usernames/release groups
            clean_name = re.sub(r'[\._-](rarbg|anoXmous|scene|proper|rerip|remux)(?:\.|_|-|$)', ' ', clean_name, flags=re.IGNORECASE).strip()

            # Remove quality markers and common release tags
            quality_markers = r'\b(1080p|720p|480p|2160p|4k|uhd|ultraHD|UltraHD|bluray|blu-ray|bdrip|webrip|hdtv|dvdrip|h\.?264|x\.?264|hevc|h\.?265|x\.?265|aac|ac3|dts|amd64|x86_64|10bit|avc|vc1|mpeg2|aiff|flac|opus|vorbis|mp3|eac3|truehd|dts-hd|atmos|imax|remastered|extended|directors?cut|uncut|proper|rerip|remux|pdtv|dsr|ts|tc|r5|dvdscr|brrip|xvid|divx|h264|x264|web|web-dl|web-rip)\b'
            clean_name = re.sub(quality_markers, '', clean_name, flags=re.IGNORECASE).strip()

            clean_name = re.sub(r'[._-]+', ' ', clean_name).strip()  # Convert dots/dashes/underscores to spaces
            clean_name = ' '.join(clean_name.split())  # Collapse multiple spaces

            print(f"[DEBUG] Name after cleaning: '{clean_name}' (year: {year})")

            self.status.set(f"Searching TMDB: {clean_name}...")
            self.root.update()

            tmdb_result = self.search_tmdb(clean_name, year)

            if tmdb_result:
                new_name = self.build_filename(tmdb_result, ext)
                self.preview_data.append((filepath, new_name, tmdb_result, "found"))
                self.display_preview_item(filepath, new_name, tmdb_result, "found")
            else:
                self.preview_data.append((filepath, filename, {'title': 'NOT FOUND', 'year': ''}, "not_found"))
                self.preview_list.insert(tk.END, f"✗ NOT FOUND: {filename}\n")

            self.progress['value'] = idx + 1
            # Show progress with file count and current filename
            progress_pct = int((idx + 1) / len(files) * 100)
            file_display = filename[:40] + "..." if len(filename) > 40 else filename
            self.status.set(f"Progress: {idx + 1}/{len(files)} ({progress_pct}%) - {file_display}")
            self.root.update()
            self.root.update_idletasks()  # Force UI refresh

        found_count = len([p for p in self.preview_data if p[3] == 'found'])
        self.status.set(f"Ready - {found_count} movies found")

    def search_tmdb(self, query, year=None):
        """Search TMDB with caching and smart fallback"""
        cache_key = f"{query}:{year}"

        # Check cache first
        if cache_key in self.tmdb_cache:
            return self.tmdb_cache[cache_key]

        try:
            if not self.api_key:
                raise Exception("API key not configured")

            url = f"{self.tmdb_base}/search/movie"

            # Try searches in order of specificity
            searches = []

            # 1. Full query with year
            if year:
                searches.append((query, year))

            # 2. Full query without year
            searches.append((query, None))

            # 3. Try without Roman numeral conversion (might match better)
            query_no_roman = re.sub(r'\b\d+\b', lambda m: self._number_to_roman(int(m.group())), query)
            if query_no_roman != query:
                searches.append((query_no_roman, year))
                searches.append((query_no_roman, None))

            # 4. Try first two words
            words = query.split()
            if len(words) > 2:
                two_word = ' '.join(words[:2])
                searches.append((two_word, year))
                searches.append((two_word, None))

            # Execute searches
            for search_query, search_year in searches:
                if not search_query or search_query.lower() == 'the':
                    continue

                print(f"[DEBUG] Searching TMDB: '{search_query}' (year: {search_year})")

                params = {
                    'api_key': self.api_key,
                    'query': search_query,
                    'page': 1,
                    'language': self.language.get()
                }
                if search_year:
                    params['year'] = search_year

                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                if data['results']:
                    result = data['results'][0]
                    movie_id = result['id']

                    tmdb_result = {
                        'title': result['title'],
                        'year': result['release_date'][:4] if result.get('release_date') else 'UNKNOWN',
                        'id': movie_id,
                    }

                    # Cache result
                    self.tmdb_cache[cache_key] = tmdb_result
                    print(f"[DEBUG] Found: {tmdb_result['title']} ({tmdb_result['year']})")
                    return tmdb_result

            print(f"[DEBUG] No TMDB results found for any variation of: {query}")

        except requests.exceptions.Timeout:
            messagebox.showerror("Timeout", "TMDB API request timed out. Check your internet connection.")
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Connection Error", "Could not connect to TMDB. Check your internet connection.")
        except Exception as e:
            print(f"[DEBUG] Error searching TMDB for '{query}': {e}")

        return None

    def _number_to_roman(self, num):
        """Convert number to Roman numeral"""
        val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        syms = ['M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I']
        roman_num = ''
        i = 0
        while num > 0:
            for _ in range(num // val[i]):
                roman_num += syms[i]
                num -= val[i]
            i += 1
        return roman_num

    def apply(self):
        if not self.preview_data:
            messagebox.showwarning("Warning", "No files to process")
            return

        if messagebox.askyesno("Confirm", f"Process {len([p for p in self.preview_data if p[3] == 'found'])} movies?"):
            thread = threading.Thread(target=self._process_movies, daemon=True)
            thread.start()

    def _process_movies(self):
        self.processing = True
        success = 0
        failed = []

        processable = [p for p in self.preview_data if p[3] == 'found']
        self.progress['maximum'] = len(processable)
        self.progress['value'] = 0

        self.status.set(f"Starting to process {len(processable)} movies...")
        self.root.update()

        for i, (filepath, new_name, tmdb_data, status) in enumerate(processable):
            try:
                file_dir = os.path.dirname(filepath)  # The folder containing the file
                parent_dir = os.path.dirname(file_dir)  # Parent of that folder
                old_folder_name = os.path.basename(file_dir)  # Current folder name
                old_filename = os.path.basename(filepath)  # Current file name

                # Build new folder and file names
                movie_folder_name = f"{tmdb_data['title']} ({tmdb_data['year']})"
                movie_folder_name = self.sanitize_filename(movie_folder_name)
                new_folder = os.path.join(parent_dir, movie_folder_name)
                new_filepath = os.path.join(new_folder, new_name)

                # Step 1: Rename the parent folder if different
                if file_dir != new_folder:
                    if not os.path.exists(new_folder):
                        self.status.set(f"Renaming folder: {old_folder_name} → {movie_folder_name}...")
                        self.root.update()

                        try:
                            os.rename(file_dir, new_folder)
                            print(f"[DEBUG] Folder renamed: {old_folder_name} → {movie_folder_name}")
                        except Exception as rename_error:
                            print(f"[DEBUG] Error renaming folder: {rename_error}")
                            raise

                # Step 2: Rename the file inside the folder if different
                if os.path.exists(new_folder):
                    current_filepath = os.path.join(new_folder, old_filename)

                    if os.path.exists(current_filepath) and current_filepath != new_filepath:
                        self.status.set(f"Renaming file: {old_filename} → {new_name}...")
                        self.root.update()

                        try:
                            os.rename(current_filepath, new_filepath)
                            print(f"[DEBUG] File renamed successfully: {old_filename} → {new_name}")
                        except PermissionError:
                            # Try copy instead if rename fails
                            try:
                                import shutil
                                shutil.copy2(current_filepath, new_filepath)
                                os.remove(current_filepath)
                                print(f"[DEBUG] File copied and deleted instead of renamed")
                            except Exception as copy_error:
                                print(f"[DEBUG] Copy also failed: {copy_error}")
                                raise PermissionError(f"Cannot rename or copy file: {copy_error}")
                        except Exception as rename_error:
                            print(f"[DEBUG] Error renaming file: {rename_error}")
                            raise

                success += 1

                # Update progress with percentage and current movie
                self.progress['value'] = i + 1
                progress_pct = int((i + 1) / len(processable) * 100)
                movie_display = new_name[:40] + "..." if len(new_name) > 40 else new_name
                self.status.set(f"Processing: {success}/{len(processable)} ({progress_pct}%) - {movie_display}")
                self.root.update()
                self.root.update_idletasks()  # Force UI refresh

            except PermissionError:
                failed.append((new_name, "Permission denied - check file permissions"))
            except OSError as e:
                failed.append((new_name, f"File error: {e}"))
            except Exception as e:
                failed.append((new_name, str(e)))

        msg = f"Processed {success}/{len(processable)} movies"

        if failed:
            msg += f"\n\nFailed ({len(failed)}):\n"
            msg += "\n".join([f"{name}: {err}" for name, err in failed[:5]])

        messagebox.showinfo("Processing Complete", msg)
        self.processing = False
        self.clear()

    def clear(self):
        self.preview_list.delete(0, tk.END)
        self.preview_data = []
        self.progress['value'] = 0
        self.search_var.set("")
        self.filter_var.set("All")
        self.status.set("Ready")

    def on_closing(self):
        """Handle window closing"""
        self.save_window_state()
        self.root.destroy()

if __name__ == "__main__":
    # Load environment variables from .env file
    if DOTENV_AVAILABLE:
        # Try to find .env in script directory first
        script_dir = os.path.dirname(os.path.abspath(__file__))
        env_file = os.path.join(script_dir, '.env')

        if os.path.exists(env_file):
            load_dotenv(env_file)
            print(f"[DEBUG] Loaded .env from: {env_file}")
        else:
            load_dotenv()
            print("[DEBUG] Loaded environment variables from .env (current directory)")

    # Get API key from environment variable and strip whitespace
    API_KEY = os.getenv('TMDB_API_KEY', '').strip()

    if not API_KEY:
        print("[WARNING] TMDB_API_KEY not found in environment")
        print("[INFO] Create a .env file with: TMDB_API_KEY=your_key_here")
        print("[INFO] Or set environment variable: export TMDB_API_KEY=your_key_here")
    else:
        print(f"[DEBUG] API Key loaded successfully")

    # Try to use TkinterDnD for drag & drop, fallback to regular Tk
    try:
        from tkinterdnd2 import TkinterDnD
        root = TkinterDnD.Tk()
        print("[DEBUG] Using TkinterDnD for drag & drop support")
    except ImportError:
        root = tk.Tk()
        print("[DEBUG] TkinterDnD not available, using regular Tk (no drag & drop)")

    app = MovieRenamer(root, API_KEY)
    root.mainloop()
