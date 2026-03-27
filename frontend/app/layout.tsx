import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TubeInsight AI",
  description: "AI-powered YouTube Creator Intelligence Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background text-foreground">
        {children}
      </body>
    </html>
  );
}
