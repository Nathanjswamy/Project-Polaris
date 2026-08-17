import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Project Polaris — Competitive Intelligence & Analytics",
  description: "Data-centric competitive intelligence platform for business analytics, competitor analysis, and market forecasting. Built as an end-to-end analytics system.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
