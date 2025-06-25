from pydantic import BaseModel


class IpInfo(BaseModel):
    """
    {
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

    _id: str
    cidr: str
    asnNumber: str
    asnName: str
    asnType: str
    country: str
    netblockId: str
    netblockName: str
    netblockSize: str
    netblockDomain: str
