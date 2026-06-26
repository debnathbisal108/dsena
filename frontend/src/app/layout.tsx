import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
const inter = Inter({ subsets: ["latin"] });
export const metadata: Metadata = { title: "AI Sales Employee", description: "Your autonomous AI sales representative" };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body className={`${inter.className} bg-gray-50 text-gray-900 antialiased`}><Providers>{children}</Providers></body></html>;
}
