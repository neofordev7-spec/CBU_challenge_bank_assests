from enum import Enum


class AssetStatus(str, Enum):
    REGISTERED = "REGISTERED"
    ASSIGNED = "ASSIGNED"
    IN_REPAIR = "IN_REPAIR"
    LOST = "LOST"
    WRITTEN_OFF = "WRITTEN_OFF"


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    AssetStatus.REGISTERED: [AssetStatus.ASSIGNED, AssetStatus.WRITTEN_OFF],
    AssetStatus.ASSIGNED: [AssetStatus.REGISTERED, AssetStatus.IN_REPAIR, AssetStatus.LOST],
    AssetStatus.IN_REPAIR: [AssetStatus.REGISTERED, AssetStatus.ASSIGNED, AssetStatus.WRITTEN_OFF],
    AssetStatus.LOST: [AssetStatus.WRITTEN_OFF],
    AssetStatus.WRITTEN_OFF: [],
}


STATUS_LABELS = {
    AssetStatus.REGISTERED: "Ro'yxatga olingan",
    AssetStatus.ASSIGNED: "Biriktirilgan",
    AssetStatus.IN_REPAIR: "Ta'mirda",
    AssetStatus.LOST: "Yo'qolgan",
    AssetStatus.WRITTEN_OFF: "Hisobdan chiqarilgan",
}
