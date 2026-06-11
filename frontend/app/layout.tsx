import type { Metadata } from "next";
import { Noto_Sans, Archivo } from "next/font/google";
import "./globals.css";
import { Nav } from "@/components/Nav";
import { RouteTransition } from "@/components/RouteTransition";

// Body = Noto Sans (the Figma body font).
const body = Noto_Sans({ subsets: ["latin"], variable: "--font-noto" });
// Fallback display face for FWC2026 until brand/fwc2026.woff2 is dropped in.
const display = Archivo({ subsets: ["latin"], weight: ["600", "700", "800", "900"], variable: "--font-archivo" });

export const metadata: Metadata = {
  title: "FIFA World Cup 2026 — Analytics",
  description: "Squads, groups, schedule, the knockout bracket, market values and model forecasts for the FIFA World Cup 2026.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable} antialiased`}>
      <body className="min-h-screen">
        <RouteTransition />
        <Nav />
        <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
        <footer className="mt-10 border-t border-border">
          <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-8 text-xs text-muted sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="font-display text-sm font-extrabold text-text">FIFA WORLD CUP 2026 · ANALYTICS</div>
              <div className="mt-1">48 teams · 104 matches · USA · Mexico · Canada</div>
            </div>
            <div className="sm:text-right">
              Data: FBref · Transfermarkt · martj42 · flags by flag-icons.<br />
              Model: Dixon-Coles + squad-value prior · 20k Monte-Carlo sims.
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
