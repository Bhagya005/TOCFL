import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TOCFL A1 Study",
  description: "TOCFL A1 vocabulary study app",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="overflow-x-hidden">
      <body className="overflow-x-hidden">{children}</body>
    </html>
  );
}
