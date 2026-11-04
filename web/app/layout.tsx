import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LocalStock — find it nearby, live",
  description: "Search a product; nearby shops verify their stock in real time so you walk in with certainty.",
  manifest: "/manifest.json",
  appleWebApp: { capable: true, statusBarStyle: "default", title: "LocalStock" },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  viewportFit: "cover",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#F2F2F7" },
    { media: "(prefers-color-scheme: dark)",  color: "#000000" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="topbar">
          <a href="/" className="brand">
            <span style={{ fontSize: 20 }}>🛍️</span> LocalStock
          </a>
          <nav>
            <a href="/portal">Shop Portal</a>
          </nav>
        </header>
        <main className="container">{children}</main>
        <footer className="foot">
          <p>LocalStock — real-time local inventory for India</p>
          <p style={{ marginTop: 4 }}>
            Calls are mocked in dev · set <code>PROVIDER_TELEPHONY=exotel</code> for live outreach
          </p>
        </footer>
      </body>
    </html>
  );
}
