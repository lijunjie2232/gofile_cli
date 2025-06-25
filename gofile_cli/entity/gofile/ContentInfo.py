from pydantic import BaseModel
from typing import Optional


class FolderInfo(BaseModel):
    """
    {
        "canAccess": true,
        "isOwner": true,
        "id": "dd1fc21c-15bd-41c0-b4a5-9c73d1dab065",
        "type": "folder",
        "name": "root",
        "createTime": 1750575722,
        "modTime": 1750575722,
        "code": "SWBjLP",
        "isRoot": true,
        "public": false,
        "totalDownloadCount": 0,
        "totalSize": 0,
        "childrenCount": 0,
        "children": {}
    }
    """

    canAccess: bool
    isOwner: bool
    id: str
    type: str
    name: str
    createTime: int
    modTime: int
    code: str
    isRoot: bool
    public: bool
    totalDownloadCount: int
    totalSize: int
    childrenCount: int
    children: dict


class FileInfo(BaseModel):
    """
    {
        "canAccess": True,
        "isOwner": True,
        "id": "698bd32e-8a11-40c9-b213-2eaf0d8a5b54",
        "parentFolder": "df591aef-5523-4c21-90d0-f343a27fb5a0",
        "type": "file",
        "name": "model.pt",
        "createTime": 1750601356,
        "modTime": 1750601356,
        "lastAccess": 1750601356,
        "size": 11236350,
        "downloadCount": 0,
        "md5": "abdeeac828503f63a4e0814f62129074",
        "mimetype": "application/zip",
        "servers": ["store-na-phx-1"],
        "serverSelected": "store-na-phx-1",
        "link": "https://store-na-phx-1.gofile.io/download/web/698bd32e-8a11-40c9-b213-2eaf0d8a5b54/model.pt",
    }
    """

    canAccess: bool
    isOwner: bool
    id: str
    parentFolder: str
    type: str
    name: str
    createTime: int
    modTime: int
    lastAccess: int
    size: int
    downloadCount: int
    md5: str
    mimetype: str
    servers: list[str]
    serverSelected: str
    link: str


class ContentMetadata(BaseModel):
    """
    {
        "totalCount": 0,
        "totalPages": 0,
        "page": 1,
        "pageSize": 1000,
        "hasNextPage": false
    }
    """

    totalCount: Optional[int] = None
    totalPages: Optional[int] = None
    page: Optional[int] = None
    pageSize: Optional[int] = None
    hasNextPage: Optional[int] = None


class ContentInfo(BaseModel):
    """
    {
        "status": "ok",
        "data": {},
        "metadata": {}
    }
    """

    status: str
    data: dict
    metadata: ContentMetadata


class FileContentInfo(BaseModel):
    status: str
    data: FileInfo
    metadata: ContentMetadata


class FolderContentInfo(BaseModel):
    status: str
    data: FolderInfo
    metadata: ContentMetadata
