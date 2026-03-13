import { useState } from "react";
import { Form, Input, Button, message } from "antd";
import { UserOutlined, LockOutlined, SafetyOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { login as loginApi } from "../api";

const demoUsers = [
  { username: "admin", password: "admin123", role: "Admin", color: "#FF4D4F" },
  { username: "user", password: "user123", role: "Xodim", color: "#52C41A" },
];

export default function Login() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();
  const [form] = Form.useForm();

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const { data } = await loginApi(values.username, values.password);
      login(data.access_token, data.user);
      message.success(`Xush kelibsiz, ${data.user.full_name}!`);
      navigate("/");
    } catch {
      message.error("Login yoki parol noto'g'ri");
    } finally {
      setLoading(false);
    }
  };

  const fillDemo = (username: string, password: string) => {
    form.setFieldsValue({ username, password });
  };

  return (
    <div className="login-page">
      <div className="login-bg-grid" />
      <div className="login-orb login-orb-1" />
      <div className="login-orb login-orb-2" />
      <div className="login-orb login-orb-3" />

      <div className="login-card">
        <div className="login-card-header">
          <div className="login-card-icon">
            <SafetyOutlined />
          </div>
          <h2>Bank Assets</h2>
          <p>Aktivlarni boshqarish tizimi</p>
        </div>

        <Form form={form} onFinish={onFinish} autoComplete="off" className="login-form">
          <Form.Item name="username" rules={[{ required: true, message: "Login kiriting" }]}>
            <Input prefix={<UserOutlined />} placeholder="Login" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: "Parol kiriting" }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="Parol" />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0 }}>
            <Button type="primary" htmlType="submit" loading={loading} block>
              Tizimga kirish
            </Button>
          </Form.Item>
        </Form>

        <div className="demo-divider">
          <span>Tezkor kirish</span>
        </div>

        <div className="demo-buttons">
          {demoUsers.map((u) => (
            <button
              key={u.username}
              className="demo-btn"
              onClick={() => fillDemo(u.username, u.password)}
              type="button"
            >
              <span className="demo-btn-dot" style={{ background: u.color }} />
              <span className="demo-btn-name">{u.username}</span>
              <span className="demo-btn-role">{u.role}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
