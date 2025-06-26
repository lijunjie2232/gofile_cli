from requests import post, get, Session
from gofile_cli.entity import Account
from gofile_cli.entity.gofile import (
    ProfileData,
    Profile,
    ContentInfo,
    FileContentInfo,
    FolderContentInfo,
    ContentCreateInfo,
    ContentDeleteInfo,
    ContentUploadInfo,
)
from gofile_cli.utils import calculate_md5
import re
from pathlib import Path
import logging
import hashlib
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
    TimeElapsedColumn,
)
from contextlib import nullcontext
from requests_toolbelt.multipart.encoder import (
    MultipartEncoder,
    MultipartEncoderMonitor,
)


logger = logging.getLogger("GoFile")

# appdata.wt = "4fd6sg89d7s6"
WT_PATTERN = re.compile(r"appdata.wt.*?=.*?\"(.*?)\"")


class GoFile:

    base_url = "https://api.gofile.io"
    upload_url = "https://upload.gofile.io/uploadfile"
    global_js_url = "https://gofile.io/dist/js/global.js"

    def __init__(
        self,
        authorization_token,
        session: Session = None,
    ):
        self.token = authorization_token
        self.session = session or Session()
        self.session.headers.update(self._get_headers())
        self.wt = GoFile.get_wt()

    @staticmethod
    def get_wt():
        response = get(GoFile.global_js_url)
        result = WT_PATTERN.findall(response.text)
        if result:
            return result[0]

    def _get_headers(
        self,
    ):
        return {
            "authorization": f"Bearer {self.token}",
        }

    @staticmethod
    def get_link(mail: Account | str):
        if isinstance(mail, Account):
            mail = mail.address
        else:
            assert isinstance(mail, str), "mail must be a string or Account"
        response = post(
            url=f"{GoFile.base_url}/accounts",
            json={
                "email": mail,
            },
        )
        if response.status_code == 200:
            return response.json()

    def get_me(self) -> Profile:
        url = f"{self.base_url}/accounts/website"
        response = self.session.get(
            url,
        )
        return ProfileData(**response.json()).profile

    def upload_file(
        self,
        file_path,
        folder_id=None,
        progress_bar=True,
    ):
        file_path = Path(file_path)
        file_size = file_path.stat().st_size
        file_name = file_path.name

        progress_columns = (
            TextColumn(
                "[bold blue]%s" % file_name,
                justify="right",
            ),
            BarColumn(
                bar_width=None,
            ),
            DownloadColumn(),
            TransferSpeedColumn(),
            "•",
            TimeRemainingColumn(),
            TimeElapsedColumn(),
            "•",
            TextColumn("{task.percentage:>3.0f}%"),
        )
        with Progress(
            *progress_columns,
        ) as progress:
            task_id = progress.add_task("Upload", total=file_size, completed=0)

            data = {
                "token": self.token,
            }
            if folder_id:
                data["folderId"] = folder_id
            m = MultipartEncoder(
                fields={
                    "file": (
                        file_name,
                        open(file_path, "rb"),
                    ),
                    **{k: str(v) for k, v in data.items()},
                }
            )

            # 封装 encoder，监控上传进度
            monitor = MultipartEncoderMonitor(
                m,
                lambda monitor: progress.update(
                    task_id,
                    completed=monitor.bytes_read,
                ),
            )

            headers = {
                "Content-Type": monitor.content_type,
            }

            response = self.session.post(
                self.upload_url,
                data=monitor,
                headers=headers,
            )

            return ContentUploadInfo(**response.json())

    def download_file(
        self,
        id=None,
        link=None,
        output_path=None,
        chunk_size=1024 * 64,
        overwrite=False,
        verify=False,
        show_process_bar=True,
    ):
        assert link or id, "Either link or file id must be provided"
        if verify:
            assert id, "id must be provided if need verify"
        id_data = None
        if id:
            id_data = self.get_content_info(id)
            assert (
                id_data.data and id_data.data.type == "file" and id_data.data.link
            ), "File is not valid"
            link = link or id_data.data.link
        if not output_path:
            output_path = link.split("/")[-1]
        output_path = Path(output_path)

        if output_path.exists() and not overwrite:
            raise FileExistsError(f"File {output_path} already exists")

        tmp_file = output_path.parent.resolve() / f"{output_path.name}.tmp"

        # Check if file exists and get its size
        headers = self.session.headers.copy()
        headers["Cookie"] = f"accountToken={self.token}"
        downloaded_size = 0
        if tmp_file.is_file():
            downloaded_size = tmp_file.stat().st_size
            headers["Range"] = f"bytes={downloaded_size}-"
        else:
            headers["Range"] = ""
            tmp_file.parent.mkdir(parents=True, exist_ok=True)

        with open(tmp_file, "ab") as f:  # Open in append mode
            r = self.session.get(
                link,
                headers=headers,
                stream=True,
            )
            r.raise_for_status()
            # Check if file exists and get its size
            total_size = (
                int(
                    r.headers.get(
                        "Content-Length",
                        0,
                    )
                )
                + downloaded_size
            )

            # 使用 rich 显示进度条
            progress_desc = TextColumn(
                "[bold blue]{task.fields[filename]}", justify="right"
            )
            bar = BarColumn(bar_width=None)
            progress_download = DownloadColumn()
            progress_time_remain = TimeRemainingColumn()
            progress_time_ela = TimeElapsedColumn()
            progress_speed = TransferSpeedColumn()
            progress_percentage = TextColumn("{task.percentage:>3.0f}%")

            with Progress(
                progress_desc,
                bar,
                progress_download,
                progress_time_remain,
                "/",
                progress_time_ela,
                progress_speed,
                progress_percentage,
                expand=True,
            ) as progress:
                if show_process_bar:
                    task_id = progress.add_task(
                        "Download",
                        filename=output_path.name,
                        total=total_size,
                        downloaded=downloaded_size,
                    )
                    if downloaded_size:
                        progress.update(
                            task_id,
                            completed=downloaded_size,
                            refresh=True,
                        )

                for chunk in r.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if show_process_bar:
                            progress.update(
                                task_id,
                                advance=len(chunk),
                                completed=downloaded_size,
                                refresh=True,
                            )

        if verify:
            if not calculate_md5(tmp_file, id_data.data.md5):
                tmp_file.unlink()
                raise ValueError("MD5 sum does not match, download failed.")
            print("MD5 sum matched")

        tmp_file.rename(output_path)

        print("Download completed.")

    def create_folder(
        self,
        # Optional: Print progress or update a progress bar
        folder_name=None,
    ) -> ContentCreateInfo:
        url = f"{self.base_url}/contents/createFolder"

        data = {"parentFolderId": parent_folder_id}

        if folder_name:
            data["folderName"] = folder_name

        response = self.session.post(
            url,
            json=data,
        )

        return ContentCreateInfo(**response.json())

    def update_content(
        self,
        content_id,
        attribute,
        attribute_value,
    ):
        valid_attributes = [
            "name",
            "description",
            "tags",
            "public",
            "expiry",
            "password",
        ]

        if attribute not in valid_attributes:
            raise ValueError(
                "Invalid attribute. Must be one of %s" % valid_attributes,
            )

        url = f"{self.base_url}/contents/{content_id}/update"

        data = {
            "attribute": attribute,
            "attributeValue": attribute_value,
        }

        response = self.session.put(
            url,
            json=data,
        )

        return response.json()

    def delete_contents(
        self,
        contents_id,
    ) -> ContentDeleteInfo:
        url = f"{self.base_url}/contents"
        data = {"contentsId": contents_id}

        response = self.session.delete(
            url,
            json=data,
        )

        return ContentDeleteInfo(**response.json())

    def get_content_info(
        self,
        content_id: str,
        password_hash=None,
        contentFilter=None,
        page: int = 1,
        pageSize: int = 20,
        sortField: str = "name",
        sortDirection: int = 1,
    ) -> FolderContentInfo | FileContentInfo:
        url = f"{self.base_url}/contents/{content_id}"

        params = {
            "contentFilter": contentFilter,
            "page": page,
            "pageSize": pageSize,
            "sortField": sortField,
            "sortDirection": sortDirection,
            "wt": self.wt,
        }
        if password_hash:
            params["password"] = (password_hash,)

        response = self.session.get(
            url,
            params=params,
        )
        data = response.json()
        content_type = data["data"].get("type", "folder")
        if content_type == "folder":
            return FolderContentInfo(**data)
        elif content_type == "file":
            return FileContentInfo(**data)

    def search_content(
        self,
        content_id,
        searched_string,
    ):
        url = f"{self.base_url}/contents/search"

        params = {"contentId": content_id, "searchedString": searched_string}

        response = self.session.get(
            url,
            params=params,
        )
        return response.json()

    def create_direct_link(
        self,
        content_id,
        expire_time=None,
        source_ips_allowed=None,
        domains_allowed=None,
        auth=None,
    ):
        url = f"{self.base_url}/contents/{content_id}/directlinks"

        data = {}

        if expire_time:
            data["expireTime"] = expire_time

        if source_ips_allowed:
            data["sourceIpsAllowed"] = source_ips_allowed

        if domains_allowed:
            data["domainsAllowed"] = domains_allowed

        if auth:
            data["auth"] = auth

        response = self.session.post(
            url,
            json=data,
        )
        return response.json()

    def update_direct_link(
        self,
        content_id,
        direct_link_id,
        expire_time=None,
        source_ips_allowed=None,
        domains_allowed=None,
        auth=None,
    ):
        url = f"{self.base_url}/contents/{content_id}/directlinks/{direct_link_id}"

        data = {}

        if expire_time:
            data["expireTime"] = expire_time

        if source_ips_allowed:
            data["sourceIpsAllowed"] = source_ips_allowed

        if domains_allowed:
            data["domainsAllowed"] = domains_allowed

        if auth:
            data["auth"] = auth

        response = self.session.put(
            url,
            json=data,
        )
        return response.json()

    def delete_direct_link(
        self,
        content_id,
        direct_link_id,
    ):
        url = f"{self.base_url}/contents/{content_id}/directlinks/{direct_link_id}"

        response = self.session.delete(
            url,
        )
        return response.json()

    def copy_contents(
        self,
        contents_id,
        folder_id,
    ):
        url = f"{self.base_url}/contents/copy"

        data = {"contentsId": contents_id, "folderId": folder_id}

        response = self.session.post(
            url,
            json=data,
        )
        return response.json()

    def move_contents(
        self,
        contents_id,
        folder_id,
    ):
        url = f"{self.base_url}/contents/move"

        data = {"contentsId": contents_id, "folderId": folder_id}

        response = self.session.put(
            url,
            json=data,
        )
        return response.json()

    def import_public_content(
        self,
        contents_id,
    ):
        url = f"{self.base_url}/contents/import"

        data = {"contentsId": contents_id}

        response = self.session.post(
            url,
            json=data,
        )
        return response.json()

    def get_account_id(
        self,
    ):
        url = f"{self.base_url}/accounts/getid"

        response = self.session.get(
            url,
        )
        return response.json()

    def get_account_info(
        self,
        account_id,
    ) -> Profile:
        url = f"{self.base_url}/accounts/{account_id}"

        response = self.session.get(
            url,
        )
        return ProfileData(**response.json()).profile

    def reset_api_token(
        self,
        account_id,
    ):
        url = f"{self.base_url}/accounts/{account_id}/resettoken"

        response = self.session.post(
            url,
        )
        return response.json()
