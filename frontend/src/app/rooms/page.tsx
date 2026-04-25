"use client";
import { useState } from "react";
import Link from "next/link";
import { Search, Plus, Users, Globe2, Zap, MessageSquare, Phone } from "lucide-react";
import styles from "./rooms.module.css";

const ROOMS = [
  { id: "1", icon: "🌐", name: "Global Language Exchange", desc: "Practice any language with native speakers from around the world.", members: 1240, live: true, langs: ["🇺🇸", "🇯🇵", "🇪🇸", "🇮🇳"], category: "Language Exchange" },
  { id: "2", icon: "💻", name: "Tech Talk", desc: "Discuss software, AI, and the future of technology.", members: 892, live: true, langs: ["🇺🇸", "🇩🇪", "🇰🇷"], category: "Technology" },
  { id: "3", icon: "🎮", name: "Gaming Lounge", desc: "Find teammates, share strategies, and talk games.", members: 3200, live: true, langs: ["🇺🇸", "🇧🇷", "🇫🇷", "🇷🇺"], category: "Gaming" },
  { id: "4", icon: "🎨", name: "Creative Hub", desc: "Art, design, music, and everything creative.", members: 445, live: false, langs: ["🇺🇸", "🇮🇹", "🇯🇵"], category: "Art" },
  { id: "5", icon: "📈", name: "Business Network", desc: "Connect with entrepreneurs and professionals worldwide.", members: 678, live: true, langs: ["🇺🇸", "🇨🇳", "🇦🇪"], category: "Business" },
  { id: "6", icon: "🧬", name: "Science & Research", desc: "Discussions on science, research, and discovery.", members: 331, live: false, langs: ["🇺🇸", "🇩🇪", "🇷🇺"], category: "Science" },
];

const CATEGORIES = ["All", "Technology", "Gaming", "Language Exchange", "Business", "Art", "Science"];

const CONTACTS = [
  { id: "1", name: "Aiko Tanaka", username: "@aiko_t", bio: "Software Engineer · Tokyo", mutual: 3, online: true, avatar: "AT" },
  { id: "2", name: "Carlos Reyes", username: "@carlos_r", bio: "Designer · Barcelona", mutual: 7, online: true, avatar: "CR" },
  { id: "3", name: "Priya Sharma", username: "@priya_s", bio: "ML Researcher · Bangalore", mutual: 2, online: false, avatar: "PS" },
  { id: "4", name: "Lena Fischer", username: "@lena_f", bio: "Product Manager · Berlin", mutual: 5, online: false, avatar: "LF" },
];

const TABS = ["Global Rooms", "Contacts", "Discover People"];

export default function RoomsPage() {
  const [tab, setTab] = useState(0);
  const [category, setCategory] = useState("All");
  const [search, setSearch] = useState("");

  const filtered = ROOMS.filter((r) =>
    (category === "All" || r.category === category) &&
    r.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className={styles.page}>
      {/* Sidebar */}
      <aside className={styles.sidebar}>
        <Link href="/" className={styles.sidebarLogo}>
          <div className={styles.logoIcon}>G</div>
        </Link>
        {[
          { icon: <MessageSquare size={20} />, href: "/dashboard", label: "Chats" },
          { icon: <Phone size={20} />, href: "/calls", label: "Calls" },
          { icon: <Users size={20} />, href: "/contacts", label: "Contacts" },
          { icon: <Globe2 size={20} />, href: "/rooms", label: "Rooms", active: true },
        ].map((item) => (
          <Link key={item.label} href={item.href} className={`${styles.sidebarIcon} ${item.active ? styles.sidebarIconActive : ""}`} data-tooltip={item.label}>
            {item.icon}
          </Link>
        ))}
      </aside>

      <div className={styles.content}>
        {/* Header */}
        <div className={styles.header}>
          <div>
            <h1 className={styles.title}>Explore</h1>
            <p className={styles.sub}>Discover rooms and people from around the world</p>
          </div>
          <div className={styles.headerRight}>
            <div className={styles.tz}><Globe2 size={13} /> IST · 8:34 AM</div>
            <button className="btn btn-primary btn-sm"><Plus size={15} /> Create Room</button>
          </div>
        </div>

        {/* Tabs */}
        <div className={styles.tabs}>
          {TABS.map((t, i) => (
            <button
              key={t}
              className={`${styles.tab} ${tab === i ? styles.tabActive : ""}`}
              onClick={() => setTab(i)}
            >{t}</button>
          ))}
        </div>

        {tab === 0 && (
          <>
            {/* Filters */}
            <div className={styles.filters}>
              <div className={styles.searchWrap}>
                <Search size={15} className={styles.searchIcon} />
                <input className={`input ${styles.searchInput}`} placeholder="Search rooms..." value={search} onChange={(e) => setSearch(e.target.value)} />
              </div>
              <div className={styles.categoryChips}>
                {CATEGORIES.map((c) => (
                  <button
                    key={c}
                    className={`${styles.chip} ${category === c ? styles.chipActive : ""}`}
                    onClick={() => setCategory(c)}
                  >{c}</button>
                ))}
              </div>
            </div>

            {/* Rooms Grid */}
            <div className={styles.grid}>
              {filtered.map((room) => (
                <div key={room.id} className={`card ${styles.roomCard}`}>
                  <div className={styles.roomHeader}>
                    <span className={styles.roomIcon}>{room.icon}</span>
                    {room.live
                      ? <span className={`badge badge-success ${styles.liveBadge}`}><Zap size={10} /> Live</span>
                      : <span className={`badge ${styles.scheduledBadge}`}>Scheduled</span>
                    }
                  </div>
                  <h3 className={styles.roomName}>{room.name}</h3>
                  <p className={styles.roomDesc}>{room.desc}</p>
                  <div className={styles.roomMeta}>
                    <div className={styles.roomLangs}>{room.langs.map((l, i) => <span key={i}>{l}</span>)}</div>
                    <div className={styles.roomMembers}>
                      <Users size={13} />
                      {room.members.toLocaleString()}
                    </div>
                  </div>
                  <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center" }}>Join Room</button>
                </div>
              ))}
            </div>
          </>
        )}

        {tab === 1 && (
          <div className={styles.contactsGrid}>
            {CONTACTS.map((c) => (
              <div key={c.id} className={`card ${styles.contactCard}`}>
                <div className={styles.contactTop}>
                  <div className={styles.contactAvatarWrap}>
                    <div className={`${styles.contactAvatar} ${c.online ? styles.contactAvatarOnline : ""}`}>{c.avatar}</div>
                    <div className={`status-dot ${c.online ? "status-online" : "status-offline"} ${styles.contactDot}`} />
                  </div>
                  <div className={styles.contactInfo}>
                    <span className={styles.contactName}>{c.name}</span>
                    <span className={styles.contactUsername}>{c.username}</span>
                    <span className={styles.contactBio}>{c.bio}</span>
                    <span className={styles.mutualCount}>{c.mutual} mutual connections</span>
                  </div>
                </div>
                <div className={styles.contactActions}>
                  <button className="btn btn-ghost btn-sm"><MessageSquare size={14} /> Message</button>
                  <button className="btn btn-ghost btn-sm"><Phone size={14} /> Call</button>
                </div>
              </div>
            ))}
          </div>
        )}

        {tab === 2 && (
          <div className={styles.discover}>
            <Search size={48} style={{ color: "var(--color-text-faint)" }} />
            <h3 style={{ color: "var(--color-text-muted)" }}>Search for people to connect with</h3>
            <div style={{ width: "100%", maxWidth: 400 }}>
              <input className="input" placeholder="Search by name or username..." />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
