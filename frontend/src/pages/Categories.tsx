import { useEffect, useState } from "react";
import { Table, Button, Modal, Form, Input, InputNumber, Typography, message, Tooltip } from "antd";
import { PlusOutlined, EditOutlined } from "@ant-design/icons";
import { getCategories, createCategory, updateCategory } from "../api";
import type { Category } from "../types";

export default function Categories() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(false);
  const [modal, setModal] = useState(false);
  const [editing, setEditing] = useState<Category | null>(null);
  const [form] = Form.useForm();

  const fetch = async () => {
    setLoading(true);
    try {
      const { data } = await getCategories();
      setCategories(data);
    } finally { setLoading(false); }
  };

  useEffect(() => { fetch(); }, []);

  const handleSubmit = async (values: any) => {
    try {
      if (editing) {
        await updateCategory(editing.id, values);
        message.success("Kategoriya yangilandi");
      } else {
        await createCategory(values);
        message.success("Kategoriya qo'shildi");
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
        <Typography.Title level={4}>Kategoriyalar</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditing(null); form.resetFields(); setModal(true); }}>
          Yangi kategoriya
        </Button>
      </div>

      <Table
        dataSource={categories}
        rowKey="id"
        loading={loading}
        size="middle"
        columns={[
          { title: "Kod", dataIndex: "code", width: 80 },
          { title: "Nomi", dataIndex: "name" },
          { title: "Tavsif", dataIndex: "description", ellipsis: true },
          { title: "Foydali muddat (oy)", dataIndex: "useful_life_months", width: 140 },
          {
            title: "", width: 60,
            render: (_: unknown, r: Category) => (
              <Tooltip title="Tahrirlash">
                <Button type="text" size="small" icon={<EditOutlined />} onClick={() => { setEditing(r); form.setFieldsValue(r); setModal(true); }} />
              </Tooltip>
            ),
          },
        ]}
      />

      <Modal
        title={editing ? "Kategoriyani tahrirlash" : "Yangi kategoriya"}
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
            <Input placeholder="IT" />
          </Form.Item>
          <Form.Item name="description" label="Tavsif">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="useful_life_months" label="Foydali xizmat muddati (oyda)">
            <InputNumber min={1} style={{ width: "100%" }} placeholder="60" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
