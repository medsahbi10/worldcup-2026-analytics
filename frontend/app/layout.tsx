import type { Metadata } from "next";
import { Oswald, Inter } from "next/font/google";
import "./globals.css";
import { Nav } from "@/components/Nav";

const display = Oswald({ subsets: ["latin"], weight: ["500", "600", "700"], variable: "--font-oswald" });
const body = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "World Cup 2026 — Analytics",
  description: "Squads, groups, schedule, market values and model forecasts for the FIFA World Cup 2026.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable} antialiased`}>
      <body className="min-h-screen">
        <Nav />
        <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
        <footer className="mx-auto max-w-6xl px-4 py-10 text-xs text-muted">
          Data: FBref · Transfermarkt · martj42 international results · flags by flagcdn.
          Model: Dixon-Coles + squad-value prior, 20k Monte-Carlo simulations.
        </footer>
      </body>
    </html>
  );
}
