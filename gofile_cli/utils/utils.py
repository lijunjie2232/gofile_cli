"""
Utility Functions Module

This module provides common utility functions used throughout the GoFile CLI application.
Includes file operations, string manipulation, and data formatting utilities.
"""

import hashlib
import re
from pathlib import Path
from time import sleep, time
from typing import Optional

AUTH_PATTERN = re.compile(r"https://gofile.io/login/(.*)\n")


def calculate_md5(file_path: Path | str, md5Sum: str = "") -> str | bool:
    """
    Calculate MD5 hash of a file or verify against provided hash.
    
    Args:
        file_path: Path to the file to calculate hash for.
        md5Sum: Optional expected hash to verify against.
    
    Returns:
        If md5Sum is provided: bool indicating if hashes match.
        If md5Sum is empty: str containing the calculated MD5 hash.
    
    Raises:
        FileNotFoundError: If the specified file does not exist.
        IOError: If there's an error reading the file.
    
    Example:
        >>> calculate_md5("/path/to/file.txt")
        'd41d8cd98f00b204e9800998ecf8427e'
        >>> calculate_md5("/path/to/file.txt", "d41d8cd98f00b204e9800998ecf8427e")
        True
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        
        calculated_hash = hash_md5.hexdigest()
        return calculated_hash == md5Sum if md5Sum else calculated_hash
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")


def message_filter(MAIL_TM, account, waiting_time: int = 120) -> Optional[str]:
    """
    Filter messages from MailTM account to find GoFile authentication link.
    
    This function polls the mailbox for new messages and extracts the GoFile
    authentication URL from email content.
    
    Args:
        MAIL_TM: MailTM client instance.
        account: MailTM Account object.
        waiting_time: Maximum time to wait for messages in seconds. Default: 120.
    
    Returns:
        Authentication token extracted from email, or None if timeout.
    
    Raises:
        TimeoutError: If no valid message is found within waiting_time.
    
    Example:
        >>> auth_token = message_filter(mailtm, account, waiting_time=180)
    """
    start_time = time()
    
    while start_time + waiting_time > time():
        try:
            messages = MAIL_TM.get_messages(account)
            for msg in messages.hydra_member:
                if msg.isDeleted or msg.seen:
                    continue
                
                content = MAIL_TM.get_message_by_id(
                    message_id=msg.id,
                    account=account,
                )
                
                result = AUTH_PATTERN.findall(content.text)
                if result:
                    # Mark message as read
                    try:
                        MAIL_TM.set_read_message_by_id(msg.id, account.token.token)
                    except Exception:
                        pass  # Ignore errors marking as read
                    
                    return result[0]
            
            sleep(5)
        except Exception as e:
            # Log error but continue polling
            print(f"Error checking messages: {e}")
            sleep(5)
    
    raise TimeoutError(f"No authentication message received within {waiting_time} seconds")


def convert_bytes_to_readable(size_bytes: int) -> str:
    """
    Convert bytes to human-readable format.
    
    Args:
        size_bytes: Size in bytes.
    
    Returns:
        Formatted string with appropriate unit (B, KB, MB, GB).
    
    Raises:
        ValueError: If size_bytes is negative.
    
    Example:
        >>> convert_bytes_to_readable(1048576)
        '1.0 MB'
        >>> convert_bytes_to_readable(1536)
        '1.5 KB'
    """
    if size_bytes < 0:
        raise ValueError("size_bytes must be non-negative")
    
    units = ["B", "KB", "MB", "GB"]
    index = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and index < len(units) - 1:
        size /= 1024.0
        index += 1
    
    # Format number, removing unnecessary trailing zeros
    bstr = f"{size:.2f}".rstrip('0').rstrip('.')
    
    return f"{bstr} {units[index]}"
