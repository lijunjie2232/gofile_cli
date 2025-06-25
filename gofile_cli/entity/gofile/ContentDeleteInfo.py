from pydantic import BaseModel


class ContentDeleteInfo(BaseModel):
    """
    {
        "status": "ok",
        "data": {
            "c702a736-e4f5-4d0d-96fc-f3fcf6b76c1f": {
                "status": "ok",
                "data": {},
            },
        },
    }
    """

    status: str
    data: dict
