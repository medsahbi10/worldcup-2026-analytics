"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  ["/", "Overview"],
  ["/predictions", "Predictions"],
  ["/groups", "Groups"],
  ["/schedule", "Schedule"],
  ["/teams", "Teams"],
  ["/players", "Players"],
  ["/lineups", "Lineups"],
];

export function Nav() {
  const path = usePathname();
  return (
    <header className="sticky top-0 z-20 border-b border-border bg-bg/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center gap-6 px-4 py-3">
        <Link href="/" className="flex items-center gap-2">
          <span className="grid h-8 w-8 place-items-center rounded-md bg-primary font-display text-lg font-bold text-white">
            26
          </span>
          <span className="font-display text-lg font-bold tracking-wide">
            WORLD CUP <span className="text-accent">2026</span>
          </span>
        </Link>
        <nav className="flex flex-wrap gap-1 text-sm">
          {LINKS.map(([href, label]) => {
            const active = path === href;
            return (
              <Link
                key={href}
                href={href}
                className={`rounded-md px-3 py-1.5 font-display uppercase tracking-wide transition-colors ${
                  active ? "bg-primary text-white" : "text-muted hover:bg-surface2 hover:text-text"
                }`}
              >
                {label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
