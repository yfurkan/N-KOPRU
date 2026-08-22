import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "N-KÖPRÜ",
  description: "Yapay Zekâ Destekli Sosyal Tartışma Zekâsı Sistemi",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="tr">
      <body>{children}</body>
    </html>
  );
}
