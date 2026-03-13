import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ConfigProvider } from "antd";
import { AuthProvider, useAuth } from "./context/AuthContext";
import AppLayout from "./components/layout/AppLayout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import AssetList from "./pages/AssetList";
import AssetDetail from "./pages/AssetDetail";
import AssetForm from "./pages/AssetCreate";
import QRScanPage from "./pages/QRScanPage";
import Directory from "./pages/Directory";
import AuditLog from "./pages/AuditLog";
import AIAnalytics from "./pages/AIAnalytics";
import MyAssets from "./pages/MyAssets";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function AppRoutes() {
  const { isAuthenticated, user } = useAuth();
  const isUser = user?.role === "user";

  return (
    <Routes>
      <Route path="/login" element={isAuthenticated ? <Navigate to="/" replace /> : <Login />} />
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        {/* USER roli — faqat o'z aktivlari va QR scan */}
        {isUser ? (
          <>
            <Route path="/" element={<MyAssets />} />
            <Route path="/my-assets" element={<MyAssets />} />
            <Route path="/assets/:id" element={<AssetDetail />} />
            <Route path="/scan" element={<QRScanPage />} />
          </>
        ) : (
          <>
            <Route path="/" element={<Dashboard />} />
            <Route path="/assets" element={<AssetList />} />
            <Route path="/assets/new" element={<AssetForm />} />
            <Route path="/assets/:id" element={<AssetDetail />} />
            <Route path="/assets/:id/edit" element={<AssetForm />} />
            <Route path="/scan" element={<QRScanPage />} />
            <Route path="/directory" element={<Directory />} />
            <Route path="/ai-analytics" element={<AIAnalytics />} />
            <Route path="/audit-log" element={<AuditLog />} />
          </>
        )}
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

const bankingTheme = {
  token: {
    colorPrimary: "#0958D9",
    colorInfo: "#0958D9",
    colorSuccess: "#52C41A",
    colorWarning: "#FAAD14",
    colorError: "#FF4D4F",
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    fontSize: 14,
    borderRadius: 10,
    borderRadiusLG: 14,
    borderRadiusSM: 6,
    colorBgLayout: "#F0F2F5",
    colorText: "#141414",
    colorTextSecondary: "#595959",
    colorTextTertiary: "#8C8C8C",
    colorBorder: "#E8E8E8",
    colorBorderSecondary: "#F0F0F0",
    controlHeight: 40,
    controlHeightLG: 48,
    boxShadow: "0 1px 3px rgba(0,0,0,0.04), 0 2px 8px rgba(0,0,0,0.04)",
    boxShadowSecondary: "0 4px 6px -2px rgba(0,0,0,0.05), 0 10px 20px -2px rgba(0,0,0,0.06)",
    motion: true,
    motionDurationFast: "0.15s",
    motionDurationMid: "0.25s",
    motionDurationSlow: "0.35s",
    motionEaseInOut: "cubic-bezier(0.4, 0, 0.2, 1)",
    motionEaseOut: "cubic-bezier(0.16, 1, 0.3, 1)",
  },
  components: {
    Layout: {
      siderBg: "#001529",
      headerBg: "#FFFFFF",
      bodyBg: "#F0F2F5",
      headerHeight: 64,
    },
    Menu: {
      darkItemBg: "transparent",
      darkItemSelectedBg: "rgba(22,119,255,0.15)",
      darkItemColor: "rgba(255,255,255,0.50)",
      darkItemHoverColor: "#FFFFFF",
      darkItemSelectedColor: "#FFFFFF",
      itemBorderRadius: 10,
      itemMarginBlock: 3,
    },
    Card: {
      borderRadiusLG: 14,
      paddingLG: 24,
    },
    Button: {
      borderRadius: 10,
      fontWeight: 500,
      controlHeight: 40,
    },
    Input: {
      borderRadius: 10,
      controlHeight: 40,
    },
    Table: {
      headerBg: "#FAFBFC",
      headerColor: "#8C8C8C",
      rowHoverBg: "#F0F7FF",
      borderColor: "#F5F5F5",
      headerBorderRadius: 10,
      cellPaddingBlock: 14,
    },
    Select: {
      borderRadius: 10,
    },
    Modal: {
      borderRadiusLG: 18,
    },
    Statistic: {
      titleFontSize: 13,
      contentFontSize: 28,
    },
    Tag: {
      borderRadiusSM: 6,
    },
    Badge: {
      fontWeight: 600,
    },
    Tabs: {
      inkBarColor: "#0958D9",
      itemActiveColor: "#0958D9",
      itemSelectedColor: "#0958D9",
    },
    Tooltip: {
      borderRadius: 8,
    },
    Popover: {
      borderRadiusLG: 14,
    },
  },
};

export default function App() {
  return (
    <ConfigProvider theme={bankingTheme}>
      <AuthProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </AuthProvider>
    </ConfigProvider>
  );
}
