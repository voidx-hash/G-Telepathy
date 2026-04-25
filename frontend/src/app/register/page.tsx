"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Lock, Mail, Eye, EyeOff, User, Shield } from "lucide-react";
import toast from "react-hot-toast";
import styles from "./auth.module.css";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [show, setShow] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    // TODO: connect to Supabase auth
    await new Promise((r) => setTimeout(r, 1200));
    toast.success("Account created! Welcome to G Telepathy.");
    router.push("/dashboard");
    setLoading(false);
  };

  return (
    <div className={styles.page}>
      <div className={styles.bgGlow} aria-hidden />
      <div className={styles.bgGrid} aria-hidden />

      {/* Logo */}
      <Link href="/" className={styles.logo}>
        <div className={styles.logoIcon}>G</div>
        <span className={styles.logoText}>Telepathy</span>
      </Link>

      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <h1 className={styles.cardTitle}>Create Account</h1>
          <p className={styles.cardSub}>Join the most secure communication platform</p>
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.field}>
            <label className={styles.label}>Full Name</label>
            <div className={styles.inputWrap}>
              <User size={16} className={styles.inputIcon} />
              <input
                className={`input ${styles.inputPadded}`}
                type="text"
                placeholder="Your name"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
              />
            </div>
          </div>

          <div className={styles.field}>
            <label className={styles.label}>Email Address</label>
            <div className={styles.inputWrap}>
              <Mail size={16} className={styles.inputIcon} />
              <input
                className={`input ${styles.inputPadded}`}
                type="email"
                placeholder="you@example.com"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                required
              />
            </div>
          </div>

          <div className={styles.field}>
            <label className={styles.label}>Password</label>
            <div className={styles.inputWrap}>
              <Lock size={16} className={styles.inputIcon} />
              <input
                className={`input ${styles.inputPadded} ${styles.inputRight}`}
                type={show ? "text" : "password"}
                placeholder="Min. 8 characters"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                minLength={8}
                required
              />
              <button
                type="button"
                className={styles.eyeBtn}
                onClick={() => setShow(!show)}
                aria-label="Toggle password"
              >
                {show ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <button type="submit" className={`btn btn-primary ${styles.submitBtn}`} disabled={loading}>
            {loading ? <span className={styles.spinner} /> : <Lock size={16} />}
            {loading ? "Creating Account..." : "Create Account"}
          </button>
        </form>

        <div className={styles.divider}><span>or</span></div>

        <button className={`btn btn-ghost ${styles.googleBtn}`}>
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z" fill="#4285F4"/>
            <path d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.258c-.806.54-1.837.859-3.048.859-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 009 18z" fill="#34A853"/>
            <path d="M3.964 10.706A5.41 5.41 0 013.682 9c0-.593.102-1.17.282-1.706V4.962H.957A8.996 8.996 0 000 9c0 1.452.348 2.827.957 4.038l3.007-2.332z" fill="#FBBC05"/>
            <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 00.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/>
          </svg>
          Continue with Google
        </button>

        <p className={styles.switchLink}>
          Already have an account?{" "}
          <Link href="/login" className={styles.link}>Sign in</Link>
        </p>

        <div className={styles.encNote}>
          <Shield size={12} />
          All communications secured with AES-256 end-to-end encryption
        </div>
      </div>
    </div>
  );
}
