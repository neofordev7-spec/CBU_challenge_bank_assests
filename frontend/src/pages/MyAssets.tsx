import { useEffect, useState } from "react";
import { Card, Table, Tag, Spin, Row, Col, Empty } from "antd";
import {
  LaptopOutlined, HistoryOutlined,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { getMyAssets } from "../api";
import type { Asset } from "../types";
import { STATUS_CONFIG } from "../utils/constants";
import { useAuth } from "../context/AuthContext";
import dayjs from "dayjs";

interface AssignmentHistory {
  id: number;
  asset_id: number;
  asset_name: string | null;
  asset_inventory_number: string | null;
  asset_status: string | null;
  assigned_at: string | null;
  returned_at: string | null;
  return_reason: string | null;
  department_name: string | null;
}

export default function MyAssets() {
  const navigate = useNavigate();
  useAuth();
  const [currentAssets, setCurrentAssets] = useState<Asset[]>([]);
  const [history, setHistory] = useState<AssignmentHistory[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMyAssets()
      .then(({ data }) => {
        setCurrentAssets(data.current_assets);
        setHistory(data.history);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", height: 400, gap: 16 }}>
        <Spin size="large" />
        <span style={{ fontSize: 13, color: "#8C8C8C", fontWeight: 450 }}>Aktivlaringiz yuklanmoqda...</span>
      </div>
    );
  }

  return (
    <div className="animate-in">

      {/* Stat cards */}
      <Row gutter={[20, 20]} style={{ marginBottom: 20 }}>
        <Col xs={12} sm={8}>
          <div className="stat-card">
            <div className="stat-icon blue"><LaptopOutlined /></div>
            <div className="stat-value">{currentAssets.length}</div>
            <div className="stat-label">Hozirgi aktivlar</div>
          </div>
        </Col>
        <Col xs={12} sm={8}>
          <div className="stat-card">
            <div className="stat-icon green"><HistoryOutlined /></div>
            <div className="stat-value">{history.length}</div>
            <div className="stat-label">Jami tarix</div>
          </div>
        </Col>
        <Col xs={12} sm={8}>
          <div className="stat-card">
            <div className="stat-icon orange"><LaptopOutlined /></div>
            <div className="stat-value">{history.filter((h) => !h.returned_at).length}</div>
            <div className="stat-label">Faol biriktirmalar</div>
          </div>
        </Col>
      </Row>

      {/* Hozirgi aktivlar */}
      <Card
        title={
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <LaptopOutlined style={{ color: "#0958D9" }} />
            <span>Hozirda menga biriktirilgan aktivlar</span>
            <Tag color="blue">{currentAssets.length} ta</Tag>
          </div>
        }
        className="chart-card"
        style={{ marginBottom: 16 }}
      >
        {currentAssets.length === 0 ? (
          <Empty description="Hozirda sizga biriktirilgan aktiv yo'q" />
        ) : (
          <Table
            dataSource={currentAssets}
            rowKey="id"
            size="small"
            pagination={false}
            onRow={(record) => ({
              onClick: () => navigate(`/assets/${record.id}`),
              style: { cursor: "pointer" },
            })}
            columns={[
              {
                title: "Inventar №",
                dataIndex: "inventory_number",
                key: "inv",
                render: (v: string) => <span style={{ fontWeight: 600, color: "#0958D9" }}>{v}</span>,
              },
              { title: "Nomi", dataIndex: "name", key: "name" },
              {
                title: "Kategoriya",
                dataIndex: ["category", "name"],
                key: "cat",
              },
              {
                title: "Status",
                dataIndex: "status",
                key: "status",
                render: (s: string) => (
                  <Tag color={STATUS_CONFIG[s]?.color} style={{ borderRadius: 6 }}>
                    {STATUS_CONFIG[s]?.label || s}
                  </Tag>
                ),
              },
              {
                title: "Narxi",
                dataIndex: "purchase_price",
                key: "price",
                render: (v: number) => v ? `${Number(v).toLocaleString("ru-RU")} so'm` : "—",
              },
            ]}
          />
        )}
      </Card>

      {/* Tarix */}
      <Card
        title={
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <HistoryOutlined style={{ color: "#722ED1" }} />
            <span>Biriktirish tarixi</span>
          </div>
        }
        className="chart-card"
      >
        {history.length === 0 ? (
          <Empty description="Tarix mavjud emas" />
        ) : (
          <Table
            dataSource={history}
            rowKey="id"
            size="small"
            pagination={{ pageSize: 10 }}
            columns={[
              {
                title: "Aktiv",
                key: "asset",
                render: (_: unknown, r: AssignmentHistory) => (
                  <div>
                    <div style={{ fontWeight: 600 }}>{r.asset_name}</div>
                    <div style={{ fontSize: 12, color: "#8c8c8c" }}>{r.asset_inventory_number}</div>
                  </div>
                ),
              },
              {
                title: "Status",
                dataIndex: "asset_status",
                key: "status",
                render: (s: string) => s ? (
                  <Tag color={STATUS_CONFIG[s]?.color} style={{ borderRadius: 6 }}>
                    {STATUS_CONFIG[s]?.label || s}
                  </Tag>
                ) : "—",
              },
              {
                title: "Berilgan",
                dataIndex: "assigned_at",
                key: "assigned",
                render: (v: string) => v ? dayjs(v).format("DD.MM.YYYY") : "—",
              },
              {
                title: "Qaytarilgan",
                dataIndex: "returned_at",
                key: "returned",
                render: (v: string) =>
                  v ? dayjs(v).format("DD.MM.YYYY") : <Tag color="green" style={{ borderRadius: 6 }}>Hozirda</Tag>,
              },
              {
                title: "Qaytarish sababi",
                dataIndex: "return_reason",
                key: "reason",
                render: (v: string) => v || "—",
              },
              {
                title: "Bo'lim",
                dataIndex: "department_name",
                key: "dept",
                render: (v: string) => v || "—",
              },
            ]}
          />
        )}
      </Card>
    </div>
  );
}
