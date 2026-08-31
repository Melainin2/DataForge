import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DataForge — AI Voice Agent",
  description: "Real-time voice agent for the AssemblyAI Voice Agent Hackathon",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}