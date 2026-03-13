import { useState } from "react";
import {
  Card, Button, Spin, Tag, Typography, Progress, Row, Col, Alert, Empty, Steps,
  Tooltip,
} from "antd";
import {
  RobotOutlined, ThunderboltOutlined, BulbOutlined,
  WarningOutlined, ExclamationCircleOutlined,
  CheckCircleOutlined, InfoCircleOutlined,
  SafetyOutlined, ArrowRightOutlined,
  LoadingOutlined, SyncOutlined, ReloadOutlined,
  ExperimentOutlined, FireOutlined,
  ClockCircleOutlined,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { aiInsights, aiRiskAssessment, aiProblematicAssets } from "../api";

type InsightItem = { type: string; title: string; description: string; priority: string };
type RiskAsset = { id: number; name: string; risk_score: number; risk_level: string; recommendation: string; predicted_failure?: string; trend?: string };
type ProblemAsset = { id: number; name: string; inventory_number: string; problem_type: string; severity: string; reason: string; recommendation: string };
type AttemptStep = { step: string; status: string };

const INSIGHT_ICONS: Record<string, React.ReactNode> = {
  warning: <WarningOutlined />,
  info: <InfoCircleOutlined />,
  success: <CheckCircleOutlined />,
  action: <ThunderboltOutlined />,
};
const INSIGHT_COLORS: Record<string, string> = {
  warning: "#FA8C16", info: "#1677FF", success: "#52C41A", action: "#722ED1",
};
const PRIORITY_COLORS: Record<string, string> = {
  high: "red", medium: "orange", low: "blue",
};
const SEVERITY_COLORS: Record<string, string> = {
  yuqori: "red", "o'rta": "orange", past: "green",
};
const RISK_COLORS: Record<string, string> = {
  past: "#52C41A", "o'rta": "#FAAD14", yuqori: "#FA8C16", kritik: "#FF4D4F",
};

// ── AI Module definitions ──
const AI_MODULES = [
  {
    key: "insights",
    icon: <BulbOutlined style={{ fontSize: 22 }} />,
    title: "Inventarizatsiya tavsiyalari",
    subtitle: "Audit va inventarizatsiya",
    description: "AI aktivlaringiz holatini tahlil qilib, inventarizatsiya va audit bo'yicha amaliy tavsiyalar beradi. Kafolat muddati, status holati va boshqa mezonlar tekshiriladi.",
    gradient: "linear-gradient(135deg, #FFF8E1 0%, #FFF3CD 100%)",
    borderColor: "#FFE082",
    iconBg: "linear-gradient(135deg, #FAAD14, #D48806)",
    accentColor: "#D48806",
  },
  {
    key: "risk",
    icon: <SafetyOutlined style={{ fontSize: 22 }} />,
    title: "Nosozlik xavfi bashorati",
    subtitle: "Risk darajasi va bashorat",
    description: "Har bir aktivning eskirish darajasi, ta'mirlash tarixi va foydalanish muddatini AI tahlil qilib, nosozlik xavfini 0-100% oralig'ida baholaydi.",
    gradient: "linear-gradient(135deg, #FFF1F0 0%, #FFCCC7 100%)",
    borderColor: "#FFA39E",
    iconBg: "linear-gradient(135deg, #FF4D4F, #CF1322)",
    accentColor: "#CF1322",
  },
  {
    key: "problems",
    icon: <ExclamationCircleOutlined style={{ fontSize: 22 }} />,
    title: "Muammoli aktivlar",
    subtitle: "Muammo va yechimlar",
    description: "AI izohlar, status o'zgarishlari va boshqa belgilar asosida muammoli aktivlarni aniqlaydi va har biri uchun aniq yechim tavsiya qiladi.",
    gradient: "linear-gradient(135deg, #FFF7E6 0%, #FFE7BA 100%)",
    borderColor: "#FFD591",
    iconBg: "linear-gradient(135deg, #FA8C16, #D46B08)",
    accentColor: "#D46B08",
  },
];

export default function AIAnalytics() {
  const navigate = useNavigate();

  // Insights
  const [insights, setInsights] = useState<InsightItem[]>([]);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [insightsLoaded, setInsightsLoaded] = useState(false);

  // Risk
  const [riskAnalysis, setRiskAnalysis] = useState("");
  const [riskAssets, setRiskAssets] = useState<RiskAsset[]>([]);
  const [riskLoading, setRiskLoading] = useState(false);
  const [riskLoaded, setRiskLoaded] = useState(false);

  // Problematic
  const [problemSummary, setProblemSummary] = useState("");
  const [problemAssets, setProblemAssets] = useState<ProblemAsset[]>([]);
  const [problemLoading, setProblemLoading] = useState(false);
  const [problemLoaded, setProblemLoaded] = useState(false);

  const [error, setError] = useState("");

  // Processing (for "load all")
  const [processStep, setProcessStep] = useState(-1);
  const [processStatus, setProcessStatus] = useState("");
  const [processAttempts, setProcessAttempts] = useState<AttemptStep[]>([]);

  const anyLoading = insightsLoading || riskLoading || problemLoading;

  const collectAttempts = (data: any, allAttempts: AttemptStep[]) => {
    if (data._attempts) allAttempts.push(...data._attempts);
  };

  // ── Individual loaders ──
  const loadInsights = async () => {
    setInsightsLoading(true);
    setError("");
    try {
      const { data } = await aiInsights();
      setInsights(data.insights || []);
      setInsightsLoaded(true);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Tavsiyalar yuklanmadi");
    } finally {
      setInsightsLoading(false);
    }
  };

  const loadRisk = async () => {
    setRiskLoading(true);
    setError("");
    try {
      const { data } = await aiRiskAssessment();
      setRiskAnalysis(data.analysis || "");
      setRiskAssets(data.assets || []);
      setRiskLoaded(true);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Risk tahlili yuklanmadi");
    } finally {
      setRiskLoading(false);
    }
  };

  const loadProblematic = async () => {
    setProblemLoading(true);
    setError("");
    try {
      const { data } = await aiProblematicAssets();
      setProblemSummary(data.summary || "");
      setProblemAssets(data.problematic_assets || []);
      setProblemLoaded(true);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Muammoli aktivlar yuklanmadi");
    } finally {
      setProblemLoading(false);
    }
  };

  // ── Load all sequentially ──
  const loadAll = async () => {
    setError("");
    setProcessStep(0);
    setProcessStatus("AI tavsiyalarni tahlil qilmoqda...");
    setProcessAttempts([]);
    const errors: string[] = [];
    const allAttempts: AttemptStep[] = [];

    setInsightsLoading(true);
    try {
      const { data } = await aiInsights();
      collectAttempts(data, allAttempts);
      setProcessAttempts([...allAttempts]);
      setInsights(data.insights || []);
      setInsightsLoaded(true);
    } catch (e: any) {
      errors.push(e.response?.data?.detail || "Tavsiyalar yuklanmadi");
    }
    setInsightsLoading(false);

    setProcessStep(1);
    setProcessStatus("Nosozlik xavfini baholash...");
    setRiskLoading(true);
    try {
      const { data } = await aiRiskAssessment();
      collectAttempts(data, allAttempts);
      setProcessAttempts([...allAttempts]);
      setRiskAnalysis(data.analysis || "");
      setRiskAssets(data.assets || []);
      setRiskLoaded(true);
    } catch (e: any) {
      errors.push(e.response?.data?.detail || "Risk tahlili yuklanmadi");
    }
    setRiskLoading(false);

    setProcessStep(2);
    setProcessStatus("Muammoli aktivlarni aniqlash...");
    setProblemLoading(true);
    try {
      const { data } = await aiProblematicAssets();
      collectAttempts(data, allAttempts);
      setProcessAttempts([...allAttempts]);
      setProblemSummary(data.summary || "");
      setProblemAssets(data.problematic_assets || []);
      setProblemLoaded(true);
    } catch (e: any) {
      errors.push(e.response?.data?.detail || "Muammoli aktivlar yuklanmadi");
    }
    setProblemLoading(false);

    if (errors.length > 0) setError([...new Set(errors)].join(". "));
    setProcessStep(3);
    setProcessStatus("");
  };

  const PROCESS_LABELS = [
    "Tavsiyalar tahlili",
    "Nosozlik xavfi tahlili",
    "Muammoli aktivlar tahlili",
  ];

  const loaders = [loadInsights, loadRisk, loadProblematic];
  const loadingStates = [insightsLoading, riskLoading, problemLoading];
  const loadedStates = [insightsLoaded, riskLoaded, problemLoaded];
  const resultCounts = [insights.length, riskAssets.length, problemAssets.length];

  const nothingLoaded = !insightsLoaded && !riskLoaded && !problemLoaded && !anyLoading;

  // ── Module card status badge ──
  const getModuleStatus = (idx: number) => {
    if (loadingStates[idx]) {
      return <Tag icon={<SyncOutlined spin />} color="processing" style={{ margin: 0, borderRadius: 6 }}>Tahlil qilinmoqda...</Tag>;
    }
    if (loadedStates[idx]) {
      return (
        <Tag icon={<CheckCircleOutlined />} color="success" style={{ margin: 0, borderRadius: 6 }}>
          {resultCounts[idx]} ta natija
        </Tag>
      );
    }
    return (
      <Tag icon={<ClockCircleOutlined />} style={{ margin: 0, borderRadius: 6, color: "#8C8C8C", borderColor: "#E8E8E8" }}>
        Boshlash kutilmoqda
      </Tag>
    );
  };

  return (
    <div className="animate-in">
      {/* ══════ PAGE HEADER ══════ */}
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        marginBottom: 24, flexWrap: "wrap", gap: 12,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{
            width: 48, height: 48, borderRadius: 14,
            background: "linear-gradient(135deg, #722ED1, #531DAB)",
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: "0 4px 16px rgba(114, 46, 209, 0.3)",
          }}>
            <ExperimentOutlined style={{ fontSize: 24, color: "#fff" }} />
          </div>
          <div>
            <Typography.Title level={4} style={{ margin: 0, color: "#141414" }}>
              AI Tahlil Markazi
            </Typography.Title>
            <Typography.Text style={{ fontSize: 13, color: "#8C8C8C" }}>
              Sun'iy intellekt yordamida aktivlaringizni chuqur tahlil qiling
            </Typography.Text>
          </div>
        </div>

        <div style={{ display: "flex", gap: 8 }}>
          {(insightsLoaded || riskLoaded || problemLoaded) && (
            <Button
              icon={<ReloadOutlined />}
              onClick={loadAll}
              loading={anyLoading}
              style={{ borderRadius: 8 }}
            >
              Barchasini yangilash
            </Button>
          )}
          <Button
            type="primary"
            icon={<ThunderboltOutlined />}
            onClick={loadAll}
            loading={anyLoading}
            style={{
              background: "linear-gradient(135deg, #722ED1, #531DAB)",
              borderColor: "#722ED1",
              borderRadius: 8,
            }}
          >
            {nothingLoaded ? "Barcha tahlillarni boshlash" : "Qayta tahlil"}
          </Button>
        </div>
      </div>

      {/* ══════ ERROR ══════ */}
      {error && (
        <Alert
          type="warning"
          message="AI xizmati xatosi"
          description={error}
          closable
          onClose={() => setError("")}
          showIcon
          style={{ marginBottom: 20, borderRadius: 10 }}
        />
      )}

      {/* ══════ MODULE CARDS ══════ */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {AI_MODULES.map((mod, idx) => (
          <Col xs={24} md={8} key={mod.key}>
            <div
              onClick={() => { if (!loadingStates[idx]) loaders[idx](); }}
              style={{
                background: loadedStates[idx] ? "#fff" : mod.gradient,
                border: `1.5px solid ${loadedStates[idx] ? "#E8E8E8" : mod.borderColor}`,
                borderRadius: 16,
                padding: "24px 20px",
                cursor: loadingStates[idx] ? "wait" : "pointer",
                transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                height: "100%",
                display: "flex",
                flexDirection: "column",
                position: "relative",
                overflow: "hidden",
              }}
              onMouseEnter={(e) => {
                if (!loadingStates[idx]) {
                  e.currentTarget.style.transform = "translateY(-4px)";
                  e.currentTarget.style.boxShadow = "0 8px 28px rgba(0,0,0,0.1)";
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "translateY(0)";
                e.currentTarget.style.boxShadow = "none";
              }}
            >
              {/* Icon + Status */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
                <div style={{
                  width: 44, height: 44, borderRadius: 12,
                  background: mod.iconBg,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  color: "#fff",
                  boxShadow: `0 4px 12px ${mod.accentColor}40`,
                }}>
                  {mod.icon}
                </div>
                {getModuleStatus(idx)}
              </div>

              {/* Title */}
              <Typography.Text strong style={{ fontSize: 16, color: "#141414", marginBottom: 4, display: "block" }}>
                {mod.title}
              </Typography.Text>
              <Typography.Text style={{ fontSize: 11, color: mod.accentColor, fontWeight: 600, marginBottom: 10, display: "block", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                {mod.subtitle}
              </Typography.Text>

              {/* Description */}
              <Typography.Paragraph style={{ fontSize: 12.5, color: "#595959", margin: 0, lineHeight: 1.6, flex: 1 }}>
                {mod.description}
              </Typography.Paragraph>

              {/* Action hint */}
              {!loadedStates[idx] && !loadingStates[idx] && (
                <div style={{
                  marginTop: 16, padding: "8px 12px", borderRadius: 8,
                  background: "rgba(255,255,255,0.6)", textAlign: "center",
                  border: `1px dashed ${mod.borderColor}`,
                }}>
                  <FireOutlined style={{ color: mod.accentColor, marginRight: 6 }} />
                  <Typography.Text style={{ fontSize: 12, color: mod.accentColor, fontWeight: 500 }}>
                    Bosib tahlilni boshlang
                  </Typography.Text>
                </div>
              )}

              {/* Loading indicator */}
              {loadingStates[idx] && (
                <div style={{ marginTop: 16, textAlign: "center" }}>
                  <Spin size="small" />
                  <Typography.Text style={{ fontSize: 11, color: "#8C8C8C", marginLeft: 8 }}>
                    AI tahlil qilmoqda...
                  </Typography.Text>
                </div>
              )}

              {/* Loaded: quick stats */}
              {loadedStates[idx] && !loadingStates[idx] && (
                <div style={{
                  marginTop: 16, padding: "8px 12px", borderRadius: 8,
                  background: "#F6FFED", border: "1px solid #B7EB8F",
                  display: "flex", alignItems: "center", justifyContent: "space-between",
                }}>
                  <span style={{ fontSize: 12, color: "#389E0D" }}>
                    <CheckCircleOutlined style={{ marginRight: 6 }} />
                    {resultCounts[idx]} ta natija topildi
                  </span>
                  <Tooltip title="Qayta tahlil qilish">
                    <ReloadOutlined
                      style={{ color: "#8C8C8C", cursor: "pointer", fontSize: 13 }}
                      onClick={(e) => { e.stopPropagation(); loaders[idx](); }}
                    />
                  </Tooltip>
                </div>
              )}
            </div>
          </Col>
        ))}
      </Row>

      {/* ══════ PROCESSING STEPS (for "load all") ══════ */}
      {processStep >= 0 && processStep < 3 && anyLoading && (
        <Card
          style={{
            marginBottom: 20, borderRadius: 14,
            background: "linear-gradient(135deg, #F9F0FF 0%, #E6F4FF 100%)",
            border: "1px solid #D3ADF7",
          }}
          styles={{ body: { padding: "20px 24px" } }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
            <SyncOutlined spin style={{ fontSize: 20, color: "#722ED1" }} />
            <Typography.Text strong style={{ fontSize: 14, color: "#531DAB" }}>
              {processStatus}
            </Typography.Text>
          </div>

          <Steps
            size="small"
            current={processStep}
            items={PROCESS_LABELS.map((label, i) => ({
              title: label,
              icon: i === processStep ? <LoadingOutlined /> :
                    i < processStep ? <CheckCircleOutlined style={{ color: "#52C41A" }} /> : undefined,
              status: (i < processStep ? "finish" : i === processStep ? "process" : "wait") as "finish" | "process" | "wait",
            }))}
            style={{ marginBottom: processAttempts.length > 0 ? 16 : 0 }}
          />

          {processAttempts.length > 0 && (
            <div style={{
              marginTop: 8, padding: "8px 12px",
              background: "rgba(255,255,255,0.7)", borderRadius: 8,
              maxHeight: 100, overflowY: "auto",
            }}>
              {processAttempts.slice(-4).map((a, i) => (
                <div key={i} style={{ fontSize: 11, color: "#595959", padding: "2px 0", display: "flex", alignItems: "center", gap: 6 }}>
                  {a.status === "success" ? (
                    <CheckCircleOutlined style={{ color: "#52C41A", fontSize: 10 }} />
                  ) : a.status === "limit" ? (
                    <ExclamationCircleOutlined style={{ color: "#FA8C16", fontSize: 10 }} />
                  ) : a.status === "skipped" ? (
                    <span style={{ color: "#D9D9D9", fontSize: 10 }}>●</span>
                  ) : (
                    <LoadingOutlined style={{ color: "#722ED1", fontSize: 10 }} />
                  )}
                  {a.step}
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* ═══════════════════ RESULTS ═══════════════════ */}

      {/* ── 1. TAVSIYALAR ── */}
      {(insightsLoaded || insightsLoading) && (
        <Card
          style={{
            marginBottom: 20, borderRadius: 14, overflow: "hidden",
            borderTop: "3px solid #FAAD14",
          }}
          styles={{ body: { padding: 0 } }}
        >
          {/* Card Header */}
          <div style={{
            padding: "16px 24px", display: "flex", alignItems: "center", justifyContent: "space-between",
            borderBottom: "1px solid #F0F0F0", background: "#FFFDF5",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{
                width: 36, height: 36, borderRadius: 10,
                background: "linear-gradient(135deg, #FAAD14, #D48806)",
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                <BulbOutlined style={{ color: "#fff", fontSize: 18 }} />
              </div>
              <div>
                <Typography.Text strong style={{ fontSize: 15, color: "#141414" }}>
                  Inventarizatsiya va audit tavsiyalari
                </Typography.Text>
                {insightsLoaded && (
                  <Tag style={{ marginLeft: 8, borderRadius: 6, fontSize: 11 }} color="gold">
                    {insights.length} ta tavsiya
                  </Tag>
                )}
              </div>
            </div>
            {insightsLoaded && (
              <Button
                size="small"
                icon={<ReloadOutlined />}
                loading={insightsLoading}
                onClick={loadInsights}
                style={{ borderRadius: 6 }}
              >
                Yangilash
              </Button>
            )}
          </div>

          {/* Content */}
          <div style={{ padding: insightsLoaded ? "16px 24px" : 24 }}>
            {insightsLoading ? (
              <div style={{ textAlign: "center", padding: 32 }}><Spin tip="AI tavsiyalarni tahlil qilmoqda..." /></div>
            ) : insightsLoaded && insights.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {insights.map((item, i) => (
                  <div
                    key={i}
                    style={{
                      display: "flex", gap: 14, padding: "14px 18px", borderRadius: 10,
                      background: "#FAFAFA", border: "1px solid #F0F0F0", alignItems: "flex-start",
                      transition: "all 0.2s",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = "#F5F5F5";
                      e.currentTarget.style.borderColor = `${INSIGHT_COLORS[item.type] || "#1677FF"}40`;
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = "#FAFAFA";
                      e.currentTarget.style.borderColor = "#F0F0F0";
                    }}
                  >
                    <div style={{
                      width: 36, height: 36, borderRadius: 10, flexShrink: 0,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      background: `${INSIGHT_COLORS[item.type] || "#1677FF"}12`,
                      color: INSIGHT_COLORS[item.type] || "#1677FF", fontSize: 17,
                    }}>
                      {INSIGHT_ICONS[item.type] || <InfoCircleOutlined />}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4, flexWrap: "wrap" }}>
                        <Typography.Text strong style={{ fontSize: 13.5, color: "#141414" }}>
                          {item.title}
                        </Typography.Text>
                        <Tag color={PRIORITY_COLORS[item.priority] || "blue"} style={{ fontSize: 10, borderRadius: 4 }}>
                          {item.priority}
                        </Tag>
                      </div>
                      <Typography.Text style={{ fontSize: 12.5, color: "#595959", lineHeight: 1.5 }}>
                        {item.description}
                      </Typography.Text>
                    </div>
                  </div>
                ))}
              </div>
            ) : insightsLoaded ? (
              <Empty description="Tavsiya topilmadi" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            ) : null}
          </div>
        </Card>
      )}

      {/* ── 2. NOSOZLIK XAVFI ── */}
      {(riskLoaded || riskLoading) && (
        <Card
          style={{
            marginBottom: 20, borderRadius: 14, overflow: "hidden",
            borderTop: "3px solid #FF4D4F",
          }}
          styles={{ body: { padding: 0 } }}
        >
          {/* Card Header */}
          <div style={{
            padding: "16px 24px", display: "flex", alignItems: "center", justifyContent: "space-between",
            borderBottom: "1px solid #F0F0F0", background: "#FFFBFB",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{
                width: 36, height: 36, borderRadius: 10,
                background: "linear-gradient(135deg, #FF4D4F, #CF1322)",
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                <SafetyOutlined style={{ color: "#fff", fontSize: 18 }} />
              </div>
              <div>
                <Typography.Text strong style={{ fontSize: 15, color: "#141414" }}>
                  Nosozlik xavfi bashorati
                </Typography.Text>
                {riskLoaded && (
                  <Tag style={{ marginLeft: 8, borderRadius: 6, fontSize: 11 }} color="red">
                    {riskAssets.length} ta aktiv
                  </Tag>
                )}
              </div>
            </div>
            {riskLoaded && (
              <Button
                size="small"
                icon={<ReloadOutlined />}
                loading={riskLoading}
                onClick={loadRisk}
                style={{ borderRadius: 6 }}
              >
                Yangilash
              </Button>
            )}
          </div>

          {/* Content */}
          <div style={{ padding: riskLoaded ? "16px 24px" : 24 }}>
            {riskLoading ? (
              <div style={{ textAlign: "center", padding: 32 }}><Spin tip="Nosozlik xavfini baholash..." /></div>
            ) : riskLoaded && riskAssets.length > 0 ? (
              <>
                {riskAnalysis && (
                  <div style={{
                    padding: "14px 18px", borderRadius: 10, marginBottom: 16,
                    background: "linear-gradient(135deg, #FFF1F0 0%, #FFF7E6 100%)",
                    border: "1px solid #FFD8BF",
                    display: "flex", alignItems: "flex-start", gap: 10,
                  }}>
                    <RobotOutlined style={{ color: "#722ED1", fontSize: 16, marginTop: 2, flexShrink: 0 }} />
                    <Typography.Text style={{ fontSize: 13, color: "#434343", lineHeight: 1.6 }}>
                      {riskAnalysis}
                    </Typography.Text>
                  </div>
                )}
                <Row gutter={[12, 12]}>
                  {riskAssets.map((asset) => (
                    <Col xs={24} sm={12} md={8} key={asset.id}>
                      <div
                        style={{
                          padding: 16, borderRadius: 12,
                          border: "1px solid #F0F0F0",
                          borderLeft: `4px solid ${RISK_COLORS[asset.risk_level] || "#D9D9D9"}`,
                          background: "#fff", cursor: "pointer", height: "100%",
                          transition: "all 0.25s cubic-bezier(0.4,0,0.2,1)",
                        }}
                        onClick={() => navigate(`/assets/${asset.id}`)}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.transform = "translateY(-3px)";
                          e.currentTarget.style.boxShadow = "0 6px 20px rgba(0,0,0,0.08)";
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.transform = "translateY(0)";
                          e.currentTarget.style.boxShadow = "none";
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                          <Typography.Text strong ellipsis style={{ fontSize: 13, maxWidth: "60%" }}>
                            {asset.name}
                          </Typography.Text>
                          <Tag color={RISK_COLORS[asset.risk_level] || "default"} style={{ fontSize: 11, borderRadius: 6 }}>
                            {asset.risk_level}
                          </Tag>
                        </div>
                        <div style={{ marginBottom: 4, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <Typography.Text style={{ fontSize: 11, color: "#8C8C8C" }}>Xavf darajasi</Typography.Text>
                          <Typography.Text strong style={{ fontSize: 12, color: RISK_COLORS[asset.risk_level] || "#141414" }}>
                            {asset.risk_score}%
                          </Typography.Text>
                        </div>
                        <Progress
                          percent={asset.risk_score}
                          size="small"
                          showInfo={false}
                          strokeColor={
                            asset.risk_score >= 70 ? "#FF4D4F" :
                            asset.risk_score >= 50 ? "#FA8C16" :
                            asset.risk_score >= 30 ? "#FAAD14" : "#52C41A"
                          }
                          style={{ marginBottom: 10 }}
                        />
                        {asset.predicted_failure && (
                          <div style={{
                            fontSize: 11, color: "#CF1322", fontWeight: 500,
                            marginBottom: 6, padding: "4px 8px", borderRadius: 6,
                            background: "#FFF1F0", border: "1px solid #FFCCC7",
                          }}>
                            <ClockCircleOutlined style={{ marginRight: 4 }} />
                            {asset.predicted_failure}
                          </div>
                        )}
                        {asset.trend && (
                          <div style={{ fontSize: 11, color: "#8C8C8C", marginBottom: 6, fontStyle: "italic" }}>
                            {asset.trend}
                          </div>
                        )}
                        <div style={{ fontSize: 11.5, color: "#595959", lineHeight: 1.5 }}>
                          {asset.recommendation}
                        </div>
                        <div style={{ marginTop: 8, fontSize: 11, color: "#1677FF" }}>
                          <ArrowRightOutlined style={{ marginRight: 4 }} />Batafsil ko'rish
                        </div>
                      </div>
                    </Col>
                  ))}
                </Row>
              </>
            ) : riskLoaded ? (
              <Empty description="Xavfli aktiv topilmadi" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            ) : null}
          </div>
        </Card>
      )}

      {/* ── 3. MUAMMOLI AKTIVLAR ── */}
      {(problemLoaded || problemLoading) && (
        <Card
          style={{
            marginBottom: 20, borderRadius: 14, overflow: "hidden",
            borderTop: "3px solid #FA8C16",
          }}
          styles={{ body: { padding: 0 } }}
        >
          {/* Card Header */}
          <div style={{
            padding: "16px 24px", display: "flex", alignItems: "center", justifyContent: "space-between",
            borderBottom: "1px solid #F0F0F0", background: "#FFFCF5",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{
                width: 36, height: 36, borderRadius: 10,
                background: "linear-gradient(135deg, #FA8C16, #D46B08)",
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                <ExclamationCircleOutlined style={{ color: "#fff", fontSize: 18 }} />
              </div>
              <div>
                <Typography.Text strong style={{ fontSize: 15, color: "#141414" }}>
                  Muammoli aktivlar tahlili
                </Typography.Text>
                {problemLoaded && (
                  <Tag style={{ marginLeft: 8, borderRadius: 6, fontSize: 11 }} color="orange">
                    {problemAssets.length} ta muammo
                  </Tag>
                )}
              </div>
            </div>
            {problemLoaded && (
              <Button
                size="small"
                icon={<ReloadOutlined />}
                loading={problemLoading}
                onClick={loadProblematic}
                style={{ borderRadius: 6 }}
              >
                Yangilash
              </Button>
            )}
          </div>

          {/* Content */}
          <div style={{ padding: problemLoaded ? "16px 24px" : 24 }}>
            {problemLoading ? (
              <div style={{ textAlign: "center", padding: 32 }}><Spin tip="Muammoli aktivlarni aniqlash..." /></div>
            ) : problemLoaded && problemAssets.length > 0 ? (
              <>
                {problemSummary && (
                  <div style={{
                    padding: "14px 18px", borderRadius: 10, marginBottom: 16,
                    background: "linear-gradient(135deg, #FFF7E6 0%, #FFFBE6 100%)",
                    border: "1px solid #FFE58F",
                    display: "flex", alignItems: "flex-start", gap: 10,
                  }}>
                    <RobotOutlined style={{ color: "#722ED1", fontSize: 16, marginTop: 2, flexShrink: 0 }} />
                    <Typography.Text style={{ fontSize: 13, color: "#434343", lineHeight: 1.6 }}>
                      {problemSummary}
                    </Typography.Text>
                  </div>
                )}
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {problemAssets.map((asset, i) => (
                    <div
                      key={i}
                      style={{
                        display: "flex", gap: 14, padding: "14px 18px", borderRadius: 12,
                        background: "#fff", border: "1px solid #F0F0F0", cursor: "pointer",
                        alignItems: "flex-start", transition: "all 0.25s cubic-bezier(0.4,0,0.2,1)",
                        borderLeft: `4px solid ${SEVERITY_COLORS[asset.severity] || "#FA8C16"}`,
                      }}
                      onClick={() => navigate(`/assets/${asset.id}`)}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.transform = "translateX(4px)";
                        e.currentTarget.style.boxShadow = "0 4px 16px rgba(0,0,0,0.06)";
                        e.currentTarget.style.background = "#FAFAFA";
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = "translateX(0)";
                        e.currentTarget.style.boxShadow = "none";
                        e.currentTarget.style.background = "#fff";
                      }}
                    >
                      <div style={{
                        width: 36, height: 36, borderRadius: 10, flexShrink: 0,
                        display: "flex", alignItems: "center", justifyContent: "center",
                        background: `${SEVERITY_COLORS[asset.severity] || "#FA8C16"}12`,
                      }}>
                        <WarningOutlined style={{
                          fontSize: 18,
                          color: SEVERITY_COLORS[asset.severity] || "#FA8C16",
                        }} />
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6, flexWrap: "wrap" }}>
                          <Typography.Text strong style={{ fontSize: 13.5 }}>{asset.name}</Typography.Text>
                          <Typography.Text style={{ fontSize: 11, fontFamily: "monospace", color: "#0958D9" }}>
                            {asset.inventory_number}
                          </Typography.Text>
                          <Tag color={SEVERITY_COLORS[asset.severity] || "orange"} style={{ fontSize: 10, borderRadius: 4 }}>
                            {asset.severity}
                          </Tag>
                          <Tag style={{ fontSize: 10, borderRadius: 4 }}>{asset.problem_type}</Tag>
                        </div>
                        <Typography.Text style={{ fontSize: 12.5, color: "#595959", display: "block", marginBottom: 6, lineHeight: 1.5 }}>
                          {asset.reason}
                        </Typography.Text>
                        <div style={{ fontSize: 12, color: "#1677FF", fontWeight: 500 }}>
                          <ArrowRightOutlined style={{ marginRight: 4 }} />{asset.recommendation}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : problemLoaded ? (
              <Empty description="Muammoli aktiv topilmadi" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            ) : null}
          </div>
        </Card>
      )}

      {/* ── Empty state: nothing loaded yet and not loading ── */}
      {nothingLoaded && (
        <div style={{
          textAlign: "center", padding: "40px 24px",
          background: "linear-gradient(135deg, #F9F0FF 0%, #E6F4FF 100%)",
          borderRadius: 16, border: "1px dashed #D3ADF7",
        }}>
          <RobotOutlined style={{ fontSize: 40, color: "#722ED1", marginBottom: 12 }} />
          <Typography.Title level={5} style={{ color: "#531DAB", margin: "0 0 8px" }}>
            Hali hech qanday tahlil bajarilmagan
          </Typography.Title>
          <Typography.Paragraph style={{ color: "#8C8C8C", maxWidth: 400, margin: "0 auto", fontSize: 13 }}>
            Yuqoridagi kartalardan birini bosing yoki "Barcha tahlillarni boshlash" tugmasini ishlatib,
            AI tahlilini boshlang.
          </Typography.Paragraph>
        </div>
      )}
    </div>
  );
}
