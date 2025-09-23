import cmd
import argparse
from gofile_cli.api import GoFile, MailTM
from gofile_cli.config import (
    CONFIG,
    MailTMUser,
    GoFileUser,
)
from gofile_cli.entity.mailtm import Token
from gofile_cli.utils import (
    message_filter,
    convert_bytes_to_readable,
)
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from traceback import print_exc
from datetime import datetime, timezone

time_format = "%Y-%m-%d %H:%M:%S"


class GoFileShell(cmd.Cmd):
    intro = "欢迎使用 GoFile Shell。输入 help 查看帮助。\n"
    prompt = "[bold green](gofile-shell)>[/bold green]"
    myconfig = CONFIG
    console = Console()
    mailtm = MailTM()
    current_mail = None
    current_gofile = None
    current_profile = None

    def cmdloop(self, intro=None):
        """Repeatedly issue a prompt, accept input, parse an initial prefix
        off the received input, and dispatch to action methods, passing them
        the remainder of the line as argument.

        """

        self.preloop()
        if self.use_rawinput and self.completekey:
            try:
                import readline

                self.old_completer = readline.get_completer()
                readline.set_completer(self.complete)

                # Check if backend attribute exists and handle accordingly
                if hasattr(readline, "backend") and readline.backend == "editline":
                    if self.completekey == "tab":
                        # libedit uses "^I" instead of "tab"
                        command_string = "bind ^I rl_complete"
                    else:
                        command_string = f"bind {self.completekey} rl_complete"
                else:
                    command_string = f"{self.completekey}: complete"

                readline.parse_and_bind(command_string)
            except ImportError:
                pass
        try:
            if intro is not None:
                self.intro = intro
            if self.intro:
                self.stdout.write(str(self.intro) + "\n")
            stop = None
            while not stop:
                try:
                    if self.cmdqueue:
                        line = self.cmdqueue.pop(0)
                    else:
                        if self.use_rawinput:
                            try:
                                line = input(
                                    self.console.print(
                                        self.prompt,
                                        end="",
                                    )
                                    or " "
                                )
                            except EOFError:
                                line = "EOF"
                        else:
                            self.stdout.write(self.prompt)
                            self.stdout.flush()
                            line = self.stdin.readline()
                            if not len(line):
                                line = "EOF"
                            else:
                                line = line.rstrip("\r\n")
                    line = self.precmd(line)
                    stop = self.onecmd(line)
                    stop = self.postcmd(stop, line)
                except KeyboardInterrupt:
                    self.console.print("\n[bold red]退出中...[/bold red]")
                    break
                except Exception as e:
                    # Handle exceptions from commands - print error and continue or exit
                    self.console.print(f"[bold red]Error: {str(e)}[/bold red]")
                    # If you want to exit on any exception, uncomment the next line:
                    # stop = True
                    # Or for specific exceptions like SystemExit, you could do:
                    # if isinstance(e, SystemExit):
                    #     raise
                    pass
            self.postloop()
        finally:
            if self.use_rawinput and self.completekey:
                try:
                    import readline

                    readline.set_completer(self.old_completer)
                except ImportError:
                    pass

    def __init__(self):
        super().__init__()
        self.parser = self._create_parser()

    def check_init(self):
        if not self.current_mail or not self.current_gofile:
            self.console.print("[bold red]please login first[/bold red]")
            raise Exception("not init")
        if not self.current_profile:
            self.current_profile = self.current_gofile.get_me()

    def _create_parser(self):
        parser = argparse.ArgumentParser(prog="")
        subparsers = parser.add_subparsers(dest="")

        # upload 命令
        upload_parser = subparsers.add_parser(
            "upload",
            help="上传文件到指定文件夹",
        )
        upload_parser.add_argument(
            "file_path",
            type=str,
            default="",
            help="要上传的文件路径",
        )
        upload_parser.add_argument(
            "--id",
            type=str,
            default="",
            help="目标文件夹 ID",
        )

        # download 命令
        download_parser = subparsers.add_parser(
            "download",
            help="下载指定文件",
        )
        download_parser.add_argument(
            "id",
            type=str,
            help="要下载的文件 ID",
        )
        download_parser.add_argument(
            "output_path",
            type=str,
            help="保存路径",
        )
        download_parser.add_argument(
            "--verify",
            action="store_true",
            help="验证文件",
        )
        download_parser.add_argument(
            "--overwrite",
            action="store_true",
            help="覆盖同名文件",
        )

        # list 命令
        list_parser = subparsers.add_parser(
            "ls",
            help="列出指定目录下的内容",
        )
        list_parser.add_argument(
            "--id",
            type=str,
            default="",
            help="要列出的目录 ID",
        )

        # login 命令
        login_parser = subparsers.add_parser("login", help="登录")
        login_parser.add_argument(
            "--view_only",
            action="store_true",
            help="show storaged account only",
        )
        login_parser.add_argument(
            "--new",
            action="store_true",
            help="新建账号",
        )

        return parser

    def do_help(self, line):
        self.parser.print_help()

    def do_upload(self, line):
        try:
            args = self.parser.parse_args(("upload", *line.split()))
        except:
            return
        if "-h" in line or "--help" in line:
            # raise Exception("print help")
            return
        self.check_init()
        try:
            result = self.current_gofile.upload_file(
                args.file_path,
                folder_id=(
                    args.folder_id
                    if args.folder_id
                    else self.current_profile.rootFolder
                ),
            )
            assert result.status == "ok", f"{result.status}"
        except Exception as e:
            print_exc()
            raise e
        file_info = result.data
        table = Table(
            title="文件信息",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column(
            "属性",
            style="cyan",
        )
        table.add_column(
            "值",
            style="green",
        )

        table.add_row(
            "名称",
            file_info.name,
        )
        table.add_row(
            "类型",
            file_info.type.capitalize(),
        )
        table.add_row(
            "大小",
            convert_bytes_to_readable(file_info.size),
        )
        table.add_row(
            "创建时间",
            datetime.fromtimestamp(
                file_info.createTime,
                tz=timezone.utc,
            ).strftime(time_format),
        )
        table.add_row(
            "修改时间",
            datetime.fromtimestamp(
                file_info.modTime,
                tz=timezone.utc,
            ).strftime(time_format),
        )
        self.console.print(table)

    def do_download(self, line):
        try:
            args = self.parser.parse_args(("download", *line.split()))
        except:
            # print_exc()
            return
            # raise e
        if "-h" in line or "--help" in line:
            # raise Exception("print help")
            return
        self.check_init()

        try:
            self.current_gofile.download_file(
                id=args.id,
                output_path=args.output_path,
                overwrite=args.overwrite,
                verify=args.verify,
            )
        except Exception as e:
            print_exc()
            # raise e

    def do_ls(self, line):
        try:
            args = self.parser.parse_args(("ls", *line.split()))
        except:
            return
            # print_exc()
        if "-h" in line or "--help" in line:
            # raise Exception("print help")
            return
            # raise e
        self.check_init()
        id = None
        current_info = None
        if args.id:
            id = args.id
        else:
            id = self.current_profile.rootFolder
        try:
            current_info = self.current_gofile.get_content_info(id)
        except Exception as e:
            print_exc()
            # raise e

        assert current_info, "something wrong"

        if current_info.data.type == "folder":
            file_list = current_info.data.children
            table = Table(title=f"id={id}")
            table.add_column("name", style="green")
            table.add_column("ID", style="cyan")
            table.add_column("type", style="magenta")
            table.add_column("public", style="yellow")
            table.add_column("size", style="blue")
            table.add_column("create time", style="red")
            table.add_column("modify time", style="blue")
            table.add_column("children", style="yellow")

            for k, v in file_list.items():
                if v["type"] == "folder":
                    table.add_row(
                        v["name"],
                        k,
                        "d" if v["type"] == "folder" else "-",
                        "o" if v["public"] else "x",
                        convert_bytes_to_readable(v["totalSize"]),
                        datetime.fromtimestamp(
                            v["createTime"],
                            tz=timezone.utc,
                        ).strftime(time_format),
                        datetime.fromtimestamp(
                            v["modTime"],
                            tz=timezone.utc,
                        ).strftime(time_format),
                        str(v["childrenCount"]),
                    )
                else:
                    table.add_row(
                        v["name"],
                        k,
                        "d" if v["type"] == "folder" else "-",
                        "-",
                        convert_bytes_to_readable(v["size"]),
                        datetime.fromtimestamp(
                            v["createTime"],
                            tz=timezone.utc,
                        ).strftime(time_format),
                        datetime.fromtimestamp(
                            v["modTime"],
                            tz=timezone.utc,
                        ).strftime(time_format),
                        "-",
                    )
            self.console.print(table)
        elif current_info.data.type == "file":
            file_info = current_info.data
            table = Table(
                title="文件信息",
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column(
                "属性",
                style="cyan",
            )
            table.add_column(
                "值",
                style="green",
            )

            table.add_row(
                "名称",
                file_info.name,
            )
            table.add_row(
                "类型",
                file_info.type.capitalize(),
            )
            table.add_row(
                "大小",
                convert_bytes_to_readable(file_info.size),
            )
            table.add_row(
                "创建时间",
                datetime.fromtimestamp(
                    file_info.createTime,
                    tz=timezone.utc,
                ).strftime(time_format),
            )
            table.add_row(
                "修改时间",
                datetime.fromtimestamp(
                    file_info.modTime,
                    tz=timezone.utc,
                ).strftime(time_format),
            )
            table.add_row(
                "下载链接",
                file_info.link,
            )
            self.console.print(table)

    def do_login(self, line):
        try:
            args = self.parser.parse_args(("login", *line.split()))
        except:
            return
        if "-h" in line or "--help" in line:
            # raise Exception("print help")
            return

        if args.new:
            rand_user = input(
                self.console.print(
                    "is new user with random info? [Y/n]",
                    end="",
                )
                or " "
            )
            if rand_user == "" or rand_user.lower() == "y":
                maccount, username, password = self.mailtm.create_account()
                MailTMUser.get_or_create(
                    username=username,
                    password=password,
                    token=maccount.token.token,
                    token_id=maccount.token.id,
                )
                result = GoFile.get_link(maccount)
                if result.get("status") != "ok":
                    self.console.print("error while get link")
                    raise Exception("error while get link")
                auth = message_filter(self.mailtm, maccount)
                gofile = GoFile(auth)
                GoFileUser.get_or_create(
                    username=username,
                    token=auth,
                )
                self.current_mail = maccount
                self.current_gofile = gofile
                self.current_profile = gofile.get_me()

        else:
            # 查看mtmail账户
            users = MailTMUser.select()
            table = Table(title="Stored MailTM Users")
            table.add_column("Id", style="cyan")
            table.add_column("Username", style="magenta")
            table.add_column("Password", style="green")
            # table.add_column("Token", style="blue")
            # Add rows to the table
            for id, user in enumerate(users):
                table.add_row(
                    str(id),
                    user.username,
                    user.password,
                    # user.token,
                )
            # Print the table
            self.console.print(table)

            # 查看gofile账户
            gofiles = GoFileUser.select()
            table = Table(title="Stored GoFile Users")
            table.add_column("Id", style="cyan")
            table.add_column("Username", style="magenta")
            table.add_column("Token", style="blue")
            table.add_column("Comment", style="white")
            for id, gofile in enumerate(gofiles):
                table.add_row(
                    str(id),
                    gofile.username,
                    gofile.token,
                    gofile.comment,
                )
            self.console.print(table)

            if args.view_only:
                raise UserWarning("view only")
            username = input(
                self.console.print(
                    "select mailtm username or id:",
                    end="",
                )
                or " "
            )
            username = username.strip()
            if username.isdigit():
                username = users[int(username)].username

            try:
                mail = MailTMUser.get(MailTMUser.username == username)
                self.current_mail = self.mailtm.get_me(
                    Token(
                        id=mail.token_id,
                        token=mail.token,
                    ),
                )
            except Exception as e:
                # raise e
                is_delete = input(
                    self.console.print(
                        "delete current mailtm? [y/N]:",
                        end="",
                    )
                    or " "
                )
                if is_delete.lower() == "y":
                    MailTMUser.delete(MailTMUser.username == username)

            gofile = GoFileUser.get(GoFileUser.username == username)
            try:
                self.current_gofile = GoFile(
                    gofile.token,
                    username=gofile.username,
                )
                self.current_profile = self.current_gofile.get_me()
            except Exception as e:
                # raise e
                is_delete = input(
                    self.console.print(
                        "delete current gofile? [y/N]:",
                        end="",
                    )
                    or " "
                )
                if is_delete.lower() == "y":
                    GoFileUser.delete(GoFileUser.username == username)


if __name__ == "__main__":
    GoFileShell().cmdloop()
    pass
