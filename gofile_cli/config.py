"""
Configuration Management Module

This module handles user configuration storage and management for the GoFile CLI.
It supports multiple user profiles, credential storage, and application settings.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ConfigError(Exception):
    """Exception raised for configuration errors."""
    pass


class UserConfig:
    """Represents a user's configuration profile."""
    
    def __init__(
        self,
        username: str,
        gofile_token: Optional[str] = None,
        mailtm_token: Optional[str] = None,
        mailtm_password: Optional[str] = None,
        created_at: Optional[str] = None,
        last_used: Optional[str] = None,
        comment: Optional[str] = None,
    ):
        """
        Initialize a user configuration.
        
        Args:
            username: Username for the account.
            gofile_token: GoFile authorization token.
            mailtm_token: MailTM authentication token.
            mailtm_password: MailTM account password.
            created_at: Account creation timestamp.
            last_used: Last usage timestamp.
            comment: Optional comment or note for this account.
        """
        self.username = username
        self.gofile_token = gofile_token
        self.mailtm_token = mailtm_token
        self.mailtm_password = mailtm_password
        self.created_at = created_at or datetime.now().isoformat()
        self.last_used = last_used
        self.comment = comment
    
    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            "username": self.username,
            "gofile_token": self.gofile_token,
            "mailtm_token": self.mailtm_token,
            "mailtm_password": self.mailtm_password,
            "created_at": self.created_at,
            "last_used": self.last_used,
            "comment": self.comment,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "UserConfig":
        """Create UserConfig from dictionary."""
        return cls(
            username=data.get("username", ""),
            gofile_token=data.get("gofile_token"),
            mailtm_token=data.get("mailtm_token"),
            mailtm_password=data.get("mailtm_password"),
            created_at=data.get("created_at"),
            last_used=data.get("last_used"),
            comment=data.get("comment"),
        )


class ConfigManager:
    """
    Manages application configuration including user profiles and settings.
    
    This class handles loading, saving, and managing configuration data stored
    in JSON format. It supports multiple user profiles and application-wide settings.
    
    Attributes:
        config_path (Path): Path to the configuration file.
        config_dir (Path): Directory containing the configuration file.
    """
    
    DEFAULT_CONFIG_DIR = Path.home() / ".gofile_cli"
    CONFIG_FILE = "config.json"
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Optional custom path to config file. If None, uses default location.
        """
        if config_path:
            self.config_path = config_path
            self.config_dir = config_path.parent
        else:
            self.config_dir = self.DEFAULT_CONFIG_DIR
            self.config_path = self.config_dir / self.CONFIG_FILE
        
        self.config = {
            "users": [],
            "active_user": None,
            "settings": {
                "default_upload_folder": None,
                "download_path": str(Path.home() / "Downloads"),
                "verify_downloads": False,
                "show_progress": True,
            }
        }
        # Cache user lookup for performance
        self._user_cache: dict[str, UserConfig] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file."""
        if not self.config_path.exists():
            self._save_config()
            return
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
            
            # Ensure all required keys exist
            if "users" not in self.config:
                self.config["users"] = []
            if "active_user" not in self.config:
                self.config["active_user"] = None
            if "settings" not in self.config:
                self.config["settings"] = {}
            
            # Update user cache
            self._update_user_cache()
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid configuration file: {e}")
        except Exception as e:
            raise ConfigError(f"Failed to load configuration: {e}")
    
    def _save_config(self) -> None:
        """Save configuration to file."""
        # Create directory if it doesn't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise ConfigError(f"Failed to save configuration: {e}")
    
    def _update_user_cache(self) -> None:
        """Update the user lookup cache."""
        self._user_cache = {
            user["username"]: UserConfig.from_dict(user)
            for user in self.config["users"]
        }
    
    def add_user(self, user_config: UserConfig) -> None:
        """
        Add a new user profile.
        
        Args:
            user_config: UserConfig object to add.
        
        Raises:
            ConfigError: If user already exists.
        """
        # Check if user already exists using cache
        if user_config.username in self._user_cache:
            raise ConfigError(f"User '{user_config.username}' already exists")
        
        self.config["users"].append(user_config.to_dict())
        self._update_user_cache()
        self._save_config()
    
    def get_user(self, username: str) -> Optional[UserConfig]:
        """
        Get a user configuration by username.
        
        Args:
            username: Username to search for.
        
        Returns:
            UserConfig object if found, None otherwise.
        """
        return self._user_cache.get(username)
    
    def update_user(self, user_config: UserConfig) -> None:
        """
        Update an existing user profile.
        
        Args:
            user_config: Updated UserConfig object.
        
        Raises:
            ConfigError: If user does not exist.
        """
        if user_config.username not in self._user_cache:
            raise ConfigError(f"User '{user_config.username}' not found")
        
        for i, user in enumerate(self.config["users"]):
            if user["username"] == user_config.username:
                self.config["users"][i] = user_config.to_dict()
                self._update_user_cache()
                self._save_config()
                return
        
        raise ConfigError(f"User '{user_config.username}' not found")
    
    def delete_user(self, username: str) -> None:
        """
        Delete a user profile.
        
        Args:
            username: Username to delete.
        
        Raises:
            ConfigError: If user does not exist.
        """
        if username not in self._user_cache:
            raise ConfigError(f"User '{username}' not found")
        
        for i, user in enumerate(self.config["users"]):
            if user["username"] == username:
                self.config["users"].pop(i)
                
                # Clear active user if deleted
                if self.config["active_user"] == username:
                    self.config["active_user"] = None
                
                self._update_user_cache()
                self._save_config()
                return
        
        raise ConfigError(f"User '{username}' not found")
    
    def list_users(self) -> List[UserConfig]:
        """
        Get all user profiles.
        
        Returns:
            List of UserConfig objects.
        """
        return [UserConfig.from_dict(user) for user in self.config["users"]]
    
    def set_active_user(self, username: str) -> None:
        """
        Set the active user profile.
        
        Args:
            username: Username to set as active.
        
        Raises:
            ConfigError: If user does not exist.
        """
        # Verify user exists
        user = self.get_user(username)
        if not user:
            raise ConfigError(f"User '{username}' not found")
        
        self.config["active_user"] = username
        self._save_config()
    
    def get_active_user(self) -> Optional[UserConfig]:
        """
        Get the currently active user profile.
        
        Returns:
            Active UserConfig object or None if no active user.
        """
        if not self.config["active_user"]:
            return None
        
        return self.get_user(self.config["active_user"])
    
    def get_setting(self, key: str, default=None):
        """
        Get a configuration setting.
        
        Args:
            key: Setting key name.
            default: Default value if key doesn't exist.
        
        Returns:
            Setting value or default.
        """
        return self.config["settings"].get(key, default)
    
    def set_setting(self, key: str, value) -> None:
        """
        Set a configuration setting.
        
        Args:
            key: Setting key name.
            value: Setting value.
        """
        self.config["settings"][key] = value
        self._save_config()
    
    def get_download_path(self) -> Path:
        """Get the configured download path."""
        return Path(self.config["settings"].get("download_path", str(Path.home() / "Downloads")))
    
    def is_verified_downloads_enabled(self) -> bool:
        """Check if download verification is enabled."""
        return self.config["settings"].get("verify_downloads", False)
    
    def show_progress(self) -> bool:
        """Check if progress bars should be shown."""
        return self.config["settings"].get("show_progress", True)
