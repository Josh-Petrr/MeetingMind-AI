import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "MeetingMind AI | Command Center",
  description: "Enterprise Meeting Intelligence Platform",
};

import { Toaster } from "react-hot-toast";
import { GlobalPoller } from "@/components/GlobalPoller";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} antialiased flex h-screen overflow-hidden`}>
        {/* Sidebar */}
        <Sidebar />

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
        
        <Toaster position="top-right" />
        <GlobalPoller />
      </body>
    </html>
  );
}
