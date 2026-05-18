import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SIDIX — Creative AI Agent",
  description:
    "Self-hosted, free, open-source Creative AI Agent. Tumbuh setiap hari, bukan chatbot biasa.",
  applicationName: "SIDIX",
  authors: [{ name: "Mighan Lab / Tiranyx" }],
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="id" className="font-grotesk">
      <body className="bg-sidix-darker text-white antialiased">{children}</body>
    </html>
  );
}
