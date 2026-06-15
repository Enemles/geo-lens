import type { Metadata } from "next";
import { DM_Sans, Space_Grotesk } from "next/font/google";

import "./globals.css";

const display = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["500", "700"],
});

const sans = DM_Sans({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: "GEO Lens — AI brand visibility",
  description:
    "Measure how visible a brand is to AI assistants (Generative Engine Optimization).",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${sans.variable} ${display.variable} antialiased`}>
        {children}
      </body>
    </html>
  );
}
