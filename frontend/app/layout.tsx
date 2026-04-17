import React from "react"
import type { Metadata, Viewport } from "next";
import { Inter, Space_Mono } from "next/font/google";
import { Providers } from "@/components/providers";

import "./globals.css";

const _inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const _spaceMono = Space_Mono({
  subsets: ["latin"],
  weight: ["400", "700"],
  variable: "--font-space-mono",
});

export const metadata: Metadata = {
  title: "ClimaGuru - Dashboard Meteorologico",
  description:
    "Plataforma profesional de consultas climaticas con visualizacion de datos en tiempo real",
};

export const viewport: Viewport = {
  themeColor: "#1a6fd4",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" className="dark">
      <body className="font-sans antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
