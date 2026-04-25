"use client";
import { useState } from "react";
import Link from "next/link";
import {
  User, Shield, Bell, Mic2, Globe2, Palette, HardDrive,
  HelpCircle, Lock, ChevronRight, Play, Trash2, Plus,
  ToggleLeft, ToggleRight, MessageSquare,
} from "lucide-react";
import styles from "./settings.module.css";

const NAV_ITEMS = [
  { icon: <User size={18} />, label: "Profile & Account" },
  { icon: <Shield size={18} />, label: "Privacy & Security", active: true },
  { icon: <Bell size={18} />, label: "Notifications" },
  { icon: <Mic2 size={18} />, label: "Audio & Video" },
  { icon: <Mic2 size={18} />, label: "Voice Cloning" },
  { icon: <Globe2 size={18} />, label: "Translation" },
  { icon: <Palette size={18} />, label: "Appearance" },
  { icon: <HardDrive size={18} />, label: "Storage & Data" },
  { icon: <HelpCircle size={18} />, label: "Help & Support" },
];

const VOICE_MODELS = [
  { id: "1", name: "My Original Voice", created: "Apr 10, 2026" },
  { id: "2", name: "Calm Professional", created: "Apr 18, 2026" },
];

const LANGUAGES = ["English", "Japanese", "Spanish", "Hindi", "German", "French", "Chinese", "Arabic", "Portuguese", "Korean"];

function Toggle({ on, onToggle }: { on: boolean; onToggle: () => void }) {
  return (
    <button onClick={onToggle} className={styles.toggle} aria-label="Toggle">
      <div className={`${styles.toggleTrack} ${on ? styles.toggleOn : ""}`}>
        <div className={styles.toggleThumb} />
      </div>
    </button>
  );
}

export default function SettingsPage() {
  const [e2e, setE2e] = useState(true);
  const [tfa, setTfa] = useState(false);
  const [autoTranslate, setAutoTranslate] = useState(true);
  const [callTranslation, setCallTranslation] = useState(true);
  const [primaryLang, setPrimaryLang] = useState("English");
  const [targetLang, setTargetLang] = useState("Japanese");
  const [activeSection, setActiveSection] = useState(1);

  return (
    <div className={styles.page}>
      {/* Sidebar */}
      <aside className={styles.sidebar}>
        <Link href="/" className={styles.sidebarLogo}>
          <div className={styles.logoIcon}>G</div>
        </Link>
        <Link href="/dashboard" className={styles.sidebarIcon} data-tooltip="Chats">
          <MessageSquare size={20} />
        </Link>
        <Link href="/settings" className={`${styles.sidebarIcon} ${styles.sidebarIconActive}`} data-tooltip="Settings">
          <User size={20} />
        </Link>
      </aside>

      <div className={styles.layout}>
        {/* Settings Nav */}
        <nav className={styles.settingsNav}>
          <h2 className={styles.settingsTitle}>Settings</h2>
          {NAV_ITEMS.map((item, i) => (
            <button
              key={item.label}
              className={`${styles.navItem} ${activeSection === i ? styles.navItemActive : ""}`}
              onClick={() => setActiveSection(i)}
            >
              <span className={styles.navIcon}>{item.icon}</span>
              {item.label}
              <ChevronRight size={14} style={{ marginLeft: "auto", opacity: 0.4 }} />
            </button>
          ))}
        </nav>

        {/* Settings Content */}
        <div className={styles.content}>
          {/* E2E Encryption */}
          <section className={styles.section}>
            <div className={`card ${styles.encSection}`}>
              <div className={styles.encIcon}>
                <Shield size={36} />
              </div>
              <div className={styles.encInfo}>
                <h3 className={styles.encTitle}>End-to-End Encryption</h3>
                <p className={styles.encDesc}>Your communications are protected with AES-256 encryption. Keys never leave your device.</p>
              </div>
              <div className={styles.encRight}>
                <div className={`badge badge-success`}><Lock size={11} /> Active</div>
                <Toggle on={e2e} onToggle={() => {}} />
              </div>
            </div>
            <div className={styles.encActions}>
              <button className="btn btn-ghost btn-sm"><Lock size={14} /> View Encryption Keys</button>
              <button className="btn btn-ghost btn-sm"><Lock size={14} /> Verify Contact Identity</button>
            </div>
          </section>

          {/* 2FA */}
          <section className={styles.section}>
            <h3 className={styles.sectionTitle}>Two-Factor Authentication</h3>
            <div className={`card ${styles.row}`}>
              <div>
                <p className={styles.rowTitle}>Authenticator App</p>
                <p className={styles.rowDesc}>Add an extra layer of security with a TOTP authenticator (Google Authenticator, Authy)</p>
              </div>
              <Toggle on={tfa} onToggle={() => setTfa(!tfa)} />
            </div>
            {tfa && (
              <button className="btn btn-ghost btn-sm" style={{ marginTop: 8 }}>Setup Authenticator App</button>
            )}
          </section>

          {/* Voice Cloning */}
          <section className={styles.section}>
            <div className={styles.sectionHeader}>
              <h3 className={styles.sectionTitle}>Voice Clone Models</h3>
              <button className="btn btn-primary btn-sm"><Plus size={14} /> Create New Clone</button>
            </div>
            <div className={styles.voiceList}>
              {VOICE_MODELS.map((model) => (
                <div key={model.id} className={`card ${styles.voiceCard}`}>
                  <div className={styles.waveformMini}>
                    {Array.from({ length: 12 }).map((_, i) => (
                      <div key={i} className={styles.wavebar} style={{ height: `${20 + Math.sin(i) * 15}px` }} />
                    ))}
                  </div>
                  <div className={styles.voiceInfo}>
                    <span className={styles.voiceName}>{model.name}</span>
                    <span className={styles.voiceDate}>Created {model.created}</span>
                  </div>
                  <div className={styles.voiceActions}>
                    <button className="btn btn-icon btn-ghost"><Play size={15} /></button>
                    <button className="btn btn-icon btn-ghost" style={{ color: "var(--color-danger)" }}><Trash2 size={15} /></button>
                  </div>
                </div>
              ))}
            </div>
            <p className={styles.cloneHint}>
              <Mic2 size={13} /> Record 30 seconds of your voice to create a perfect AI clone
            </p>
          </section>

          {/* Translation */}
          <section className={styles.section}>
            <h3 className={styles.sectionTitle}>Translation Preferences</h3>
            <div className={`card ${styles.translationCard}`}>
              <div className={styles.langRow}>
                <div className={styles.langField}>
                  <label className={styles.langLabel}>Primary Language</label>
                  <select className={`input ${styles.langSelect}`} value={primaryLang} onChange={(e) => setPrimaryLang(e.target.value)}>
                    {LANGUAGES.map((l) => <option key={l}>{l}</option>)}
                  </select>
                </div>
                <div className={styles.langField}>
                  <label className={styles.langLabel}>Translate Messages To</label>
                  <select className={`input ${styles.langSelect}`} value={targetLang} onChange={(e) => setTargetLang(e.target.value)}>
                    {LANGUAGES.map((l) => <option key={l}>{l}</option>)}
                  </select>
                </div>
              </div>
              <div className={styles.googleBadge}>
                <Globe2 size={14} />
                <span>Translation Provider: <strong>Google Cloud Translate API</strong></span>
              </div>
              <div className={styles.row} style={{ padding: "12px 0", borderTop: "1px solid var(--glass-border)" }}>
                <div>
                  <p className={styles.rowTitle}>Auto-Translate Incoming Messages</p>
                  <p className={styles.rowDesc}>Automatically translates messages from other languages</p>
                </div>
                <Toggle on={autoTranslate} onToggle={() => setAutoTranslate(!autoTranslate)} />
              </div>
              <div className={styles.row} style={{ padding: "12px 0", borderTop: "1px solid var(--glass-border)" }}>
                <div>
                  <p className={styles.rowTitle}>Real-Time Call Translation</p>
                  <p className={styles.rowDesc}>Show live transcription and translation during voice/video calls</p>
                </div>
                <Toggle on={callTranslation} onToggle={() => setCallTranslation(!callTranslation)} />
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
