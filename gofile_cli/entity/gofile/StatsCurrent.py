from pydantic import BaseModel


class StatsCurrent(BaseModel):
    """
    {
        "folderCount": 1,
        "fileCount": 0,
        "storage": 0
    }
    """

    folderCount: int
    fileCount: int
    storage: int
