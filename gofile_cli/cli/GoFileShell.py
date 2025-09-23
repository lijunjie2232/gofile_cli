import cmd
import argparse
from gofile_cli.api import GoFile
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# 模拟 gofile 实例
auth_token = "ydbMfBeWdZ2yJz1R09jwd8gHz8i4V08T"
gofile = GoFile(auth_token)


class GoFileShell(cmd.Cmd):
    intro = "欢迎使用 GoFile Shell。输入 help 或 ? 查看帮助。\n"
    prompt = "[bold cyan](gofile-shell) [/bold cyan]"

    def __init__(self):
        super().__init__()
        self.parser = self._create_parser()

    def _create_parser(self):
        parser = argparse.ArgumentParser(prog="command")
        subparsers = parser.add_subparsers(dest="command")

        # upload 命令
        upload_parser = subparsers.add_parser("upload", help="上传文件到指定文件夹")
        upload_parser.add_argument("file_path", type=str, help="要上传的文件路径")
        upload_parser.add_argument("folder_id", type=str, help="目标文件夹 ID")

        # download 命令
        download_parser = subparsers.add_parser("download", help="下载指定文件")
        download_parser.add_argument("file_id", type=str, help="要下载的文件 ID")
        download_parser.add_argument("output_path", type=str, help="保存路径")

        # list 命令
        list_parser = subparsers.add_parser("ls", help="列出指定目录下的内容")
        list_parser.add_argument("folder_id", type=str, help="要列出的目录 ID")

        # login 命令
        login_parser = subparsers.add_parser("login", help="登录")
        login_parser.add_argument("gofile_token", type=str, help="gofile授权令牌")
        login_parser.add_argument("mailtm_token", type=str, help="mailtm授权令牌")
        login_parser.add_argument("username", type=str, help="邮箱")
        login_parser.add_argument("password", type=str, help="密码")

        return parser

    def do_run(self, line):
        args = self.parser.parse_args(line.split())
        # autowire to call related method
        action = getattr(self, args.command)
        pass


if __name__ == "__main__":
    GoFileShell().cmdloop()
