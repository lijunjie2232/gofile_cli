from pydantic import BaseModel


class ContentUploadData(BaseModel):
    createTime: int
    downloadPage: str
    id: str
    md5: str
    mimetype: str
    modTime: int
    name: str
    parentFolder: str
    parentFolderCode: str
    servers: list[str]
    size: int
    type: str


class ContentUploadInfo(BaseModel):
    """
    {
        "data": {
            "createTime": 1750601356,
            "downloadPage": "https://gofile.io/d/0cC7ih",
            "id": "698bd32e-8a11-40c9-b213-2eaf0d8a5b54",
            "md5": "abdeeac828503f63a4e0814f62129074",
            "mimetype": "application/zip",
            "modTime": 1750601356,
            "name": "model.pt",
            "parentFolder": "df591aef-5523-4c21-90d0-f343a27fb5a0",
            "parentFolderCode": "0cC7ih",
            "servers": ["store-na-phx-1"],
            "size": 11236350,
            "type": "file",
        },
        "status": "ok",
    }
    """

    status: str
    data: ContentUploadData
