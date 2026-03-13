export interface User {
  id: number;
  username: string;
  full_name: string;
  email: string | null;
  role: string;
  is_active: boolean;
  employee_id: number | null;
  created_at: string;
}

export interface Branch {
  id: number;
  name: string;
  code: string;
  address: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Department {
  id: number;
  name: string;
  code: string;
  branch_id: number;
  is_active: boolean;
  created_at: string;
  branch?: Branch;
}

export interface Employee {
  id: number;
  full_name: string;
  employee_code: string;
  position: string | null;
  department_id: number;
  phone: string | null;
  email: string | null;
  is_active: boolean;
  created_at: string;
  department?: Department;
}

export interface Category {
  id: number;
  name: string;
  code: string;
  description: string | null;
  useful_life_months: number | null;
  is_active: boolean;
}

export interface Asset {
  id: number;
  name: string;
  serial_number: string;
  inventory_number: string;
  category_id: number;
  status: string;
  description: string | null;
  purchase_date: string | null;
  purchase_price: number | null;
  warranty_expiry: string | null;
  photo_path: string | null;
  qr_code_path: string | null;
  current_employee_id: number | null;
  current_department_id: number | null;
  current_branch_id: number | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  category?: Category;
  current_employee?: Employee;
  current_department?: Department;
  current_branch?: Branch;
  current_value?: number | null;
}

export interface AssetListResponse {
  items: Asset[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface Assignment {
  id: number;
  asset_id: number;
  employee_id: number;
  department_id: number;
  branch_id: number;
  assigned_at: string;
  returned_at: string | null;
  return_reason: string | null;
  notes: string | null;
  employee?: Employee;
  department?: Department;
  branch?: Branch;
}

export interface AuditLog {
  id: number;
  asset_id: number | null;
  action: string;
  entity_type: string;
  entity_id: number;
  old_value: string | null;
  new_value: string | null;
  description: string;
  performed_by: number | null;
  performed_at: string;
  user?: User;
}

export interface OverviewStats {
  total_assets: number;
  registered: number;
  assigned: number;
  in_repair: number;
  lost: number;
  written_off: number;
  total_value: string;
  expiring_warranty_count: number;
}

export interface CategoryStat {
  category_id: number;
  category_name: string;
  count: number;
}

export interface StatusStat {
  status: string;
  count: number;
}

export interface DepartmentStat {
  department_id: number;
  department_name: string;
  count: number;
}

export interface BranchStat {
  branch_id: number;
  branch_name: string;
  count: number;
}

export interface AgingAsset {
  id: number;
  name: string;
  inventory_number: string;
  category_name: string;
  purchase_date: string | null;
  warranty_expiry: string | null;
  age_months: number | null;
  useful_life_months: number | null;
  status: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}
