export const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  REGISTERED: { label: "Ro'yxatga olingan", color: "blue" },
  ASSIGNED: { label: "Biriktirilgan", color: "green" },
  IN_REPAIR: { label: "Ta'mirda", color: "orange" },
  LOST: { label: "Yo'qolgan", color: "red" },
  WRITTEN_OFF: { label: "Hisobdan chiqarilgan", color: "volcano" },
};

export const STATUS_COLORS: Record<string, string> = {
  REGISTERED: "#1890ff",
  ASSIGNED: "#52c41a",
  IN_REPAIR: "#fa8c16",
  LOST: "#f5222d",
  WRITTEN_OFF: "#722ed1",
};

export const ALLOWED_TRANSITIONS: Record<string, string[]> = {
  REGISTERED: ["ASSIGNED", "WRITTEN_OFF"],
  ASSIGNED: ["REGISTERED", "IN_REPAIR", "LOST"],
  IN_REPAIR: ["REGISTERED", "ASSIGNED", "WRITTEN_OFF"],
  LOST: ["WRITTEN_OFF"],
  WRITTEN_OFF: [],
};

export const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
