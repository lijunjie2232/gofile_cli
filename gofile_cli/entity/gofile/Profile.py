from pydantic import BaseModel, Field
from .StatsCurrent import StatsCurrent
from .IpInfo import IpInfo


class Profile(BaseModel):
    """
    "ipTraffic": {
        "2024": {},
        "2025": {
            "5": {
                "29": 403135
            },
            "6": {
                "3": 19458211234,
                "5": 213911552,
                "21": 223054336
            }
        }
    },
    "id": "8ff4cc08-5653-4d0f-af33-4842b2a1197c",
    "createTime": 1750575722,
    "email": "0wil78aj@punkproof.com",
    "tier": "standard",
    "token": "ztbqoBKbq4JLBUK1G85w2s5HThy2n6CY",
    "rootFolder": "dd1fc21c-15bd-41c0-b4a5-9c73d1dab065",
    "statsCurrent": {
        "folderCount": 1,
        "fileCount": 0,
        "storage": 0
    },
    "ipinfo": {
        "_id": "110.233.0.0/16",
        "cidr": "110.233.0.0/16",
        "asnNumber": "AS2518",
        "asnName": "BIGLOBE Inc.",
        "asnType": "isp",
        "country": "JP",
        "netblockId": "BIGLOBE",
        "netblockName": "BIGLOBE Inc.",
        "netblockSize": "65536",
        "netblockDomain": "biglobe.co.jp"
    }
    """

    ipTraffic: dict | int
    id: str
    createTime: int
    email: str
    tier: str
    token: str
    rootFolder: str
    statsCurrent: StatsCurrent
    ipinfo: IpInfo


class ProfileData(BaseModel):
    """
    {
        "status": "ok",
        "data": {
            Profile()
        }
    }
    """

    status: str
    profile: Profile = Field(alias="data")
