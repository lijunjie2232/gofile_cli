"""
GoFile API Client Module

This module provides a comprehensive Python client for the GoFile.io file hosting service.
It enables file upload, download, folder management, and content operations through
a simple and intuitive interface.

Main Classes:
    GoFile: Primary class for interacting with GoFile API endpoints.

Example Usage:
    >>> from gofile_cli.api import GoFile
    >>> gofile = GoFile(authorization_token="your_token")
    >>> profile = gofile.get_me()
    >>> print(f"Logged in as: {profile.email}")
"""

import hashlib
import logging
import re
from contextlib import nullcontext
from pathlib import Path
from typing import Optional, Union

from requests import Session, get, post
from requests_toolbelt.multipart.encoder import (MultipartEncoder,
                                                 MultipartEncoderMonitor)
from rich.progress import (BarColumn, DownloadColumn, Progress, TextColumn,
                           TimeElapsedColumn, TimeRemainingColumn,
                           TransferSpeedColumn)

from gofile_cli.entity import Account
from gofile_cli.entity.gofile import (ContentCreateInfo, ContentDeleteInfo,
                                      ContentInfo, ContentUploadInfo,
                                      FileContentInfo, FolderContentInfo,
                                      Profile, ProfileData)
from gofile_cli.utils import calculate_md5

logger = logging.getLogger("GoFile")

# appdata.wt = "4fd6sg89d7s6"
WT_PATTERN = re.compile(r"appdata.wt.*?=.*?\"(.*?)\"")


class GoFile:
    """
    A comprehensive client for the GoFile.io file hosting service API.
    
    This class provides methods for all GoFile API operations including:
    - User authentication and profile management
    - File upload and download with progress tracking
    - Folder creation and content organization
    - Content metadata retrieval and modification
    - Direct link management
    
    Attributes:
        token (str): Authorization token for API access.
        username (str, optional): Username of the authenticated user.
        session (Session): Requests session for HTTP operations.
        wt (str): WT parameter extracted from GoFile's global.js.
    
    Example:
        >>> gofile = GoFile(authorization_token="abc123")
        >>> profile = gofile.get_me()
        >>> print(profile.email)
    """

    base_url = "https://api.gofile.io"
    upload_url = "https://upload.gofile.io/uploadfile"
    global_js_url = "https://gofile.io/dist/js/global.js"

    def __init__(
        self,
        authorization_token: str,
        username: Optional[str] = None,
        session: Optional[Session] = None,
    ):
        """
        Initialize a GoFile client instance.
        
        Args:
            authorization_token: Bearer token for API authentication.
            username: Optional username for display purposes.
            session: Optional Requests session. If not provided, a new session is created.
        """
        self.token = authorization_token
        self.username = username
        self.session = session or Session()
        self.session.headers.update(self._get_headers())
        self._wt_cache: Optional[str] = None

    @staticmethod
    def get_wt() -> Optional[str]:
        """
        Extract the WT (write token) parameter from GoFile's global JavaScript file.
        
        The WT parameter is required for certain API operations. This method scrapes
        it from the official GoFile website.
        
        Returns:
            str or None: The WT parameter if found, None otherwise.
        """
        try:
            response = get(GoFile.global_js_url, timeout=10)
            result = WT_PATTERN.findall(response.text)
            return result[0] if result else None
        except Exception as e:
            logger.warning(f"Failed to fetch WT parameter: {e}")
            return None

    @property
    def wt(self) -> Optional[str]:
        """
        Get WT parameter with caching.
        
        Returns:
            The WT parameter if found, None otherwise.
        """
        if self._wt_cache is None:
            self._wt_cache = GoFile.get_wt()
        return self._wt_cache

    def _get_headers(self) -> dict:
        """
        Generate HTTP headers with authorization.
        
        Returns:
            dict: Dictionary containing authorization headers.
        """
        return {
            "authorization": f"Bearer {self.token}",
        }

    @staticmethod
    def get_link(mail: Union[Account, str]) -> dict:
        """
        Get a registration link sent to the specified email address.
        
        This method initiates the account creation process by requesting
        an authentication link to be sent to the provided email.
        
        Args:
            mail: Either an Account object or email address string.
        
        Returns:
            dict: API response containing the status of the link request.
        
        Example:
            >>> result = GoFile.get_link("user@example.com")
            >>> if result.get('status') == 'ok':
            ...     print("Link sent successfully")
        """
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
        return {}

    def get_me(self) -> Profile:
        """
        Get the profile information of the authenticated user.
        
        Returns:
            Profile: User profile object containing account details.
        
        Example:
            >>> profile = gofile.get_me()
            >>> print(f"Email: {profile.email}")
            >>> print(f"Root Folder ID: {profile.rootFolder}")
        """
        url = f"{self.base_url}/accounts/website"
        response = self.session.get(
            url,
        )
        return ProfileData(**response.json()).profile

    def upload_file(
        self,
        file_path: Union[str, Path],
        folder_id: Optional[str] = None,
        progress_bar: bool = True,
    ) -> ContentUploadInfo:
        """
        Upload a file to GoFile.
        
        Args:
            file_path: Path to the file to upload.
            folder_id: Optional destination folder ID. If None, uploads to root folder.
            progress_bar: Whether to display upload progress. Defaults to True.
        
        Returns:
            ContentUploadInfo: Object containing uploaded file information.
        
        Raises:
            FileNotFoundError: If the specified file does not exist.
        
        Example:
            >>> result = gofile.upload_file("/path/to/file.txt")
            >>> print(f"Uploaded file ID: {result.data.id}")
        """
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
            
            def open_file():
                return open(file_path, "rb")
            
            m = MultipartEncoder(
                fields={
                    "file": (
                        file_name,
                        open_file(),
                    ),
                    **{k: str(v) for k, v in data.items()},
                }
            )

            # Wrap encoder to monitor upload progress
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
        id: Optional[str] = None,
        link: Optional[str] = None,
        output_path: Optional[Union[str, Path]] = None,
        chunk_size: int = 1024 * 64,
        overwrite: bool = False,
        verify: bool = False,
        show_process_bar: bool = True,
    ) -> None:
        """
        Download a file from GoFile.
        
        Args:
            id: File ID to download. Either this or 'link' must be provided.
            link: Direct download link. Either this or 'id' must be provided.
            output_path: Destination path for the downloaded file.
            chunk_size: Size of chunks to read at a time (bytes). Default: 64KB.
            overwrite: Whether to overwrite existing files. Default: False.
            verify: Whether to verify file integrity using MD5. Default: False.
            show_process_bar: Whether to display download progress. Default: True.
        
        Raises:
            AssertionError: If neither 'id' nor 'link' is provided.
            FileExistsError: If output file exists and overwrite is False.
            ValueError: If MD5 verification fails.
        
        Example:
            >>> gofile.download_file(id="abc123", output_path="./downloads/")
        """
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

            # Use rich to display progress bar
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
        folder_name: str = None,
        parent_folder_id: str = None,
    ) -> ContentCreateInfo:
        """
        Create a new folder.
        
        Args:
            folder_name: Name of the folder to create. If None, creates with default name.
            parent_folder_id: ID of the parent folder. If None, creates in root folder.
        
        Returns:
            ContentCreateInfo: Object containing the result of the folder creation.
        """
        url = f"{self.base_url}/contents/createFolder"

        data = {}
        
        if parent_folder_id:
            data["parentFolderId"] = parent_folder_id

        if folder_name:
            data["folderName"] = folder_name

        response = self.session.post(
            url,
            json=data,
        )

        return ContentCreateInfo(**response.json())

    def update_content(
        self,
        content_id: str,
        attribute: str,
        attribute_value: any,
    ) -> dict:
        """
        Update attributes of a content item (file or folder).
        
        Args:
            content_id: ID of the content to update.
            attribute: Attribute to update. Must be one of: name, description, tags, public, expiry, password.
            attribute_value: New value for the attribute.
        
        Returns:
            dict: API response containing the update result.
        
        Raises:
            ValueError: If the specified attribute is not valid.
        
        Example:
            >>> gofile.update_content("abc123", "name", "new_filename.txt")
        """
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
        contents_id: str,
    ) -> ContentDeleteInfo:
        """
        Delete content (file or folder) from GoFile.
        
        Args:
            contents_id: ID of the content to delete.
        
        Returns:
            ContentDeleteInfo: Object containing the deletion result.
        
        Example:
            >>> result = gofile.delete_contents("abc123")
            >>> if result.status == "ok":
            ...     print("Content deleted successfully")
        """
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
        password_hash: Optional[str] = None,
        contentFilter: Optional[str] = None,
        page: int = 1,
        pageSize: int = 1000,
        sortField: str = "name",
        sortDirection: int = 1,
    ) -> Union[FolderContentInfo, FileContentInfo]:
        """
        Get detailed information about a content item (file or folder).
        
        Args:
            content_id: ID of the content to retrieve.
            password_hash: Optional password hash for protected content.
            contentFilter: Optional filter for content type.
            page: Page number for pagination. Default: 1.
            pageSize: Number of items per page. Default: 1000.
            sortField: Field to sort by. Default: "name".
            sortDirection: Sort direction (1 for ascending, -1 for descending). Default: 1.
        
        Returns:
            FolderContentInfo or FileContentInfo: Content information object.
        
        Raises:
            FileNotFoundError: If the content does not exist.
        
        Example:
            >>> info = gofile.get_content_info("abc123")
            >>> print(f"Type: {info.data.type}, Name: {info.data.name}")
        """
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
            params["password"] = password_hash

        response = self.session.get(
            url,
            params=params,
        )
        data = response.json()
        assert data, FileNotFoundError()
        content_type = data["data"].get("type", "folder")
        if content_type == "folder":
            return FolderContentInfo(**data)
        elif content_type == "file":
            return FileContentInfo(**data)

    def search_content(
        self,
        content_id: str,
        searched_string: str,
    ) -> dict:
        """
        Search for content within a folder.
        
        Args:
            content_id: ID of the folder to search in.
            searched_string: Search query string.
        
        Returns:
            dict: API response containing search results.
        
        Example:
            >>> results = gofile.search_content("folder_id", "keyword")
        """
        url = f"{self.base_url}/contents/search"

        params = {"contentId": content_id, "searchedString": searched_string}

        response = self.session.get(
            url,
            params=params,
        )
        return response.json()

    def create_direct_link(
        self,
        content_id: str,
        expire_time: Optional[int] = None,
        source_ips_allowed: Optional[list] = None,
        domains_allowed: Optional[list] = None,
        auth: Optional[dict] = None,
    ) -> dict:
        """
        Create a direct link for a content item.
        
        Args:
            content_id: ID of the content to create a direct link for.
            expire_time: Optional expiration time in seconds.
            source_ips_allowed: Optional list of allowed source IP addresses.
            domains_allowed: Optional list of allowed domains.
            auth: Optional authentication configuration.
        
        Returns:
            dict: API response containing the created direct link information.
        
        Example:
            >>> result = gofile.create_direct_link("abc123")
        """

    def update_direct_link(
        self,
        content_id: str,
        direct_link_id: str,
        expire_time: Optional[int] = None,
        source_ips_allowed: Optional[list] = None,
        domains_allowed: Optional[list] = None,
        auth: Optional[dict] = None,
    ) -> dict:
        """
        Update an existing direct link.
        
        Args:
            content_id: ID of the content owning the direct link.
            direct_link_id: ID of the direct link to update.
            expire_time: Optional new expiration time in seconds.
            source_ips_allowed: Optional new list of allowed source IPs.
            domains_allowed: Optional new list of allowed domains.
            auth: Optional new authentication configuration.
        
        Returns:
            dict: API response containing the updated direct link information.
        
        Example:
            >>> result = gofile.update_direct_link("abc123", "link_id", expire_time=3600)
        """

    def delete_direct_link(
        self,
        content_id: str,
        direct_link_id: str,
    ) -> dict:
        """
        Delete a direct link.
        
        Args:
            content_id: ID of the content owning the direct link.
            direct_link_id: ID of the direct link to delete.
        
        Returns:
            dict: API response confirming deletion.
        
        Example:
            >>> result = gofile.delete_direct_link("abc123", "link_id")
        """

    def copy_contents(
        self,
        contents_id: str,
        folder_id: str,
    ) -> dict:
        """
        Copy content to another folder.
        
        Args:
            contents_id: ID of the content to copy.
            folder_id: ID of the destination folder.
        
        Returns:
            dict: API response containing the copy operation result.
        
        Example:
            >>> result = gofile.copy_contents("abc123", "dest_folder_id")
        """

    def move_contents(
        self,
        contents_id: str,
        folder_id: str,
    ) -> dict:
        """
        Move content to another folder.
        
        Args:
            contents_id: ID of the content to move.
            folder_id: ID of the destination folder.
        
        Returns:
            dict: API response containing the move operation result.
        
        Example:
            >>> result = gofile.move_contents("abc123", "dest_folder_id")
        """

    def import_public_content(
        self,
        contents_id: str,
    ) -> dict:
        """
        Import a public content item to your account.
        
        Args:
            contents_id: ID of the public content to import.
        
        Returns:
            dict: API response containing the import operation result.
        
        Example:
            >>> result = gofile.import_public_content("public_content_id")
        """

    def get_account_id(
        self,
    ) -> dict:
        """
        Get the account ID of the authenticated user.
        
        Returns:
            dict: API response containing the account ID.
        
        Example:
            >>> result = gofile.get_account_id()
            >>> print(f"Account ID: {result['data']['id']}")
        """

    def get_account_info(
        self,
        account_id: str,
    ) -> Profile:
        """
        Get profile information for a specific account by ID.
        
        Args:
            account_id: ID of the account to retrieve.
        
        Returns:
            Profile: Profile object containing account information.
        
        Example:
            >>> profile = gofile.get_account_info("account_id")
            >>> print(f"Email: {profile.email}")
        """
        url = f"{self.base_url}/accounts/{account_id}"

        response = self.session.get(
            url,
        )
        return ProfileData(**response.json()).profile

    def reset_api_token(
        self,
        account_id: str,
    ) -> dict:
        """
        Reset the API token for an account.
        
        Args:
            account_id: ID of the account to reset the token for.
        
        Returns:
            dict: API response containing the new token information.
        
        Example:
            >>> result = gofile.reset_api_token("account_id")
        """
        url = f"{self.base_url}/accounts/{account_id}/resettoken"

        response = self.session.post(
            url,
        )
        return response.json()
