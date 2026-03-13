import { useEffect, useState } from "react";
import { Table, Button, Modal, Form, Input, Select, Typography, message, Tooltip } from "antd";
import { PlusOutlined, EditOutlined, DeleteOutlined } from "@ant-design/icons";
import { getDepartments, getBranches, createDepartment, updateDepartment, deleteDepartment } from "../api";
import type { Department, Branch } from "../types";

export default function Departments() {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loading, setLoading] = useState(false);
  const [modal, setModal] = useState(false);
  const [editing, setEditing] = useState<Department | null>(null);
  const [form] = Form.useForm();

  const fetch = async () => {
    setLoading(true);
    try {
      const [d, b] = await Promise.all([getDepartments(), getBranches()]);
      setDepartments(d.data);
      setBranches(b.data);
    } finally { setLoading(false); }
  };

  useEffect(() => { fetch(); }, []);

  const handleSubmit = async (values: any) => {
    try {
      if (editing) {
        await updateDepartment(editing.id, values);
        message.success("Bo'lim yangilandi");
      } else {
        await createDepartment(values);
        message.success("Bo'lim qo'shildi");
      }
      setModal(false);
      form.resetFields();
      setEditing(null);
      fetch();
    } catch (e: any) {
      message.error(e.response?.data?.detail || "Xatolik");
    }
  };

  return (
    <div className="animate-in">
      <div className="page-header">
        <Typography.Title level={4}>Bo'limlar</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditing(null); form.resetFields(); setModal(true); }}>
          Yangi bo'lim
        </Button>
      </div>

      <Table
        dataSource={departments}
        rowKey="id"
        loading={loading}
        size="middle"
        columns={[
          { title: "Kod", dataIndex: "code", width: 120 },
          { title: "Nomi", dataIndex: "name" },
          { title: "Filial", dataIndex: ["branch", "name"], width: 180 },
          {
            title: "", width: 90,
            render: (_: unknown, r: Department) => (
              <div style={{ display: "flex", gap: 4 }}>
                <Tooltip title="Tahrirlash">
                  <Button type="text" size="small" icon={<EditOutlined />} onClick={() => { setEditing(r); form.setFieldsValue(r); setModal(true); }} />
                </Tooltip>
                <Tooltip title="O'chirish">
                  <Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={async () => { await deleteDepartment(r.id); message.success("O'chirildi"); fetch(); }} />
                </Tooltip>
              </div>
            ),
          },
        ]}
      />

      <Modal
        title={editing ? "Bo'limni tahrirlash" : "Yangi bo'lim"}
        open={modal}
        onOk={() => form.submit()}
        onCancel={() => { setModal(false); setEditing(null); }}
        okText="Saqlash"
        cancelText="Bekor qilish"
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="name" label="Nomi" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="code" label="Kod" rules={[{ required: true }]}>
            <Input placeholder="HQ-IT" />
          </Form.Item>
          <Form.Item name="branch_id" label="Filial" rules={[{ required: true }]}>
            <Select options={branches.map((b) => ({ value: b.id, label: b.name }))} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
