import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

// Version should match package.json and PRD
const APP_VERSION = '1.5.0';

export const metadata: Metadata = {
  title: `WSOPTV v${APP_VERSION}`,
  description: 'Private Poker VOD Streaming Platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
