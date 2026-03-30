import argparse
import cmd

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from gofile_cli.api import GoFile

console = Console()

# Mock gofile instance
auth_token = "ydbMfBeWdZ2yJz1R09jwd8gHz8i4V08T"
gofile = GoFile(auth_token)


class GoFileShell(cmd.Cmd):
    intro = "Welcome to GoFile Shell. Type 'help' or '?' for help.\n"
    prompt = "[bold cyan](gofile-shell) [/bold cyan]"

    def __init__(self):
        super().__init__()
        self.parser = self._create_parser()

    def _create_parser(self):
        parser = argparse.ArgumentParser(prog="command")
        subparsers = parser.add_subparsers(dest="command")

        # upload command
        upload_parser = subparsers.add_parser("upload", help="Upload file to specified folder")
        upload_parser.add_argument("file_path", type=str, help="Path to file to upload")
        upload_parser.add_argument("folder_id", type=str, help="Destination folder ID")

        # download command
        download_parser = subparsers.add_parser("download", help="Download specified file")
        download_parser.add_argument("file_id", type=str, help="File ID to download")
        download_parser.add_argument("output_path", type=str, help="Save path")

        # list command
        list_parser = subparsers.add_parser("ls", help="List contents of specified directory")
        list_parser.add_argument("folder_id", type=str, help="Directory ID to list")

        # login command
        login_parser = subparsers.add_parser("login", help="Login to account")
        login_parser.add_argument("gofile_token", type=str, help="GoFile authorization token")
        login_parser.add_argument("mailtm_token", type=str, help="MailTM authorization token")
        login_parser.add_argument("username", type=str, help="Email address")
        login_parser.add_argument("password", type=str, help="Password")

        return parser

    def do_run(self, line):
        args = self.parser.parse_args(line.split())
        # autowire to call related method
        action = getattr(self, args.command)
        pass


if __name__ == "__main__":
    GoFileShell().cmdloop()
