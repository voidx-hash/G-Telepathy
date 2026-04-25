"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Mic, MicOff, Video, VideoOff, PhoneOff,
  Monitor, ScreenShare, Hand, MessageSquare,
  Users, Globe2, Mic2, ChevronDown, Play, Trash2,
  Lock, Timer,
} from "lucide-react";
import styles from "./call.module.css";

const PARTICIPANTS = [
  { id: "1", name: "Aiko Tanaka", avatar: "AT", speaking: true },
  { id: "2", name: "Carlos Reyes", avatar: "CR", speaking: false },
  { id: "3", name: "Priya Sharma", avatar: "PS", speaking: false },
];

const SUBTITLES = [
  { speaker: "Aiko", text: "I think we should finalize the encryption layer first." },
  { speaker: "Aiko", text: "What do you all think about the translation feature?", translated: true },
];

const VOICE_PRESETS = ["Aria", "Nova", "Echo", "Onyx", "Shimmer", "Fable"];
const LANGUAGES = ["English", "Japanese", "Spanish", "Hindi", "German", "French", "Chinese", "Arabic", "Portuguese"];

export default function CallPage() {
  const router = useRouter();
  const [muted, setMuted] = useState(false);
  const [camOff, setCamOff] = useState(false);
  const [showTranslation, setShowTranslation] = useState(true);
  const [showVoiceClone, setShowVoiceClone] = useState(true);
  const [selectedVoice, setSelectedVoice] = useState("Your Voice (Original)");
  const [targetLang, setTargetLang] = useState("English");

  return (
    <div className={styles.page}>
      {/* BG */}
      <div className={styles.bgBlur} />

      {/* Top Bar */}
      <div className={styles.topBar}>
        <div className={styles.topLeft}>
          <div className={styles.logoMini}>G</div>
          <div className={styles.timer}><Timer size={14} /> 00:14:32</div>
          <div className={`badge badge-success ${styles.encBadge}`}>
            <Lock size={10} /> AES-256 Encrypted
          </div>
        </div>
        <div className={styles.topRight}>
          <div className={`badge badge-primary`}>
            <Users size={10} /> {PARTICIPANTS.length} Participants
          </div>
        </div>
      </div>

      {/* Main Layout */}
      <div className={styles.main}>
        {/* Left: Translation Panel */}
        {showTranslation && (
          <div className={`card-glass ${styles.sidePanel}`}>
            <div className={styles.sidePanelHeader}>
              <Globe2 size={16} style={{ color: "var(--color-secondary)" }} />
              <span className={styles.sidePanelTitle}>Live Translation</span>
              <div className={styles.googleBadge}>Google Translate</div>
              <button className={styles.closePanel} onClick={() => setShowTranslation(false)}>✕</button>
            </div>
            <div className={styles.langRow}>
              <span className={styles.langLabel}>Translate to</span>
              <select
                className={styles.langSelect}
                value={targetLang}
                onChange={(e) => setTargetLang(e.target.value)}
              >
                {LANGUAGES.map((l) => <option key={l}>{l}</option>)}
              </select>
            </div>
            <div className={styles.subtitles}>
              {SUBTITLES.map((s, i) => (
                <div key={i} className={styles.subtitle}>
                  <span className={styles.subtitleSpeaker}>{s.speaker}:</span>
                  <span className={`${styles.subtitleText} ${s.translated ? styles.subtitleTranslated : ""}`}>
                    {s.text}
                  </span>
                  {s.translated && (
                    <span className={styles.translatedBadge}>
                      <Globe2 size={10} /> translated
                    </span>
                  )}
                </div>
              ))}
              <div className={styles.subtitleLive}>
                <span className={styles.subtitleSpeaker}>Carlos:</span>
                <span className={styles.cursor}>▊</span>
              </div>
            </div>
          </div>
        )}

        {/* Center: Video Feed */}
        <div className={styles.videoArea}>
          {/* Main Speaker */}
          <div className={styles.mainVideo}>
            <div className={styles.videoPlaceholder}>
              <div className={styles.videoAvatar}>{PARTICIPANTS[0].avatar}</div>
              <div className={styles.waveformWrap}>
                <div className="waveform">
                  {Array.from({ length: 7 }).map((_, i) => (
                    <div key={i} className="waveform-bar" />
                  ))}
                </div>
              </div>
            </div>
            <div className={styles.videoLabel}>
              <span>{PARTICIPANTS[0].name}</span>
              <span className={styles.speakingLabel}>Speaking...</span>
            </div>
          </div>

          {/* Gallery Strip */}
          <div className={styles.gallery}>
            {PARTICIPANTS.slice(1).map((p) => (
              <div key={p.id} className={styles.galleryTile}>
                <div className={styles.galleryAvatar}>{p.avatar}</div>
                <span className={styles.galleryName}>{p.name}</span>
              </div>
            ))}
            <div className={styles.galleryTile}>
              <div className={`${styles.galleryAvatar} ${styles.you}`}>You</div>
              <span className={styles.galleryName}>You</span>
            </div>
          </div>
        </div>

        {/* Right: Voice Clone Panel */}
        {showVoiceClone && (
          <div className={`card-glass ${styles.sidePanel}`}>
            <div className={styles.sidePanelHeader}>
              <Mic2 size={16} style={{ color: "var(--color-primary-dim)" }} />
              <span className={styles.sidePanelTitle}>Voice Cloning</span>
              <button className={styles.closePanel} onClick={() => setShowVoiceClone(false)}>✕</button>
            </div>
            <div className={styles.currentVoice}>
              <span className={styles.langLabel}>Current Voice</span>
              <select className={styles.langSelect} value={selectedVoice} onChange={(e) => setSelectedVoice(e.target.value)}>
                <option>Your Voice (Original)</option>
                {VOICE_PRESETS.map((v) => <option key={v}>{v}</option>)}
              </select>
            </div>
            <div className={styles.voicePresets}>
              <span className={styles.langLabel}>AI Voice Presets</span>
              <div className={styles.presetGrid}>
                {VOICE_PRESETS.map((v) => (
                  <button
                    key={v}
                    className={`${styles.presetChip} ${selectedVoice === v ? styles.presetChipActive : ""}`}
                    onClick={() => setSelectedVoice(v)}
                  >
                    {v}
                  </button>
                ))}
              </div>
            </div>
            <button className={`btn btn-primary ${styles.cloneBtn}`}>
              <Mic2 size={15} /> Clone Your Voice
            </button>
            <p className={styles.cloneHint}>Record 30s of your voice to create a perfect AI clone</p>
            <div className={styles.sliders}>
              <div className={styles.slider}>
                <span className={styles.langLabel}>Pitch</span>
                <input type="range" min={-12} max={12} defaultValue={0} className={styles.sliderInput} />
              </div>
              <div className={styles.slider}>
                <span className={styles.langLabel}>Speed</span>
                <input type="range" min={50} max={200} defaultValue={100} className={styles.sliderInput} />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Control Bar */}
      <div className={`card-glass ${styles.controls}`}>
        <button
          className={`btn btn-icon ${muted ? "btn-danger" : "btn-ghost"}`}
          onClick={() => setMuted(!muted)}
          data-tooltip={muted ? "Unmute" : "Mute"}
        >
          {muted ? <MicOff size={20} /> : <Mic size={20} />}
        </button>
        <button
          className={`btn btn-icon ${camOff ? "btn-danger" : "btn-ghost"}`}
          onClick={() => setCamOff(!camOff)}
          data-tooltip={camOff ? "Start Camera" : "Stop Camera"}
        >
          {camOff ? <VideoOff size={20} /> : <Video size={20} />}
        </button>
        <button className="btn btn-icon btn-ghost" data-tooltip="Share Screen"><ScreenShare size={20} /></button>
        <button className="btn btn-icon btn-ghost" data-tooltip="Raise Hand"><Hand size={20} /></button>
        <button className="btn btn-icon btn-ghost" data-tooltip="Chat"><MessageSquare size={20} /></button>
        <button
          className={`btn btn-icon btn-ghost ${showTranslation ? styles.controlActive : ""}`}
          onClick={() => setShowTranslation(!showTranslation)}
          data-tooltip="Translation"
        >
          <Globe2 size={20} />
        </button>
        <button
          className={`btn btn-icon btn-ghost ${showVoiceClone ? styles.controlActive : ""}`}
          onClick={() => setShowVoiceClone(!showVoiceClone)}
          data-tooltip="Voice Clone"
        >
          <Mic2 size={20} />
        </button>
        <div className={styles.controlSep} />
        <button className="btn btn-danger" onClick={() => router.push("/dashboard")}>
          <PhoneOff size={18} /> End Call
        </button>
      </div>
    </div>
  );
}
