import { useEffect, useState } from "react";
import { Table, Button, Modal, Form, Input, Select, Typography, message, Tooltip } from "antd";
import { PlusOutlined, EditOutlined, DeleteOutlined } from "@ant-design/icons";
import { getEmployees, getDepartments, createEmployee, updateEmployee, deleteEmployee } from "../api";
import type { Employee, Department } from "../types";

export default function Employees() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(false);
  const [modal, setModal] = useState(false);
  const [editing, setEditing] = useState<Employee | null>(null);
  const [form] = Form.useForm();

  const fetch = async () => {
    setLoading(true);
    try {
      const [e, d] = await Promise.all([getEmployees(), getDepartments()]);
      setEmployees(e.data);
      setDepartments(d.data);
    } finally { setLoading(false); }
  };

  useEffect(() => { fetch(); }, []);

  const handleSubmit = async (values: any) => {
    try {
      if (editing) {
        await updateEmployee(editing.id, values);
        message.success("Xodim yangilandi");
      } else {
        await createEmployee(values);
        message.success("Xodim qo'shildi");
      }
      setModal(false);
      form.resetFields();
      setEditing(null);
      fetch();
    } catch (e: any) {
      message.error(e.response?.data?.detail || "Xatolik");
    }
  };

  const handleEdit = (emp: Employee) => {
    setEditing(emp);
    form.setFieldsValue(emp);
    setModal(true);
  };

  const handleDelete = async (id: number) => {
    await deleteEmployee(id);
    message.success("O'chirildi");
    fetch();
  };

  return (
    <div className="animate-in">
      <div className="page-header">
        <Typography.Title level={4}>Xodimlar</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditing(null); form.resetFields(); setModal(true); }}>
          Yangi xodim
        </Button>
      </div>

      <Table
        dataSource={employees}
        rowKey="id"
        loading={loading}
        size="middle"
        columns={[
          { title: "Kod", dataIndex: "employee_code", width: 100 },
          { title: "F.I.O", dataIndex: "full_name" },
          { title: "Lavozim", dataIndex: "position" },
          { title: "Bo'lim", dataIndex: ["department", "name"], width: 160 },
          { title: "Telefon", dataIndex: "phone", width: 140 },
          {
            title: "", width: 90,
            render: (_: unknown, r: Employee) => (
              <div style={{ display: "flex", gap: 4 }}>
                <Tooltip title="Tahrirlash">
                  <Button type="text" size="small" icon={<EditOutlined />} onClick={() => handleEdit(r)} />
                </Tooltip>
                <Tooltip title="O'chirish">
                  <Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(r.id)} />
                </Tooltip>
              </div>
            ),
          },
        ]}
      />

      <Modal
        title={editing ? "Xodimni tahrirlash" : "Yangi xodim"}
        open={modal}
        onOk={() => form.submit()}
        onCancel={() => { setModal(false); setEditing(null); }}
        okText="Saqlash"
        cancelText="Bekor qilish"
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="full_name" label="F.I.O" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="employee_code" label="Xodim kodi" rules={[{ required: true }]}>
            <Input placeholder="EMP-001" />
          </Form.Item>
          <Form.Item name="position" label="Lavozim">
            <Input />
          </Form.Item>
          <Form.Item name="department_id" label="Bo'lim" rules={[{ required: true }]}>
            <Select
              showSearch
              optionFilterProp="label"
              options={departments.map((d) => ({ value: d.id, label: `${d.name} (${d.code})` }))}
            />
          </Form.Item>
          <Form.Item name="phone" label="Telefon">
            <Input />
          </Form.Item>
          <Form.Item name="email" label="Email">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
