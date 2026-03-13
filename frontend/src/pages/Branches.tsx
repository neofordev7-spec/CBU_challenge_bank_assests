import { useEffect, useState } from "react";
import { Table, Button, Modal, Form, Input, Typography, message, Tooltip } from "antd";
import { PlusOutlined, EditOutlined, DeleteOutlined } from "@ant-design/icons";
import { getBranches, createBranch, updateBranch, deleteBranch } from "../api";
import type { Branch } from "../types";

export default function Branches() {
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loading, setLoading] = useState(false);
  const [modal, setModal] = useState(false);
  const [editing, setEditing] = useState<Branch | null>(null);
  const [form] = Form.useForm();

  const fetch = async () => {
    setLoading(true);
    try {
      const { data } = await getBranches();
      setBranches(data);
    } finally { setLoading(false); }
  };

  useEffect(() => { fetch(); }, []);

  const handleSubmit = async (values: any) => {
    try {
      if (editing) {
        await updateBranch(editing.id, values);
        message.success("Filial yangilandi");
      } else {
        await createBranch(values);
        message.success("Filial qo'shildi");
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
        <Typography.Title level={4}>Filiallar</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditing(null); form.resetFields(); setModal(true); }}>
          Yangi filial
        </Button>
      </div>

      <Table
        dataSource={branches}
        rowKey="id"
        loading={loading}
        size="middle"
        columns={[
          { title: "Kod", dataIndex: "code", width: 100 },
          { title: "Nomi", dataIndex: "name" },
          { title: "Manzil", dataIndex: "address", ellipsis: true },
          {
            title: "", width: 90,
            render: (_: unknown, r: Branch) => (
              <div style={{ display: "flex", gap: 4 }}>
                <Tooltip title="Tahrirlash">
                  <Button type="text" size="small" icon={<EditOutlined />} onClick={() => { setEditing(r); form.setFieldsValue(r); setModal(true); }} />
                </Tooltip>
                <Tooltip title="O'chirish">
                  <Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={async () => { await deleteBranch(r.id); message.success("O'chirildi"); fetch(); }} />
                </Tooltip>
              </div>
            ),
          },
        ]}
      />

      <Modal
        title={editing ? "Filialni tahrirlash" : "Yangi filial"}
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
            <Input placeholder="BR-01" />
          </Form.Item>
          <Form.Item name="address" label="Manzil">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
