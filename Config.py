# SteamKM_Config.py
import os
import sys
import json
import tempfile
import threading
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, Tuple, List
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox

def get_config_dir():
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))
        return Path(base) / "SteamKM"
    else:
        # Linux/macOS
        base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        return Path(base) / "SteamKM"

# File paths and constants
CONFIG_DIR = get_config_dir()
CONFIG_FILE_PATH = CONFIG_DIR / "manager_settings.json"
GAME_PICTURES_DIR = CONFIG_DIR / "game_pictures"
DEFAULT_BRANCH = "beta"

# UI settings
UI_MARGIN = 8, 8, 8, 8  # Used for the UI and window margin (for all layouts)
HORIZONTAL_SPACING = 5  # Horizontal spacing between elements
VERTICAL_SPACING = 8  # Vertical spacing between elements
VERTICAL_SPACING_SMALL = 5  # Vertical spacing between elements that are supposed to be closer together, like theme color pickers
BUTTON_HEIGHT = 30  # Height
ICON_BUTTON_WIDTH = 33  # Width for icon buttons
TITLE_HEIGHT = BUTTON_HEIGHT  # Height for title labels
CHECKBOX_SIZE = 18  # Height
DEFAULT_RADIUS = 15  # Border Radius
DEFAULT_BORDER_SIZE = 0  # Border Size
DEFAULT_CHECKBOX_RADIUS = 9  # Checkbox Radius
DEFAULT_BAR_RADIUS = 7  # Bar Radius
DEFAULT_BAR_THICKNESS = 14  # Bar Thickness
DBH = 1.19  # Dynamic brightness hover value
DBP = 0.92  # Dynamic brightness press value
PADDING = "padding: 6px"
GROUPBOX_PADDING = "padding: 0"
BUTTON_PADDING = "padding: 0px 12px"
COLOR_PICKER_BUTTON_STYLE = "border-top-right-radius: 0px; border-bottom-right-radius: 0px; border-right: 0px;"
COLOR_RESET_BUTTON_STYLE = "border-top-left-radius: 0px; border-bottom-left-radius: 0px; border-left: 0px;"
DV_SCROLLBAR = "DynamicVScrollBar"

# Table Widget related sizes
TABLE_CELL_RADIUS = 3  # Corner radius for all cells in the table widget including icons and headers
TABLE_ICON_HEIGHT = 23  # Height for icons in the table widget
TABLE_ICON_WIDTH = 67  # Width for icons in the table widget

# Constants for dialog dimensions
DEFAULT_DIALOG_WIDTH = 400
DEFAULT_DIALOG_HEIGHT = 20
DEFAULT_TEXT_BROWSER_MIN_HEIGHT = 50

def check_old_file_structure() -> Tuple[bool, List[str], List[str]]:
    """
    Checks if old configuration files exist in the executable directory.
    
    Returns:
        Tuple containing:
        - Boolean indicating if migration is needed
        - List of old file paths that need migration
        - List of new file paths where files should be migrated to
    """
    # Get the script directory (where the executable is located)
    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    script_dir_path = Path(script_dir)
    
    # Skip migration if executable is already in the AppData/config directory
    # This can happen if someone manually moved the exe there
    if CONFIG_DIR in script_dir_path.parents or CONFIG_DIR == script_dir_path:
        return False, [], []
    
    # Define old file paths
    old_config_path = os.path.join(script_dir, "manager_settings.json")
    old_keys_path = os.path.join(script_dir, "steam_keys.json.enc")
    old_files = []
    
    # Check which old files exist
    if os.path.exists(old_config_path):
        old_files.append(old_config_path)
    if os.path.exists(old_keys_path):
        old_files.append(old_keys_path)
    
    # If no old files, no migration needed
    if not old_files:
        return False, [], []
    
    # Ensure CONFIG_DIR exists
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Define new file paths
    new_files = []
    for old_file in old_files:
        filename = os.path.basename(old_file)
        new_files.append(str(CONFIG_DIR / filename))
    
    return True, old_files, new_files

def migrate_files(old_files: List[str], new_files: List[str]) -> bool:
    """
    Migrates files from old locations to new locations and deletes the old files if successful.
    
    Args:
        old_files: List of old file paths
        new_files: List of new file paths
    
    Returns:
        Boolean indicating if migration was successful
    """
    try:
        # Create the config directory if it doesn't exist
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        # Copy each file
        for old_file, new_file in zip(old_files, new_files):
            shutil.copy2(old_file, new_file)
            
        # Verify all files were copied successfully
        all_copied = all(os.path.exists(new_file) for new_file in new_files)
        
        # Only delete original files if all were copied successfully
        if all_copied:
            for old_file in old_files:
                os.remove(old_file)
                
        return all_copied
    except Exception as e:
        logging.error(f"Error during file migration: {e}")
        return False

class ConfigManager:
    """
    Centralized configuration manager that provides in-memory access to config settings
    with debounced saving to reduce disk I/O operations.
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConfigManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._config = {}
        self._save_timer = QTimer()
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._perform_save)
        self._save_pending = False
        
        # Default config values
        self._defaults = {
            "selected_branch": DEFAULT_BRANCH,
            "show_update_message": False,
            "auto_update_check": True,
            "swap_input_search": False,
            "merge_edges": True,
            "using_custom_colors": False,
            "theme": "dark",
            "custom_colors": {},
            "border_radius": DEFAULT_RADIUS,
            "border_size": DEFAULT_BORDER_SIZE,
            "checkbox_radius": DEFAULT_CHECKBOX_RADIUS,
            "bar_thickness":  DEFAULT_BAR_THICKNESS,
            "bar_radius": DEFAULT_BAR_RADIUS,
            "categories": ["New", "Premium", "Good", "Low Effort", "Bad", "VR", "DLC", "Used"],
        }
        
        self.load()
        self._initialized = True
    
    def load(self):
        """Load configuration from disk with fallback to defaults"""
        if not CONFIG_FILE_PATH.exists():
            self._config = self._defaults.copy()
            return
        
        try:
            with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                # Merge with defaults to ensure all expected keys exist
                self._config = self._defaults.copy()
                self._config.update(loaded_config)
        except (json.JSONDecodeError, IOError, OSError) as e:
            logging.error(f" loading config: {e}")
            self._config = self._defaults.copy()
    
    def get(self, key: str, default=None) -> Any:
        """Get a config value with optional default if key doesn't exist"""
        return self._config.get(key, default if default is not None else self._defaults.get(key))
    
    def set(self, key: str, value: Any, save: bool = True) -> None:
        """Set a config value and optionally trigger a save"""
        self._config[key] = value
        if save:
            self.schedule_save()
    
    def update(self, values: Dict[str, Any], save: bool = True) -> None:
        """Update multiple config values at once"""
        self._config.update(values)
        if save:
            self.schedule_save()
    
    def schedule_save(self, delay_ms: int = 500) -> None:
        """Schedule a save operation with debouncing"""
        if self._save_timer.isActive():
            self._save_timer.stop()
        self._save_timer.start(delay_ms)
        self._save_pending = True
    
    def _perform_save(self) -> None:
        """Actually perform the save operation to disk"""
        if not self._save_pending:
            return
        
        try:
            # Create directory if it doesn't exist
            CONFIG_FILE_PATH.parent.mkdir(exist_ok=True)
            
            # Use atomic write pattern to prevent corruption
            with tempfile.NamedTemporaryFile('w', dir=CONFIG_FILE_PATH.parent, 
                                           delete=False, encoding='utf-8') as tf:
                # Write to temporary file
                json.dump(self._config, tf, indent=4)
                temp_path = tf.name
                
            # Atomic replace
            os.replace(temp_path, CONFIG_FILE_PATH)
            self._save_pending = False
        except (IOError, OSError, TypeError) as e:
            logging.error(f" saving config: {e}")
            # Try to clean up the temp file if it exists
            if 'temp_path' in locals():
                try:
                    os.unlink(temp_path)
                except:
                    pass
    
    def save_now(self) -> None:
        """Force an immediate save operation"""
        if self._save_timer.isActive():
            self._save_timer.stop()
        self._perform_save()
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get a copy of the entire configuration"""
        return self._config.copy()