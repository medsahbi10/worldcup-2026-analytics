"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Logo } from "@/components/brand";

const LINKS = [
  ["/", "Overview"],
  ["/groups", "Groups"],
  ["/bracket", "Bracket"],
  ["/schedule", "Schedule"],
  ["/ranking", "Ranking"],
  ["/teams", "Teams"],
  ["/players", "Players"],
];

export function Nav() {
  const path = usePathname();
  return (
    <header className="sticky top-0 z-20 border-b border-border bg-bg/85 backdrop-blur">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
        <Logo />
        <nav className="flex flex-wrap gap-1 text-sm">
          {LINKS.map(([href, label]) => {
            const active = path === href;
            return (
              <Link
                key={href}
                href={href}
                className={`rounded-md px-3 py-1.5 font-display font-bold uppercase tracking-wide transition-colors ${
                  active ? "bg-accent text-[#08163a]" : "text-muted hover:bg-surface2 hover:text-text"
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
