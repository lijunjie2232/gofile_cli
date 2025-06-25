from pydantic import BaseModel


class ContentCreateData(BaseModel):
    id: str
    owner: str
    type: str
    name: str
    parentFolder: str
    createTime: int
    modTime: int
    code: str


class ContentCreateInfo(BaseModel):
    """
    {
        "status": "ok",
        "data": {
            "id": "c06f966d-ab6c-4f09-8ace-90cc1180a993",
            "owner": "bb04cc81-ec76-4051-9617-0eab6eba4270",
            "type": "folder",
            "name": "test",
            "parentFolder": "df591aef-5523-4c21-90d0-f343a27fb5a0",
            "createTime": 1750599414,
            "modTime": 1750599414,
            "code": "aM4kIU",
        },
    }
    """

    status: str
    data: ContentCreateData
