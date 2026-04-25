import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "react-hot-toast";

export const metadata: Metadata = {
  title: "G Telepathy — Communicate Without Limits",
  description:
    "End-to-end encrypted real-time communication platform with AI Voice Cloning and live translation in 100+ languages.",
  keywords: ["encrypted chat", "voice cloning", "real-time translation", "secure calls"],
  authors: [{ name: "voidx-hash" }],
  themeColor: "#7c3aed",
  openGraph: {
    title: "G Telepathy",
    description: "Communicate Without Limits — E2E Encrypted · AI Voice Cloning · Real-Time Translation",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>
        {children}
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 3000,
            style: {
              background: "#2a292f",
              color: "#e4e1e9",
              border: "1px solid rgba(255,255,255,0.08)",
              fontFamily: "Inter, sans-serif",
            },
          }}
        />
      </body>
    </html>
  );
}
