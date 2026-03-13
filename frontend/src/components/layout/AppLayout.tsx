import { useState } from "react";
import { Layout, Menu, Button, Avatar, Dropdown, Tag } from "antd";
import {
  DashboardOutlined, LaptopOutlined, ScanOutlined,
  DatabaseOutlined, AuditOutlined, LogoutOutlined,
  MenuFoldOutlined, MenuUnfoldOutlined,
  SafetyOutlined, RobotOutlined,
} from "@ant-design/icons";
import { useNavigate, useLocation, Outlet } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import AIChatbot from "../ai/AIChatbot";

const { Header, Sider, Content } = Layout;

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();

  const isUser = user?.role === "user";

  const adminMenuItems = [
    { key: "/", icon: <DashboardOutlined />, label: "Dashboard" },
    { key: "/assets", icon: <LaptopOutlined />, label: "Aktivlar" },
    { key: "/scan", icon: <ScanOutlined />, label: "QR Skan" },
    { type: "divider" as const },
    { key: "/directory", icon: <DatabaseOutlined />, label: "Ma'lumotlar" },
    { key: "/ai-analytics", icon: <RobotOutlined />, label: "AI Tahlil" },
    { key: "/audit-log", icon: <AuditOutlined />, label: "Audit Log" },
  ];

  const userMenuItems = [
    { key: "/", icon: <LaptopOutlined />, label: "Mening aktivlarim" },
    { key: "/scan", icon: <ScanOutlined />, label: "QR Skan" },
  ];

  const menuItems = isUser ? userMenuItems : adminMenuItems;

  const roleLabels: Record<string, string> = {
    admin: "ADMIN",
    user: "XODIM",
  };

  const roleColors: Record<string, string> = {
    admin: "#f5222d",
    user: "#52c41a",
  };

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        width={260}
        className="app-sidebar"
        breakpoint="lg"
        onBreakpoint={(broken) => setCollapsed(broken)}
      >
        <div className="sidebar-logo">
          <div className="logo-box">
            <SafetyOutlined />
          </div>
          {!collapsed && <span className="logo-text">Bank Assets</span>}
        </div>
        <Menu
          mode="inline"
          theme="dark"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header className="app-header">
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ fontSize: 16 }}
          />
          <Dropdown
            menu={{
              items: [
                {
                  key: "info",
                  label: (
                    <div style={{ padding: "6px 0" }}>
                      <div style={{ fontWeight: 600, fontSize: 14, color: "#141414" }}>{user?.full_name}</div>
                      <div style={{ fontSize: 12, color: "#8c8c8c", marginTop: 2 }}>{user?.email || user?.username}</div>
                    </div>
                  ),
                  disabled: true,
                },
                { type: "divider" },
                { key: "logout", icon: <LogoutOutlined />, label: "Tizimdan chiqish", danger: true, onClick: logout },
              ],
            }}
            placement="bottomRight"
          >
            <div className="header-user-btn">
              <Avatar
                size={38}
                style={{
                  background: "linear-gradient(135deg, #0958D9, #1677FF)",
                  fontWeight: 600,
                  fontSize: 15,
                }}
              >
                {user?.full_name?.charAt(0)?.toUpperCase()}
              </Avatar>
              <div style={{ lineHeight: 1.3 }}>
                <div style={{ fontWeight: 600, fontSize: 13, color: "#141414", letterSpacing: "-0.01em" }}>
                  {user?.full_name}
                </div>
                <Tag
                  color={roleColors[user?.role || ""] || "default"}
                  style={{ fontSize: 10, lineHeight: "16px", margin: 0, padding: "0 7px", borderRadius: 4, fontWeight: 600, letterSpacing: "0.04em" }}
                >
                  {roleLabels[user?.role || ""] || user?.role?.toUpperCase()}
                </Tag>
              </div>
            </div>
          </Dropdown>
        </Header>
        <Content className="content-area">
          <Outlet />
        </Content>
      </Layout>
      <AIChatbot />
    </Layout>
  );
}
