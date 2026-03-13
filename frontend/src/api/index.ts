import api from "./client";
import type {
  Asset, AssetListResponse, Assignment, AuditLog,
  Branch, Category, Department, Employee, User,
  LoginResponse, OverviewStats, CategoryStat,
  StatusStat, DepartmentStat, BranchStat, AgingAsset,
} from "../types";

// Auth
export const login = (username: string, password: string) =>
  api.post<LoginResponse>("/api/auth/login", { username, password });

export const getMe = () => api.get<LoginResponse["user"]>("/api/auth/me");
export const getMyAssets = () => api.get<{ current_assets: Asset[]; history: any[] }>("/api/auth/my-assets");

// Branches
export const getBranches = () => api.get<Branch[]>("/api/branches/");
export const createBranch = (data: Partial<Branch>) => api.post<Branch>("/api/branches/", data);
export const updateBranch = (id: number, data: Partial<Branch>) => api.put<Branch>(`/api/branches/${id}`, data);
export const deleteBranch = (id: number) => api.delete(`/api/branches/${id}`);

// Departments
export const getDepartments = (branchId?: number) =>
  api.get<Department[]>("/api/departments/", { params: { branch_id: branchId } });
export const createDepartment = (data: Partial<Department>) => api.post<Department>("/api/departments/", data);
export const updateDepartment = (id: number, data: Partial<Department>) => api.put<Department>(`/api/departments/${id}`, data);
export const deleteDepartment = (id: number) => api.delete(`/api/departments/${id}`);

// Employees
export const getEmployees = (departmentId?: number, search?: string) =>
  api.get<Employee[]>("/api/employees/", { params: { department_id: departmentId, search } });
export const createEmployee = (data: Partial<Employee>) => api.post<Employee>("/api/employees/", data);
export const updateEmployee = (id: number, data: Partial<Employee>) => api.put<Employee>(`/api/employees/${id}`, data);
export const deleteEmployee = (id: number) => api.delete(`/api/employees/${id}`);

// Categories
export const getCategories = () => api.get<Category[]>("/api/categories/");
export const createCategory = (data: Partial<Category>) => api.post<Category>("/api/categories/", data);
export const updateCategory = (id: number, data: Partial<Category>) => api.put<Category>(`/api/categories/${id}`, data);

// Assets
export const getAssets = (params: Record<string, unknown>) =>
  api.get<AssetListResponse>("/api/assets/", { params });
export const getAsset = (id: number) => api.get<Asset>(`/api/assets/${id}`);
export const createAsset = (data: Partial<Asset>) => api.post<Asset>("/api/assets/", data);
export const updateAsset = (id: number, data: Partial<Asset>) => api.put<Asset>(`/api/assets/${id}`, data);
export const deleteAsset = (id: number) => api.delete(`/api/assets/${id}`);
export const changeAssetStatus = (id: number, status: string, reason?: string) =>
  api.patch<Asset>(`/api/assets/${id}/status`, { status, reason });

// Assignments
export const assignAsset = (data: { asset_id: number; employee_id?: number; department_id?: number; branch_id?: number; notes?: string }) =>
  api.post<Assignment>("/api/assignments/", data);
export const returnAsset = (assignmentId: number, return_reason?: string) =>
  api.post<Assignment>(`/api/assignments/${assignmentId}/return`, { return_reason });
export const getAssetAssignments = (assetId: number) =>
  api.get<Assignment[]>(`/api/assignments/asset/${assetId}`);

// QR Code
export const getAssetQRCode = (assetId: number) => `${api.defaults.baseURL}/api/assets/${assetId}/qrcode`;
export const qrLookup = (inventoryNumber: string) =>
  api.get<Asset>(`/api/qr/lookup/${inventoryNumber}`);

// Audit Logs
export const getAuditLogs = (params: Record<string, unknown>) =>
  api.get<{ items: AuditLog[]; total: number }>("/api/audit-logs/", { params });
export const getAssetAuditLogs = (assetId: number) =>
  api.get<AuditLog[]>(`/api/audit-logs/asset/${assetId}`);

// Statistics
export const getOverview = () => api.get<OverviewStats>("/api/statistics/overview");
export const getByCategory = () => api.get<CategoryStat[]>("/api/statistics/by-category");
export const getByStatus = () => api.get<StatusStat[]>("/api/statistics/by-status");
export const getByDepartment = () => api.get<DepartmentStat[]>("/api/statistics/by-department");
export const getByBranch = () => api.get<BranchStat[]>("/api/statistics/by-branch");
export const getAgingAssets = () => api.get<AgingAsset[]>("/api/statistics/aging");

// Users
export const getUsers = () => api.get<User[]>("/api/auth/users");

// AI
export const aiSuggestCategory = (name: string, description?: string) =>
  api.post<{ category_id: number; category_name: string; confidence: number; reason: string }>(
    "/api/ai/suggest-category", { name, description }
  );
export const aiRiskAssessment = () =>
  api.get<{ analysis: string; assets: { id: number; name: string; risk_score: number; risk_level: string; recommendation: string }[] }>(
    "/api/ai/risk-assessment"
  );
export const aiInsights = () =>
  api.get<{ insights: { type: string; title: string; description: string; priority: string }[] }>(
    "/api/ai/insights"
  );
export const aiProblematicAssets = () =>
  api.get<{ problematic_assets: { id: number; name: string; inventory_number: string; problem_type: string; severity: string; reason: string; recommendation: string }[]; summary: string }>(
    "/api/ai/problematic-assets"
  );

export const aiChat = (message: string) =>
  api.post<{ answer: string; suggestions: string[]; _attempts?: any[] }>(
    "/api/ai/chat", { message }
  );

export const aiAutoFill = (name: string) =>
  api.post<{
    category_id: number | null; category_name: string | null;
    description: string | null; estimated_price_uzs: number | null;
    useful_life_months: number | null; confidence: number; reason: string;
    _attempts?: any[];
  }>("/api/ai/auto-fill", { name });

// Upload
export const uploadPhoto = (file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  return api.post<{ filename: string; path: string }>("/api/upload/photo", formData);
};
