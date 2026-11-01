import "./globals.css";
import type { Metadata } from "next";
export const metadata: Metadata = { title: "ContentSignal — AI Video Studio", description: "Create videos from text, images and existing footage." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="ar" dir="rtl"><body>{children}</body></html>; }
