"use client";
import { useState } from "react";
import Link from "next/link";
import {
  MessageSquare, Phone, Users, Globe2, Settings,
  Search, Lock, Send, Smile, Paperclip, Mic,
  Video, Info, MoreVertical, Plus, Check, CheckCheck,
} from "lucide-react";
import styles from "./dashboard.module.css";

const CONVERSATIONS = [
  { id: "1", name: "Aiko Tanaka", avatar: "AT", online: true, lang: "🇯🇵", lastMsg: "こんにちは！How are you?", time: "2m", unread: 3 },
  { id: "2", name: "Carlos Reyes", avatar: "CR", online: true, lang: "🇪🇸", lastMsg: "The meeting is at 3pm", time: "15m", unread: 0 },
  { id: "3", name: "Priya Sharma", avatar: "PS", online: false, lang: "🇮🇳", lastMsg: "Check the new feature!", time: "1h", unread: 1 },
  { id: "4", name: "Tech Talk Room", avatar: "TT", online: true, lang: "🌐", lastMsg: "256 members online", time: "3h", unread: 0, isRoom: true },
  { id: "5", name: "Lena Fischer", avatar: "LF", online: false, lang: "🇩🇪", lastMsg: "Guten Morgen!", time: "5h", unread: 0 },
];

const MESSAGES = [
  { id: "1", sent: false, text: "こんにちは！How are you doing today?", translation: "Hello! How are you doing today?", time: "10:23 AM", read: true },
  { id: "2", sent: true, text: "I'm great, thanks! Working on a new project.", time: "10:24 AM", read: true },
  { id: "3", sent: false, text: "That sounds exciting! What kind of project?", time: "10:25 AM", read: true },
  { id: "4", sent: true, text: "A secure communication platform with AI voice cloning 🎙️", time: "10:27 AM", read: false },
];

const LANGS = ["English", "Japanese", "Spanish", "Hindi", "German", "French", "Chinese", "Arabic"];

export default function DashboardPage() {
  const [active, setActive] = useState(CONVERSATIONS[0]);
  const [message, setMessage] = useState("");
  const [targetLang, setTargetLang] = useState("English");
  const [translateOn, setTranslateOn] = useState(true);

  return (
    <div className={styles.layout}>
      {/* Icon Sidebar */}
      <aside className={styles.sidebar}>
        <Link href="/" className={styles.sidebarLogo}>
          <div className={styles.logoIcon}>G</div>
        </Link>
        <nav className={styles.sidebarNav}>
          {[
            { icon: <MessageSquare size={20} />, label: "Chats", href: "/dashboard", active: true },
            { icon: <Phone size={20} />, label: "Calls", href: "/calls" },
            { icon: <Users size={20} />, label: "Contacts", href: "/contacts" },
            { icon: <Globe2 size={20} />, label: "Rooms", href: "/rooms" },
          ].map((item) => (
            <Link
              key={item.label}
              href={item.href}
              className={`${styles.sidebarIcon} ${item.active ? styles.sidebarIconActive : ""}`}
              data-tooltip={item.label}
            >
              {item.icon}
            </Link>
          ))}
        </nav>
        <Link href="/settings" className={styles.sidebarIcon} style={{ marginTop: "auto" }} data-tooltip="Settings">
          <Settings size={20} />
        </Link>
        <div className={styles.sidebarAvatar}>
          <div className={styles.avatarCircle}>U</div>
          <div className={`status-dot status-online ${styles.avatarDot}`} />
        </div>
      </aside>

      {/* Conversation List */}
      <div className={styles.chatList}>
        <div className={styles.chatListHeader}>
          <h2 className={styles.chatListTitle}>Messages</h2>
          <button className="btn btn-icon btn-ghost"><Plus size={18} /></button>
        </div>
        <div className={styles.searchWrap}>
          <Search size={15} className={styles.searchIcon} />
          <input className={`input ${styles.searchInput}`} placeholder="Search conversations..." />
        </div>
        <div className={styles.filterTabs}>
          {["All", "Unread", "Groups"].map((f) => (
            <button key={f} className={`tab ${f === "All" ? "active" : ""}`}>{f}</button>
          ))}
        </div>
        <div className={styles.convList}>
          {CONVERSATIONS.map((c) => (
            <button
              key={c.id}
              className={`${styles.convItem} ${active.id === c.id ? styles.convItemActive : ""}`}
              onClick={() => setActive(c)}
            >
              <div className={styles.convAvatar}>
                <div className={`${styles.avatarCircle} ${c.online ? styles.avatarOnline : ""}`}>
                  {c.avatar}
                </div>
                {c.online && <div className={`status-dot status-online ${styles.avatarDot}`} />}
              </div>
              <div className={styles.convInfo}>
                <div className={styles.convTop}>
                  <span className={styles.convName}>{c.name}</span>
                  <span className={styles.convTime}>{c.time}</span>
                </div>
                <div className={styles.convBottom}>
                  <span className={styles.convMsg}>{c.lastMsg}</span>
                  {c.unread > 0 && <span className={styles.unreadBadge}>{c.unread}</span>}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Chat Area */}
      <div className={styles.chatArea}>
        {/* Chat Header */}
        <div className={styles.chatHeader}>
          <div className={styles.chatHeaderLeft}>
            <div className={styles.avatarCircle}>{active.avatar}</div>
            <div>
              <div className={styles.chatName}>{active.name}</div>
              <div className={styles.chatStatus}>
                <div className="status-dot status-online" />
                Active now
              </div>
            </div>
          </div>
          <div className={styles.chatHeaderRight}>
            <div className={`badge badge-success ${styles.encBadge}`}>
              <Lock size={10} /> E2E Encrypted
            </div>
            <Link href="/call" className="btn btn-icon btn-ghost"><Video size={18} /></Link>
            <Link href="/call" className="btn btn-icon btn-ghost"><Phone size={18} /></Link>
            <button className="btn btn-icon btn-ghost"><Info size={18} /></button>
            <button className="btn btn-icon btn-ghost"><MoreVertical size={18} /></button>
          </div>
        </div>

        {/* Translation Bar */}
        {translateOn && (
          <div className={styles.translateBar}>
            <Globe2 size={14} style={{ color: "var(--color-secondary)" }} />
            <span>Auto-translating to</span>
            <select
              className={styles.langSelect}
              value={targetLang}
              onChange={(e) => setTargetLang(e.target.value)}
            >
              {LANGS.map((l) => <option key={l}>{l}</option>)}
            </select>
            <span style={{ marginLeft: "auto", color: "var(--color-text-faint)", fontSize: "0.8rem" }}>
              Powered by Google Translate
            </span>
            <button className={styles.translateToggle} onClick={() => setTranslateOn(false)}>✕</button>
          </div>
        )}

        {/* Messages */}
        <div className={styles.messages}>
          {MESSAGES.map((msg) => (
            <div key={msg.id} className={`${styles.msgRow} ${msg.sent ? styles.msgRowSent : ""}`}>
              {!msg.sent && <div className={styles.msgAvatar}>{active.avatar}</div>}
              <div className={`${styles.bubble} ${msg.sent ? styles.bubbleSent : styles.bubbleRecv}`}>
                <p className={styles.bubbleText}>{msg.text}</p>
                {msg.translation && !msg.sent && (
                  <p className={styles.bubbleTranslation}>
                    <Globe2 size={11} /> {msg.translation}
                  </p>
                )}
                <div className={styles.bubbleMeta}>
                  <span className={styles.bubbleTime}>{msg.time}</span>
                  {msg.sent && (
                    msg.read
                      ? <CheckCheck size={13} style={{ color: "var(--color-secondary)" }} />
                      : <Check size={13} />
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Input Bar */}
        <div className={styles.inputBar}>
          <button className="btn btn-icon btn-ghost"><Paperclip size={18} /></button>
          <button className="btn btn-icon btn-ghost"><Smile size={18} /></button>
          <input
            className={`input ${styles.msgInput}`}
            placeholder="Type a message..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && message && setMessage("")}
          />
          {message ? (
            <button className="btn btn-primary btn-icon" onClick={() => setMessage("")}>
              <Send size={16} />
            </button>
          ) : (
            <button className="btn btn-icon btn-ghost"><Mic size={18} /></button>
          )}
        </div>
      </div>
    </div>
  );
}
