# 🌐 G Telepathy

> **Communicate Without Limits** — A next-generation, end-to-end encrypted real-time communication platform with AI Voice Cloning and live multilingual translation.

[![License: MIT](https://img.shields.io/badge/License-MIT-violet.svg)](https://opensource.org/licenses/MIT)
[![Built with: Next.js](https://img.shields.io/badge/Frontend-Next.js%2014-black)](https://nextjs.org/)
[![Backend: FastAPI](https://img.shields.io/badge/Backend-FastAPI-green)](https://fastapi.tiangolo.com/)
[![Translation: Google Cloud](https://img.shields.io/badge/Translation-Google%20Cloud%20Translate-blue)](https://cloud.google.com/translate)
[![Encryption: AES-256](https://img.shields.io/badge/Encryption-AES--256%20E2E-red)](https://en.wikipedia.org/wiki/Advanced_Encryption_Standard)

---

## ✨ Core Features

| Feature | Description |
|---|---|
| 🔒 **E2E Encrypted Chat** | All messages secured with AES-256 end-to-end encryption |
| 📞 **Encrypted Voice & Video Calls** | WebRTC-based calls with full E2E encryption |
| 🎙️ **AI Voice Cloning** | Clone any voice from 30s of audio; apply in real-time calls |
| 🌐 **Real-Time Translation** | Live message & call translation via Google Cloud Translate API (100+ languages) |
| 🗣️ **Voice Modulation** | Real-time pitch, speed, and timbre control during calls |
| 🌍 **Global Rooms** | Join topic-based public rooms with people across the world |
| 📖 **Live Transcription** | Real-time speech-to-text during calls with speaker labels |
| 🔑 **2FA Authentication** | TOTP-based two-factor authentication |
| 🌙 **Neon Void Dark UI** | Hyper-modern glassmorphism dark-mode interface |

---

## 🎨 Design System

**Theme**: Neon Void / Synthetic Ether  
**Colors**: Vivid Violet `#7C3AED` × Electric Cyan `#06B6D4` × Deep Space `#131318`  
**Font**: Inter  
**Style**: Glassmorphism panels, neon glow shadows, gradient CTAs  
**UI Designs**: Created with [Google Stitch](https://stitch.google.com/projects/15260782561300495248)

---

## 🏗️ Tech Stack

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS + Custom CSS (Neon Void Design System)
- **Real-time**: Socket.io Client
- **Calls**: WebRTC (via simple-peer)
- **State**: Zustand

### Backend
- **API**: FastAPI (Python)
- **Real-time**: Socket.io (python-socketio)
- **Auth**: Supabase Auth + JWT
- **Database**: Supabase (PostgreSQL)
- **File Storage**: Supabase Storage

### AI & Services
- **Translation**: Google Cloud Translate API v3
- **Speech-to-Text**: Google Cloud Speech-to-Text (for live transcription)
- **Voice Cloning**: ElevenLabs API / open-source XTTS model
- **Encryption**: libsodium / Signal Protocol (E2E)

---

## 📁 Project Structure

```
G-Telepathy/
├── frontend/                   # Next.js 14 App
│   ├── app/
│   │   ├── (auth)/             # Login, Register pages
│   │   ├── dashboard/          # Main chat dashboard
│   │   ├── call/               # Call interface
│   │   ├── rooms/              # Global rooms discovery
│   │   └── settings/           # User settings
│   ├── components/             # Reusable UI components
│   ├── lib/                    # Utilities & API clients
│   └── styles/                 # Global CSS & design tokens
│
├── backend/                    # FastAPI Python Backend
│   ├── routers/                # API route handlers
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── calls.py
│   │   ├── rooms.py
│   │   └── translate.py
│   ├── services/               # Business logic
│   │   ├── translation.py      # Google Translate integration
│   │   ├── voice_clone.py      # Voice cloning service
│   │   ├── encryption.py       # E2E encryption helpers
│   │   └── transcription.py    # Speech-to-text service
│   ├── sockets/                # Socket.io event handlers
│   │   ├── chat.py
│   │   └── calls.py
│   ├── models/                 # Pydantic models
│   ├── config.py               # Environment configuration
│   ├── main.py                 # FastAPI app entry point
│   └── requirements.txt
│
├── supabase/
│   ├── schema.sql              # Database schema
│   └── migrations/             # DB migration files
│
├── .env.example                # Environment variables template
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- Python 3.11+
- Supabase account
- Google Cloud project with Translate API enabled

### 1. Clone the repository
```bash
git clone https://github.com/voidx-hash/G-Telepathy.git
cd G-Telepathy
```

### 2. Set up environment variables
```bash
cp .env.example .env
# Fill in your API keys in .env
```

### 3. Start the backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 4. Start the frontend
```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:3000`.

---

## 🔐 Security

- All messages and calls encrypted with **AES-256** before leaving the device
- Encryption keys are **never sent to the server** — only encrypted payloads
- **Zero-knowledge architecture**: G Telepathy servers cannot read your messages
- Optional **identity verification** via QR code key exchange

---

## 🌍 Translation

G Telepathy uses the **Google Cloud Translate API** to provide:
- Auto-detect source language
- Translate incoming messages to your preferred language instantly
- Real-time call transcription with live translation overlay
- Support for **100+ languages**

---

## 📄 License

MIT License © 2026 [voidx-hash](https://github.com/voidx-hash)
