import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'AI Synthetic Data & Edge-Case Platform',
  description: 'Create realistic, privacy-preserving synthetic datasets and rare edge cases.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-[#090d16] text-gray-100 antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
