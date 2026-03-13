import { useState, useRef, useEffect } from "react";
import { Button, Input, Typography, Spin, Badge } from "antd";
import {
  RobotOutlined, SendOutlined, CloseOutlined,
  BulbOutlined,
} from "@ant-design/icons";
import { aiChat } from "../../api";

type ChatMessage = {
  role: "user" | "ai";
  text: string;
  suggestions?: string[];
  time: string;
};

const QUICK_QUESTIONS = [
  "Jami nechta aktiv bor?",
  "Qaysi bo'limda eng ko'p aktiv bor?",
  "Ta'mirda turgan barcha aktivlar ro'yxati",
  "O'tgan oy bilan solishtirganda holat qanday?",
  "Kafolati tugayotgan aktivlar bormi?",
  "IT bo'limida qancha aktiv bor?",
];

export default function AIChatbot() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [hasNewMessage, setHasNewMessage] = useState(false);
  const chatBodyRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<any>(null);

  const scrollToBottom = () => {
    if (chatBodyRef.current) {
      chatBodyRef.current.scrollTop = chatBodyRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  useEffect(() => {
    if (open && inputRef.current) {
      inputRef.current.focus();
    }
  }, [open]);

  const getTimeStr = () => {
    const now = new Date();
    return `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")}`;
  };

  const sendMessage = async (text: string) => {
    if (!text.trim() || loading) return;

    const userMsg: ChatMessage = { role: "user", text: text.trim(), time: getTimeStr() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const { data } = await aiChat(text.trim());
      const aiMsg: ChatMessage = {
        role: "ai",
        text: data.answer || "Javob olishda xatolik yuz berdi",
        suggestions: data.suggestions || [],
        time: getTimeStr(),
      };
      setMessages((prev) => [...prev, aiMsg]);
      if (!open) setHasNewMessage(true);
    } catch (e: any) {
      const errorMsg: ChatMessage = {
        role: "ai",
        text: e.response?.data?.detail || "AI xizmati hozircha mavjud emas. Keyinroq urinib ko'ring.",
        time: getTimeStr(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleOpen = () => {
    setOpen(true);
    setHasNewMessage(false);
  };

  return (
    <>
      {/* Floating Button — pill shaped with label */}
      {!open && (
        <div
          onClick={handleOpen}
          className="ai-chat-fab"
          style={{
            position: "fixed",
            bottom: 24,
            right: 24,
            zIndex: 1000,
            cursor: "pointer",
          }}
        >
          {/* Pulse ring */}
          <div
            style={{
              position: "absolute",
              inset: -4,
              borderRadius: 30,
              border: "2px solid rgba(114, 46, 209, 0.3)",
              animation: "aiChatPulse 2.5s ease-in-out infinite",
              pointerEvents: "none",
            }}
          />
          <Badge dot={hasNewMessage} offset={[-8, 4]}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "12px 20px 12px 16px",
                borderRadius: 28,
                background: "linear-gradient(135deg, #722ED1 0%, #531DAB 100%)",
                boxShadow: "0 6px 24px rgba(114, 46, 209, 0.45), 0 2px 8px rgba(0,0,0,0.1)",
                transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = "translateY(-3px) scale(1.03)";
                e.currentTarget.style.boxShadow = "0 10px 32px rgba(114, 46, 209, 0.55), 0 4px 12px rgba(0,0,0,0.12)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "translateY(0) scale(1)";
                e.currentTarget.style.boxShadow = "0 6px 24px rgba(114, 46, 209, 0.45), 0 2px 8px rgba(0,0,0,0.1)";
              }}
            >
              <div style={{
                width: 32, height: 32, borderRadius: "50%",
                background: "rgba(255,255,255,0.2)",
                display: "flex", alignItems: "center", justifyContent: "center",
                flexShrink: 0,
              }}>
                <RobotOutlined style={{ fontSize: 18, color: "#fff" }} />
              </div>
              <span style={{
                color: "#fff", fontSize: 14, fontWeight: 600,
                letterSpacing: "0.01em", whiteSpace: "nowrap",
              }}>
                AI Yordamchi
              </span>
            </div>
          </Badge>
        </div>
      )}

      {/* Chat Window */}
      {open && (
        <div
          style={{
            position: "fixed",
            bottom: 24,
            right: 24,
            width: 400,
            maxWidth: "calc(100vw - 32px)",
            height: 560,
            maxHeight: "calc(100vh - 100px)",
            borderRadius: 18,
            overflow: "hidden",
            boxShadow: "0 16px 56px rgba(0,0,0,0.16), 0 6px 20px rgba(114,46,209,0.1)",
            display: "flex",
            flexDirection: "column",
            zIndex: 1001,
            background: "#fff",
            border: "1px solid #F0F0F0",
            animation: "chatWindowIn 0.3s cubic-bezier(0.16, 1, 0.3, 1)",
          }}
        >
          {/* Header */}
          <div
            style={{
              background: "linear-gradient(135deg, #722ED1 0%, #531DAB 100%)",
              padding: "16px 20px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              flexShrink: 0,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <div
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: 10,
                  background: "rgba(255,255,255,0.2)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <RobotOutlined style={{ fontSize: 20, color: "#fff" }} />
              </div>
              <div>
                <div style={{ color: "#fff", fontWeight: 600, fontSize: 15, lineHeight: 1.2 }}>
                  AI Yordamchi
                </div>
                <div style={{ color: "rgba(255,255,255,0.7)", fontSize: 11 }}>
                  Bank aktivlari bo'yicha savol bering
                </div>
              </div>
            </div>
            <Button
              type="text"
              icon={<CloseOutlined style={{ color: "#fff", fontSize: 16 }} />}
              onClick={() => setOpen(false)}
              style={{ border: "none" }}
            />
          </div>

          {/* Chat Body */}
          <div
            ref={chatBodyRef}
            style={{
              flex: 1,
              overflowY: "auto",
              padding: "16px",
              background: "#F9FAFB",
              display: "flex",
              flexDirection: "column",
              gap: 12,
            }}
          >
            {/* Welcome Message */}
            {messages.length === 0 && !loading && (
              <div style={{ textAlign: "center", padding: "24px 8px" }}>
                <div
                  style={{
                    width: 56,
                    height: 56,
                    borderRadius: 16,
                    background: "linear-gradient(135deg, #F9F0FF, #E6F4FF)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    margin: "0 auto 16px",
                  }}
                >
                  <RobotOutlined style={{ fontSize: 28, color: "#722ED1" }} />
                </div>
                <Typography.Title level={5} style={{ margin: "0 0 4px", color: "#141414" }}>
                  Assalomu alaykum!
                </Typography.Title>
                <Typography.Paragraph style={{ color: "#8C8C8C", fontSize: 13, margin: "0 0 20px" }}>
                  Men bank aktivlari bo'yicha AI yordamchiman. Savol bering!
                </Typography.Paragraph>
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {QUICK_QUESTIONS.map((q, i) => (
                    <div
                      key={i}
                      onClick={() => sendMessage(q)}
                      style={{
                        padding: "10px 14px",
                        borderRadius: 10,
                        background: "#fff",
                        border: "1px solid #E8E8E8",
                        cursor: "pointer",
                        fontSize: 13,
                        color: "#531DAB",
                        display: "flex",
                        alignItems: "center",
                        gap: 8,
                        transition: "all 0.2s",
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.borderColor = "#B37FEB";
                        e.currentTarget.style.background = "#F9F0FF";
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.borderColor = "#E8E8E8";
                        e.currentTarget.style.background = "#fff";
                      }}
                    >
                      <BulbOutlined style={{ color: "#B37FEB", flexShrink: 0 }} />
                      {q}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Messages */}
            {messages.map((msg, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: msg.role === "user" ? "flex-end" : "flex-start",
                }}
              >
                <div
                  style={{
                    maxWidth: "85%",
                    padding: "10px 14px",
                    borderRadius: msg.role === "user" ? "14px 14px 4px 14px" : "14px 14px 14px 4px",
                    background: msg.role === "user"
                      ? "linear-gradient(135deg, #722ED1, #531DAB)"
                      : "#fff",
                    color: msg.role === "user" ? "#fff" : "#141414",
                    fontSize: 13,
                    lineHeight: 1.6,
                    boxShadow: msg.role === "ai" ? "0 1px 4px rgba(0,0,0,0.06)" : "none",
                    border: msg.role === "ai" ? "1px solid #F0F0F0" : "none",
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                  }}
                >
                  {msg.text}
                </div>
                <div style={{ fontSize: 10, color: "#BFBFBF", marginTop: 4, padding: "0 4px" }}>
                  {msg.time}
                </div>
                {/* Suggestions */}
                {msg.role === "ai" && msg.suggestions && msg.suggestions.length > 0 && (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 8, maxWidth: "85%" }}>
                    {msg.suggestions.map((s, j) => (
                      <div
                        key={j}
                        onClick={() => sendMessage(s)}
                        style={{
                          padding: "5px 10px",
                          borderRadius: 8,
                          background: "#F9F0FF",
                          border: "1px solid #D3ADF7",
                          cursor: "pointer",
                          fontSize: 11,
                          color: "#531DAB",
                          transition: "all 0.2s",
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = "#EFDBFF";
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = "#F9F0FF";
                        }}
                      >
                        {s}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {/* Loading */}
            {loading && (
              <div style={{ display: "flex", alignItems: "flex-start" }}>
                <div
                  style={{
                    padding: "12px 16px",
                    borderRadius: "14px 14px 14px 4px",
                    background: "#fff",
                    border: "1px solid #F0F0F0",
                    boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
                  }}
                >
                  <Spin size="small" />
                  <span style={{ marginLeft: 8, fontSize: 12, color: "#8C8C8C" }}>
                    AI javob yozmoqda...
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <div
            style={{
              padding: "12px 16px",
              borderTop: "1px solid #F0F0F0",
              background: "#fff",
              flexShrink: 0,
            }}
          >
            <div style={{ display: "flex", gap: 8 }}>
              <Input
                ref={inputRef}
                placeholder="Savolingizni yozing..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onPressEnter={() => sendMessage(input)}
                disabled={loading}
                style={{
                  borderRadius: 10,
                  border: "1px solid #E8E8E8",
                  padding: "8px 14px",
                }}
              />
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={() => sendMessage(input)}
                loading={loading}
                disabled={!input.trim()}
                style={{
                  borderRadius: 10,
                  background: input.trim() ? "linear-gradient(135deg, #722ED1, #531DAB)" : undefined,
                  borderColor: "#722ED1",
                  height: 40,
                  width: 40,
                  minWidth: 40,
                }}
              />
            </div>
          </div>
        </div>
      )}
    </>
  );
}
