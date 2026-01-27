import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Antariks Clipper",
  description: "Auto-generate viral highlight clips for Reels & TikTok",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
