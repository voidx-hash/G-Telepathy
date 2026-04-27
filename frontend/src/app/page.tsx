"use client";
import Link from "next/link";
import {
  Shield, Mic2, Globe2, Zap, Lock, Users, ChevronRight,
  MessageSquare, Phone, Star,
} from "lucide-react";
import styles from "./page.module.css";

const FEATURES = [
  {
    icon: <Lock size={28} />,
    title: "Military-Grade E2E Encryption",
    desc: "AES-256 encryption on every message and call. Your keys never leave your device.",
    color: "var(--color-primary)",
  },
  {
    icon: <Mic2 size={28} />,
    title: "AI Voice Cloning",
    desc: "Clone any voice in 30 seconds. Apply it in real-time calls with pitch and speed modulation.",
    color: "var(--color-secondary)",
  },
  {
    icon: <Globe2 size={28} />,
    title: "Real-Time Translation",
    desc: "Powered by Google Cloud Translate. Break language barriers across 100+ languages instantly.",
    color: "var(--color-success)",
  },
  {
    icon: <Phone size={28} />,
    title: "Encrypted Voice & Video",
    desc: "WebRTC peer-to-peer calls with live transcription and translation overlays.",
    color: "#f59e0b",
  },
  {
    icon: <Users size={28} />,
    title: "Global Rooms",
    desc: "Join public rooms by topic or language. Connect with thousands of people worldwide.",
    color: "var(--color-primary)",
  },
  {
    icon: <Zap size={28} />,
    title: "Instant & Reliable",
    desc: "Socket.io powered real-time messaging with sub-100ms delivery and offline queuing.",
    color: "var(--color-secondary)",
  },
];

const STATS = [
  { value: "AES-256", label: "Encryption Standard" },
  { value: "100+", label: "Languages Supported" },
  { value: "E2E", label: "Zero Knowledge" },
  { value: "<100ms", label: "Message Latency" },
];

export default function LandingPage() {
  return (
    <div className={styles.page}>
      {/* Background */}
      <div className={styles.bgGlow} aria-hidden />
      <div className={styles.bgGrid} aria-hidden />

      {/* Navbar */}
      <nav className={styles.nav}>
        <div className={styles.navLogo}>
          <div className={styles.logoIcon}>G</div>
          <span className={styles.logoText}>Telepathy</span>
        </div>
        <div className={styles.navLinks}>
          <a href="#features" className={styles.navLink}>Features</a>
          <a href="#security" className={styles.navLink}>Security</a>
          <Link href="/login" className="btn btn-ghost btn-sm">Sign In</Link>
          <Link href="/register" className="btn btn-primary btn-sm">Get Started</Link>
        </div>
      </nav>

      {/* Beta Testing Banner */}
      <div className={styles.betaBanner}>
        <span className={styles.betaDot} aria-hidden />
        <strong>🚀 Now Open for Beta Testing</strong>
        &nbsp;— G Telepathy is live and accepting early users. Features may evolve. Your feedback shapes the platform.
        <a href="https://github.com/voidx-hash/G-Telepathy/issues" target="_blank" rel="noopener noreferrer" className={styles.betaLink}>
          Report an Issue →
        </a>
      </div>

      {/* Hero */}
      <section className={styles.hero}>
        <div className={`badge badge-cyan ${styles.heroBadge}`}>
          <Shield size={12} />
          Beta · AES-256 End-to-End Encrypted
        </div>
        <h1 className={styles.heroTitle}>
          Communicate<br />
          <span className="gradient-text">Without Limits</span>
        </h1>
        <p className={styles.heroSub}>
          The most secure communication platform on earth.
          AI voice cloning, real-time translation in 100+ languages,
          and military-grade E2E encryption — all in one place.
        </p>
        <div className={styles.heroCta}>
          <Link href="/register" className="btn btn-primary btn-lg">
            Start for Free <ChevronRight size={18} />
          </Link>
          <Link href="/login" className="btn btn-ghost btn-lg">
            Sign In Securely
          </Link>
        </div>

        {/* Stats row */}
        <div className={styles.stats}>
          {STATS.map((s) => (
            <div key={s.label} className={styles.stat}>
              <span className={`gradient-text ${styles.statValue}`}>{s.value}</span>
              <span className={styles.statLabel}>{s.label}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section id="features" className={styles.features}>
        <h2 className={styles.sectionTitle}>
          Everything you need to <span className="gradient-text">connect securely</span>
        </h2>
        <p className={styles.sectionSub}>
          Built for privacy-first people who need powerful communication tools.
        </p>
        <div className={styles.featuresGrid}>
          {FEATURES.map((f) => (
            <div key={f.title} className={`card ${styles.featureCard}`}>
              <div className={styles.featureIcon} style={{ color: f.color, background: `${f.color}18` }}>
                {f.icon}
              </div>
              <h3 className={styles.featureTitle}>{f.title}</h3>
              <p className={styles.featureDesc}>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Security Section */}
      <section id="security" className={styles.security}>
        <div className={`card-glass ${styles.securityCard}`}>
          <div className={styles.securityIcon}>
            <Shield size={48} />
          </div>
          <div className={styles.securityContent}>
            <h2 className={styles.sectionTitle} style={{ textAlign: "left" }}>
              Zero-Knowledge Security
            </h2>
            <p className={styles.sectionSub} style={{ textAlign: "left" }}>
              G Telepathy uses a zero-knowledge architecture. Your encrypted messages are stored on our servers,
              but only <strong>you</strong> hold the decryption keys. We literally cannot read your messages.
            </p>
            <ul className={styles.securityList}>
              {[
                "AES-256 client-side encryption before transmission",
                "Signal Protocol for forward secrecy",
                "Optional QR code identity verification",
                "No metadata logging on our servers",
                "Open-source cryptography (libsodium)",
              ].map((item) => (
                <li key={item} className={styles.securityItem}>
                  <Star size={14} style={{ color: "var(--color-primary-dim)", flexShrink: 0 }} />
                  {item}
                </li>
              ))}
            </ul>
            <Link href="/register" className="btn btn-primary" style={{ marginTop: "24px" }}>
              Start Secure Communication
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className={styles.footer}>
        <div className={styles.footerLogo}>
          <div className={styles.logoIcon}>G</div>
          <span className={styles.logoText}>Telepathy</span>
        </div>
        <div className={styles.footerLinks}>
          <a href="#">Privacy Policy</a>
          <a href="#">Terms of Service</a>
          <a href="#">Security</a>
          <a href="https://github.com/voidx-hash/G-Telepathy" target="_blank" rel="noopener">GitHub</a>
        </div>
        <p className={styles.footerNote}>
          <Lock size={12} />
          All communications secured with AES-256 end-to-end encryption
        </p>
        <p className={styles.footerCopy}>© 2026 G Telepathy. MIT License.</p>
      </footer>
    </div>
  );
}
