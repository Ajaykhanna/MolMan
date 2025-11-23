"""
Centralized logging configuration for MolMan.

This module provides a unified logging setup with:
- Multiple handlers (console, file, rotating file)
- Configurable log levels
- Structured logging format
- Debug mode support
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional


# Default log directory
DEFAULT_LOG_DIR = Path.home() / ".molman" / "logs"

# Log format
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEBUG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"


def setup_logging(
    level: int = logging.INFO,
    log_dir: Optional[Path] = None,
    enable_file_logging: bool = True,
    enable_console_logging: bool = True,
    debug_mode: bool = False,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    Set up centralized logging for MolMan.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: ~/.molman/logs)
        enable_file_logging: Whether to enable file logging
        enable_console_logging: Whether to enable console logging
        debug_mode: Enable debug mode with verbose output
        max_bytes: Maximum size of each log file before rotation (default: 10 MB)
        backup_count: Number of backup log files to keep (default: 5)

    Returns:
        Configured root logger
    """
    # Adjust level for debug mode
    if debug_mode:
        level = logging.DEBUG

    # Get root logger
    root_logger = logging.getLogger("molman")
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Choose format based on debug mode
    log_format = DEBUG_FORMAT if debug_mode else DEFAULT_FORMAT
    formatter = logging.Formatter(log_format)

    # Console handler
    if enable_console_logging:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handlers
    if enable_file_logging:
        # Use provided log directory or default
        if log_dir is None:
            log_dir = DEFAULT_LOG_DIR

        # Create log directory if it doesn't exist
        log_dir.mkdir(parents=True, exist_ok=True)

        # Rotating file handler (main log)
        main_log_file = log_dir / "molman.log"
        file_handler = logging.handlers.RotatingFileHandler(
            main_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        # Error-specific log file (always captures errors regardless of level)
        error_log_file = log_dir / "molman_errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)

    # Prevent propagation to avoid duplicate logs
    root_logger.propagate = False

    root_logger.debug("Logging system initialized")
    if enable_file_logging:
        root_logger.debug(f"Log files location: {log_dir}")

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name under the 'molman' namespace.

    Args:
        name: Name of the logger (typically __name__ of the module)

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("This is an info message")
    """
    # Ensure the logger is under the 'molman' namespace
    if not name.startswith("molman."):
        if name == "__main__":
            name = "molman.main"
        else:
            name = f"molman.{name}"

    return logging.getLogger(name)


def set_log_level(level: int) -> None:
    """
    Change the log level for all MolMan loggers.

    Args:
        level: New logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    root_logger = logging.getLogger("molman")
    root_logger.setLevel(level)
    for handler in root_logger.handlers:
        handler.setLevel(level)


def enable_debug_mode() -> None:
    """
    Enable debug mode with verbose logging.

    This sets the log level to DEBUG and switches to the detailed format.
    """
    root_logger = logging.getLogger("molman")
    root_logger.setLevel(logging.DEBUG)

    # Update formatter to debug format
    debug_formatter = logging.Formatter(DEBUG_FORMAT)
    for handler in root_logger.handlers:
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(debug_formatter)

    root_logger.debug("Debug mode enabled")


def disable_console_logging() -> None:
    """
    Disable console logging (useful for GUI applications or automated scripts).
    """
    root_logger = logging.getLogger("molman")
    for handler in list(root_logger.handlers):
        if isinstance(handler, logging.StreamHandler) and not isinstance(
            handler, logging.FileHandler
        ):
            root_logger.removeHandler(handler)


def get_log_directory() -> Path:
    """
    Get the current log directory path.

    Returns:
        Path to log directory
    """
    return DEFAULT_LOG_DIR


# Initialize logging when module is imported
# This ensures logging is set up by default, but can be reconfigured
if not logging.getLogger("molman").handlers:
    setup_logging()
