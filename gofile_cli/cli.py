"""
GoFile CLI - Command Line Interface for GoFile.io

A modern, feature-rich command-line tool for interacting with GoFile.io file hosting service.
Supports file upload, download, folder management, and account operations.

Usage:
    gofile-cli upload <file_path> [--id FOLDER_ID]
    gofile-cli download <ID> [--output OUTPUT_PATH] [--verify] [--overwrite]
    gofile-cli ls [--id FOLDER_ID] [--tree]
    gofile-cli login [--new] [--view-only]
    gofile-cli logout
    gofile-cli mkdir <folder_name> [--parent PARENT_ID]
    gofile-cli delete <CONTENT_ID> [--recursive]
    gofile-cli info <CONTENT_ID>

Examples:
    # Upload a file to root folder
    $ gofile-cli upload /path/to/file.txt
    
    # Upload to specific folder
    $ gofile-cli upload document.pdf --id abc123
    
    # Download with verification
    $ gofile-cli download xyz789 --output ./downloads/ --verify
    
    # List folder contents
    $ gofile-cli ls --id abc123
    
    # Create new account
    $ gofile-cli login --new
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from gofile_cli.api import GoFile, MailTM
from gofile_cli.config import ConfigManager, UserConfig
from gofile_cli.entity.gofile import Profile
from gofile_cli.utils import convert_bytes_to_readable, message_filter

# Initialize Typer app
app = typer.Typer(
    name="gofile-cli",
    help="Command-line interface for GoFile.io file hosting service",
    add_completion=True,
)
console = Console()

# Global config manager
config_manager: Optional[ConfigManager] = None
# Time format for displaying timestamps
time_format = "%Y-%m-%d %H:%M:%S"


def handle_errors(func):
    """
    Decorator to handle common error patterns in CLI commands.
    
    Args:
        func: The command function to wrap.
    
    Returns:
        Wrapped function with error handling.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileExistsError as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
            console.print("Use --overwrite flag to overwrite existing files.")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[bold red]Operation failed:[/bold red] {str(e)}")
            raise typer.Exit(1)
    return wrapper


def get_config() -> ConfigManager:
    """Get or create configuration manager instance."""
    global config_manager
    if config_manager is None:
        config_manager = ConfigManager()
    return config_manager


def get_gofile_client() -> Optional[GoFile]:
    """Get GoFile client for active user.
    
    Returns:
        GoFile client instance or None if not authenticated.
    """
    config = get_config()
    active_user = config.get_active_user()
    
    if not active_user:
        console.print("[bold red]Error:[/bold red] Not logged in. Please run 'gofile-cli login' first.")
        return None
    
    if not active_user.gofile_token:
        console.print("[bold red]Error:[/bold red] No GoFile token found for active user.")
        return None
    
    return GoFile(
        authorization_token=active_user.gofile_token,
        username=active_user.username,
    )


def get_mailtm_client() -> MailTM:
    """Get MailTM client instance.
    
    Returns:
        MailTM client instance.
    """
    return MailTM()

@app.command("upload")
def upload_file(
    file_path: str = typer.Argument(..., help="Path to the file to upload"),
    folder_id: Optional[str] = typer.Option(
        None,
        "--id",
        help="Destination folder ID (default: root folder)",
    ),
):
    """
    Upload a file to GoFile.
    
    FILE_PATH: Path to the file you want to upload
    
    Examples:
        $ gofile-cli upload document.pdf
        $ gofile-cli upload photo.jpg --id abc123
    """
    client = get_gofile_client()
    if not client:
        raise typer.Exit(1)
    
    # Validate file path
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        console.print(f"[bold red]Error:[/bold red] File not found: {file_path}")
        raise typer.Exit(1)
    
    if not file_path_obj.is_file():
        console.print(f"[bold red]Error:[/bold red] Not a file: {file_path}")
        raise typer.Exit(1)
    
    try:
        # Get destination folder
        profile = client.get_me()
        dest_folder_id = folder_id or profile.rootFolder
        
        with console.status(f"[bold green]Uploading {file_path_obj.name}..."):
            result = client.upload_file(
                file_path=file_path,
                folder_id=dest_folder_id,
                progress_bar=True,
            )
        
        # Display upload result
        file_info = result.data
        table = Table(
            title=f"[bold green]✓ Upload Successful[/bold green]",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Name", file_info.name)
        table.add_row("Type", file_info.type.capitalize())
        table.add_row("Size", convert_bytes_to_readable(file_info.size))
        table.add_row(
            "Created",
            datetime.fromtimestamp(file_info.createTime, tz=timezone.utc).strftime(time_format),
        )
        table.add_row(
            "Modified",
            datetime.fromtimestamp(file_info.modTime, tz=timezone.utc).strftime(time_format),
        )
        table.add_row("Download Link", f"[blue]{file_info.link}[/blue]")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]Upload failed:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.command("download")
def download_file(
    file_id: str = typer.Argument(..., help="File ID to download"),
    output_path: Optional[str] = typer.Option(
        None,
        "--output", "-o",
        help="Output path (default: current directory)",
    ),
    verify: bool = typer.Option(
        False,
        "--verify", "-v",
        help="Verify file integrity using MD5",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite existing files",
    ),
):
    """
    Download a file from GoFile.
    
    FILE_ID: ID of the file to download
    
    Examples:
        $ gofile-cli download abc123
        $ gofile-cli download xyz789 -o ./downloads/
        $ gofile-cli download def456 --verify --overwrite
    """
    client = get_gofile_client()
    if not client:
        raise typer.Exit(1)
    
    try:
        # Determine output path
        if output_path:
            output = Path(output_path)
            if output.is_dir():
                output = output / file_id  # Will be renamed after download
        else:
            config = get_config()
            output = config.get_download_path()
        
        output.parent.mkdir(parents=True, exist_ok=True)
        
        console.print(f"[bold blue]Downloading file {file_id}...[/bold blue]")
        
        client.download_file(
            id=file_id,
            output_path=output,
            overwrite=overwrite,
            verify=verify,
            show_process_bar=True,
        )
        
        console.print(f"[bold green]✓ Download completed successfully![/bold green]")
        
    except FileExistsError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        console.print("Use --overwrite flag to overwrite existing files.")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Download failed:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.command("ls")
def list_contents(
    folder_id: Optional[str] = typer.Option(
        None,
        "--id",
        help="Folder ID to list (default: root folder)",
    ),
    tree: bool = typer.Option(
        False,
        "--tree", "-t",
        help="Display as tree structure",
    ),
):
    """
    List contents of a folder.
    
    Examples:
        $ gofile-cli ls
        $ gofile-cli ls --id abc123
        $ gofile-cli ls --tree
    """
    client = get_gofile_client()
    if not client:
        raise typer.Exit(1)
    
    try:
        # Get folder ID
        if not folder_id:
            profile = client.get_me()
            folder_id = profile.rootFolder
        
        # Get content info
        content_info = client.get_content_info(folder_id)
        
        if content_info.data.type == "folder":
            file_list = content_info.data.children
            
            table = Table(
                title=f"Folder Contents (ID: {folder_id})",
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("Name", style="green")
            table.add_column("ID", style="cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Public", style="yellow")
            table.add_column("Size", style="blue")
            table.add_column("Created", style="red")
            table.add_column("Modified", style="blue")
            table.add_column("Children", style="yellow")
            
            for k, v in file_list.items():
                if v["type"] == "folder":
                    table.add_row(
                        v["name"],
                        k,
                        "📁",
                        "🌐" if v.get("public") else "🔒",
                        convert_bytes_to_readable(v.get("totalSize", 0)),
                        datetime.fromtimestamp(v["createTime"], tz=timezone.utc).strftime(time_format),
                        datetime.fromtimestamp(v["modTime"], tz=timezone.utc).strftime(time_format),
                        str(v.get("childrenCount", 0)),
                    )
                else:
                    table.add_row(
                        v["name"],
                        k,
                        "📄",
                        "-",
                        convert_bytes_to_readable(v.get("size", 0)),
                        datetime.fromtimestamp(v["createTime"], tz=timezone.utc).strftime(time_format),
                        datetime.fromtimestamp(v["modTime"], tz=timezone.utc).strftime(time_format),
                        "-",
                    )
            
            console.print(table)
            
        elif content_info.data.type == "file":
            file_info = content_info.data
            table = Table(
                title="File Information",
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Name", file_info.name)
            table.add_row("Type", file_info.type.capitalize())
            table.add_row("Size", convert_bytes_to_readable(file_info.size))
            table.add_row(
                "Created",
                datetime.fromtimestamp(file_info.createTime, tz=timezone.utc).strftime(time_format),
            )
            table.add_row(
                "Modified",
                datetime.fromtimestamp(file_info.modTime, tz=timezone.utc).strftime(time_format),
            )
            table.add_row("Download Link", f"[blue underline]{file_info.link}[/blue underline]")
            
            console.print(table)
    
    except Exception as e:
        console.print(f"[bold red]Error listing contents:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.command("login")
def login(
    new: bool = typer.Option(
        False,
        "--new", "-n",
        help="Create a new account",
    ),
    view_only: bool = typer.Option(
        False,
        "--view-only",
        help="View stored accounts without logging in",
    ),
):
    """
    Login to GoFile or create a new account.
    
    Examples:
        $ gofile-cli login                  # View accounts and login
        $ gofile-cli login --new            # Create new account
        $ gofile-cli login --view-only      # View accounts only
    """
    config = get_config()
    mailtm = get_mailtm_client()
    
    if view_only:
        # Just display accounts
        users = config.list_users()
        if users:
            table = Table(title="Stored Accounts")
            table.add_column("Username", style="cyan")
            table.add_column("Has GoFile Token", style="green")
            table.add_column("Created", style="yellow")
            table.add_column("Comment", style="white")
            
            for user in users:
                has_token = "✓" if user.gofile_token else "✗"
                table.add_row(
                    user.username,
                    has_token,
                    user.created_at[:10] if user.created_at else "N/A",
                    user.comment or "",
                )
            console.print(table)
        else:
            console.print("[yellow]No stored accounts found.[/yellow]")
        return
    
    if new:
        # Create new account
        try:
            with console.status("[bold green]Creating new account..."):
                maccount, username, password = mailtm.create_account()
            
            console.print(f"[bold green]✓ Created MailTM account:[/bold green] {username}")
            
            # Store MailTM credentials
            mail_user = UserConfig(
                username=username,
                mailtm_token=maccount.token.token,
                mailtm_password=password,
            )
            config.add_user(mail_user)
            
            # Get GoFile link
            with console.status("[bold green]Requesting GoFile authentication..."):
                result = GoFile.get_link(maccount)
            
            if result.get("status") != "ok":
                console.print("[bold red]Error getting GoFile link[/bold red]")
                raise typer.Exit(1)
            
            # Wait for authentication email
            with console.status("[bold green]Waiting for authentication email..."):
                auth_token = message_filter(mailtm, maccount, waiting_time=120)
            
            # Initialize GoFile client
            gofile = GoFile(authorization_token=auth_token, username=username)
            profile = gofile.get_me()
            
            # Update config with GoFile token
            mail_user.gofile_token = auth_token
            config.update_user(mail_user)
            config.set_active_user(username)
            
            console.print(f"[bold green]✓ Successfully logged in as {username}![/bold green]")
            console.print(f"Email: {profile.email}")
            console.print(f"Root Folder: {profile.rootFolder}")
            
        except TimeoutError as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[bold red]Account creation failed:[/bold red] {str(e)}")
            raise typer.Exit(1)
    else:
        # Login with existing account
        users = config.list_users()
        
        if not users:
            console.print("[yellow]No stored accounts found. Create one with --new flag.[/yellow]")
            raise typer.Exit(1)
        
        # Display accounts
        table = Table(title="Select Account")
        table.add_column("#", style="cyan")
        table.add_column("Username", style="green")
        table.add_column("Created", style="yellow")
        
        for i, user in enumerate(users):
            table.add_row(
                str(i),
                user.username,
                user.created_at[:10] if user.created_at else "N/A",
            )
        console.print(table)
        
        # Get user selection
        try:
            selection = typer.prompt("Enter username or number")
            
            # Try to parse as number first
            if selection.isdigit() and 0 <= int(selection) < len(users):
                selected_user = users[int(selection)]
            else:
                # Find by username
                selected_user = config.get_user(selection)
                if not selected_user:
                    console.print(f"[bold red]Error:[/bold red] User '{selection}' not found")
                    raise typer.Exit(1)
            
            # Set as active user
            config.set_active_user(selected_user.username)
            console.print(f"[bold green]✓ Logged in as {selected_user.username}[/bold green]")
            
        except Exception as e:
            console.print(f"[bold red]Login failed:[/bold red] {str(e)}")
            raise typer.Exit(1)


@app.command("logout")
def logout():
    """Logout current user."""
    config = get_config()
    active_user = config.get_active_user()
    
    if not active_user:
        console.print("[yellow]Not logged in.[/yellow]")
        return
    
    config.config["active_user"] = None
    config._save_config()
    console.print(f"[bold green]✓ Logged out {active_user.username}[/bold green]")


@app.command("mkdir")
def create_folder(
    folder_name: str = typer.Argument(..., help="Name of the folder to create"),
    parent_id: Optional[str] = typer.Option(
        None,
        "--parent", "-p",
        help="Parent folder ID (default: root folder)",
    ),
):
    """
    Create a new folder.
    
    FOLDER_NAME: Name of the folder to create
    
    Examples:
        $ gofile-cli mkdir "My Documents"
        $ gofile-cli mkdir "Photos" --parent abc123
    """
    client = get_gofile_client()
    if not client:
        raise typer.Exit(1)
    
    try:
        # Get parent folder
        if not parent_id:
            profile = client.get_me()
            parent_id = profile.rootFolder
        
        result = client.create_folder(
            folder_name=folder_name,
            parent_folder_id=parent_id,
        )
        
        if result.status == "ok":
            console.print(f"[bold green]✓ Created folder '{folder_name}' with ID: {result.data.id}[/bold green]")
        else:
            console.print(f"[bold red]Error creating folder:[/bold red] {result.status}")
            raise typer.Exit(1)
    
    except Exception as e:
        console.print(f"[bold red]Failed to create folder:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.command("delete")
def delete_content(
    content_id: str = typer.Argument(..., help="ID of content to delete"),
    recursive: bool = typer.Option(
        False,
        "--recursive", "-r",
        help="Delete recursively (for folders)",
    ),
):
    """
    Delete content (file or folder).
    
    CONTENT_ID: ID of the content to delete
    
    Examples:
        $ gofile-cli delete abc123
        $ gofile-cli delete xyz789 --recursive
    """
    client = get_gofile_client()
    if not client:
        raise typer.Exit(1)
    
    try:
        # Confirm deletion
        if not typer.confirm(f"Are you sure you want to delete {content_id}?"):
            console.print("[yellow]Deletion cancelled.[/yellow]")
            raise typer.Exit(0)
        
        result = client.delete_contents(content_id)
        
        if result.status == "ok":
            console.print(f"[bold green]✓ Successfully deleted {content_id}[/bold green]")
        else:
            console.print(f"[bold red]Error deleting content:[/bold red] {result.status}")
            raise typer.Exit(1)
    
    except Exception as e:
        console.print(f"[bold red]Deletion failed:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.command("info")
def get_info(
    content_id: str = typer.Argument(..., help="ID of content to get information for"),
):
    """
    Get detailed information about content.
    
    CONTENT_ID: ID of the content
    
    Examples:
        $ gofile-cli info abc123
    """
    client = get_gofile_client()
    if not client:
        raise typer.Exit(1)
    
    try:
        content_info = client.get_content_info(content_id)
        
        if content_info.data.type == "file":
            file_info = content_info.data
            table = Table(
                title=f"File Information (ID: {content_id})",
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Name", file_info.name)
            table.add_row("Type", file_info.type.capitalize())
            table.add_row("Size", convert_bytes_to_readable(file_info.size))
            table.add_row(
                "Created",
                datetime.fromtimestamp(file_info.createTime, tz=timezone.utc).strftime(time_format),
            )
            table.add_row(
                "Modified",
                datetime.fromtimestamp(file_info.modTime, tz=timezone.utc).strftime(time_format),
            )
            table.add_row("Link", f"[blue underline]{file_info.link}[/blue underline]")
            
            console.print(table)
        else:
            console.print(f"[bold blue]Folder ID:[/bold blue] {content_id}")
            console.print(f"[bold blue]Name:[/bold blue] {content_info.data.name}")
    
    except Exception as e:
        console.print(f"[bold red]Error getting info:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version", "-v",
        help="Show version and exit",
    ),
):
    """
    GoFile CLI - A powerful command-line tool for GoFile.io
    
    Use 'gofile-cli <command> --help' for more information about a command.
    """
    if version:
        console.print("[bold]GoFile CLI[/bold] version 1.0.0")
        raise typer.Exit()
    
    if ctx.invoked_subcommand is None:
        console.print("""
[bold cyan]╔════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║[/bold cyan]       [bold white]Welcome to GoFile CLI![/bold white]          [bold cyan]║[/bold cyan]
[bold cyan]╚════════════════════════════════════════════╝[/bold cyan]

[bold]Quick Start:[/bold]
  [green]gofile-cli login --new[/green]     Create a new account
  [green]gofile-cli upload <file>[/green]   Upload a file
  [green]gofile-cli download <id>[/green]   Download a file
  [green]gofile-cli ls[/green]              List folder contents

[bold]Common Commands:[/bold]
  [cyan]upload[/cyan]     Upload files to GoFile
  [cyan]download[/cyan]   Download files from GoFile
  [cyan]ls[/cyan]         List folder contents
  [cyan]login[/cyan]      Login or create account
  [cyan]logout[/cyan]     Logout current user
  [cyan]mkdir[/cyan]      Create new folder
  [cyan]delete[/cyan]     Delete content
  [cyan]info[/cyan]       Get content information

[dim]Use 'gofile-cli <command> --help' for detailed command help.[/dim]
""")


if __name__ == "__main__":
    app()
