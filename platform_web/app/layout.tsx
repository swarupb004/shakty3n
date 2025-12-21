import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Shakty3n Platform",
  description: "AI-powered autonomous coding platform",
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
