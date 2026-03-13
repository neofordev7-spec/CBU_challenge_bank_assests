import { useEffect, useState } from "react";
import {
  Form, Input, Select, DatePicker, InputNumber, Button, Card,
  Typography, Upload, message, Row, Col, Switch, Progress,
} from "antd";
import {
  ArrowLeftOutlined, UploadOutlined, SaveOutlined, PlusOutlined,
  RobotOutlined, ThunderboltOutlined, CheckCircleOutlined,
} from "@ant-design/icons";
import { useNavigate, useParams } from "react-router-dom";
import { createAsset, updateAsset, getAsset, getCategories, uploadPhoto, aiSuggestCategory, aiAutoFill } from "../api";
import type { Category } from "../types";
import dayjs from "dayjs";

export default function AssetForm() {
  const { id } = useParams<{ id: string }>();
  const isEdit = !!id;
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState<Category[]>([]);
  const [photoPath, setPhotoPath] = useState<string | null>(null);

  // AI states
  const [aiEnabled, setAiEnabled] = useState(true);
  const [aiSuggestion, setAiSuggestion] = useState<{
    category_id: number; category_name: string; confidence: number; reason: string;
  } | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [autoFillLoading, setAutoFillLoading] = useState(false);
  const [autoFillResult, setAutoFillResult] = useState<{
    category_id: number | null; category_name: string | null;
    description: string | null; estimated_price_uzs: number | null;
    confidence: number; reason: string;
  } | null>(null);

  useEffect(() => {
    getCategories().then((r) => setCategories(r.data));
    if (isEdit) {
      getAsset(+id).then((r) => {
        const a = r.data;
        form.setFieldsValue({
          ...a,
          purchase_date: a.purchase_date ? dayjs(a.purchase_date) : null,
          warranty_expiry: a.warranty_expiry ? dayjs(a.warranty_expiry) : null,
        });
        setPhotoPath(a.photo_path);
      });
    }
  }, [id]);

  const onFinish = async (values: any) => {
    setLoading(true);
    try {
      const data = {
        ...values,
        purchase_date: values.purchase_date?.format("YYYY-MM-DD"),
        warranty_expiry: values.warranty_expiry?.format("YYYY-MM-DD"),
        photo_path: photoPath,
      };
      if (isEdit) {
        await updateAsset(+id, data);
        message.success("Aktiv yangilandi");
      } else {
        await createAsset(data);
        message.success("Aktiv yaratildi");
      }
      navigate("/assets");
    } catch (e: any) {
      message.error(e.response?.data?.detail || "Xatolik yuz berdi");
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (file: File) => {
    try {
      const { data } = await uploadPhoto(file);
      setPhotoPath(data.path);
      message.success("Rasm yuklandi");
    } catch {
      message.error("Rasm yuklashda xatolik");
    }
    return false;
  };

  const handleAiSuggest = async () => {
    const name = form.getFieldValue("name");
    const description = form.getFieldValue("description");
    if (!name?.trim()) {
      message.warning("Avval aktiv nomini kiriting");
      return;
    }
    setAiLoading(true);
    try {
      const { data } = await aiSuggestCategory(name, description);
      setAiSuggestion(data);
      if (data.category_id) {
        form.setFieldValue("category_id", data.category_id);
        message.success(`AI tavsiyasi: ${data.category_name} (${data.confidence}%)`);
      }
    } catch {
      message.info("AI xizmati hozircha mavjud emas");
    } finally {
      setAiLoading(false);
    }
  };

  const handleAutoFill = async () => {
    const name = form.getFieldValue("name");
    if (!name?.trim()) {
      message.warning("Avval aktiv nomini kiriting");
      return;
    }
    setAutoFillLoading(true);
    setAutoFillResult(null);
    try {
      const { data } = await aiAutoFill(name);
      setAutoFillResult(data);

      // Maydonlarni to'ldirish
      if (data.category_id) {
        form.setFieldValue("category_id", data.category_id);
      }
      if (data.description) {
        form.setFieldValue("description", data.description);
      }
      if (data.estimated_price_uzs) {
        form.setFieldValue("purchase_price", data.estimated_price_uzs);
      }

      message.success(`AI ${data.confidence}% ishonch bilan maydonlarni to'ldirdi`);
    } catch {
      message.info("AI xizmati hozircha mavjud emas");
    } finally {
      setAutoFillLoading(false);
    }
  };

  return (
    <div className="animate-in">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/assets")} />
          <Typography.Title level={4} style={{ margin: 0 }}>
            {isEdit ? "Aktivni tahrirlash" : "Yangi aktiv"}
          </Typography.Title>
        </div>
        {!isEdit && (
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <RobotOutlined style={{ color: aiEnabled ? "#722ED1" : "#D9D9D9", fontSize: 16 }} />
            <Typography.Text style={{ fontSize: 13, color: aiEnabled ? "#531DAB" : "#8C8C8C" }}>
              AI yordamchi
            </Typography.Text>
            <Switch
              size="small"
              checked={aiEnabled}
              onChange={setAiEnabled}
              style={{ background: aiEnabled ? "#722ED1" : undefined }}
            />
          </div>
        )}
      </div>

      {/* AI Auto-fill panel */}
      {!isEdit && aiEnabled && (
        <Card
          size="small"
          style={{
            marginBottom: 16,
            borderRadius: 12,
            background: "linear-gradient(135deg, #F9F0FF 0%, #EDE7F6 100%)",
            border: "1px solid #D3ADF7",
          }}
          styles={{ body: { padding: "14px 18px" } }}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{
                width: 36, height: 36, borderRadius: 10,
                background: "linear-gradient(135deg, #722ED1, #531DAB)",
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                <ThunderboltOutlined style={{ color: "#fff", fontSize: 18 }} />
              </div>
              <div>
                <div style={{ fontWeight: 600, fontSize: 13, color: "#531DAB" }}>
                  AI avtomatik to'ldirish
                </div>
                <div style={{ fontSize: 11, color: "#8C8C8C" }}>
                  Aktiv nomini kiriting — AI qolgan maydonlarni to'ldiradi
                </div>
              </div>
            </div>
            <Button
              type="primary"
              icon={autoFillLoading ? undefined : <RobotOutlined />}
              loading={autoFillLoading}
              onClick={handleAutoFill}
              style={{
                background: "linear-gradient(135deg, #722ED1, #531DAB)",
                borderColor: "#722ED1",
                borderRadius: 8,
              }}
            >
              AI bilan to'ldirish
            </Button>
          </div>

          {/* Auto-fill result */}
          {autoFillResult && (
            <div style={{
              marginTop: 12, padding: "10px 14px", borderRadius: 8,
              background: "rgba(255,255,255,0.8)", border: "1px solid #D3ADF7",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                <CheckCircleOutlined style={{ color: "#52C41A" }} />
                <Typography.Text strong style={{ fontSize: 12, color: "#531DAB" }}>
                  {autoFillResult.confidence}% ishonch bilan to'ldirildi
                </Typography.Text>
                <Progress
                  percent={autoFillResult.confidence}
                  size="small"
                  style={{ width: 80, margin: 0 }}
                  strokeColor="#722ED1"
                  showInfo={false}
                />
              </div>
              <div style={{ fontSize: 11, color: "#595959" }}>
                {autoFillResult.reason}
              </div>
            </div>
          )}
        </Card>
      )}

      <Card className="form-card">
        <Form form={form} layout="vertical" onFinish={onFinish}>
          <Row gutter={24}>
            <Col xs={24} md={12}>
              <Form.Item name="name" label="Nomi" rules={[{ required: true, message: "Nom kiriting" }]}>
                <Input placeholder="Masalan: Dell Latitude 5540" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="serial_number" label="Seriya raqami" rules={[{ required: true, message: "Seriya raqami kiriting" }]}>
                <Input placeholder="Masalan: DELL-LAT-12345" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={24}>
            <Col xs={24} md={12}>
              <Form.Item label="Kategoriya" required>
                <div style={{ display: "flex", gap: 8 }}>
                  <Form.Item name="category_id" noStyle rules={[{ required: true, message: "Kategoriya tanlang" }]}>
                    <Select
                      placeholder="Kategoriya tanlang"
                      showSearch
                      optionFilterProp="label"
                      style={{ flex: 1 }}
                      options={categories.map((c) => ({ value: c.id, label: `${c.name} (${c.code})` }))}
                    />
                  </Form.Item>
                  {!isEdit && aiEnabled && (
                    <Button
                      icon={<RobotOutlined />}
                      loading={aiLoading}
                      onClick={handleAiSuggest}
                      title="AI orqali kategoriyani aniqlash"
                      style={{ borderColor: "#722ED1", color: "#722ED1" }}
                    >
                      AI
                    </Button>
                  )}
                </div>
                {aiSuggestion && aiSuggestion.category_id && (
                  <div style={{
                    marginTop: 6, padding: "6px 10px", borderRadius: 6,
                    background: "#F9F0FF", border: "1px solid #D3ADF7", fontSize: 12,
                  }}>
                    <RobotOutlined style={{ color: "#722ED1", marginRight: 6 }} />
                    <strong>{aiSuggestion.category_name}</strong> ({aiSuggestion.confidence}%)
                    <span style={{ color: "#8C8C8C", marginLeft: 8 }}>{aiSuggestion.reason}</span>
                  </div>
                )}
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="purchase_price" label="Narxi (so'm)">
                <InputNumber
                  style={{ width: "100%" }}
                  min={0}
                  step={1000}
                  formatter={(v) => `${v}`.replace(/\B(?=(\d{3})+(?!\d))/g, ",")}
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="description" label="Tavsif">
            <Input.TextArea rows={3} placeholder="Qo'shimcha ma'lumot..." />
          </Form.Item>

          <Row gutter={24}>
            <Col xs={24} md={12}>
              <Form.Item name="purchase_date" label="Sotib olingan sana">
                <DatePicker style={{ width: "100%" }} />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="warranty_expiry" label="Kafolat muddati">
                <DatePicker style={{ width: "100%" }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="notes" label="Izoh">
            <Input.TextArea rows={2} />
          </Form.Item>

          <Form.Item label="Rasm">
            <Upload
              beforeUpload={handleUpload}
              maxCount={1}
              accept="image/*"
              showUploadList={false}
            >
              <Button icon={<UploadOutlined />}>Rasm yuklash</Button>
            </Upload>
            {photoPath && <Typography.Text type="success" style={{ marginLeft: 12 }}>Rasm yuklangan</Typography.Text>}
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, paddingTop: 8, borderTop: "1px solid #f0f0f0" }}>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              icon={isEdit ? <SaveOutlined /> : <PlusOutlined />}
              size="large"
            >
              {isEdit ? "Saqlash" : "Yaratish"}
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
