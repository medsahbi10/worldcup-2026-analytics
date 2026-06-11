"use client";

/* Brand primitives reskinned from the WC2026 Figma boards.
 * Anything that points at a /brand asset degrades gracefully when the file
 * is absent (see public/brand/README.md). */
import Image from "next/image";
import Link from "next/link";
import { useState } from "react";

/* ---- 12-group neon palette (Groups A–L). { bg, ink } ---------------- */
/* ordered to match design/screen/groups.png */
export const GROUP_COLORS: Record<string, { bg: string; ink: string }> = {
  A: { bg: "#34c759", ink: "#04240f" },
  B: { bg: "#f43056", ink: "#fff" },
  C: { bg: "#ff9f0a", ink: "#231603" },
  D: { bg: "#0a84ff", ink: "#fff" },
  E: { bg: "#8b5cf6", ink: "#fff" },
  F: { bg: "#a3e635", ink: "#1a2102" },
  G: { bg: "#ec4899", ink: "#fff" },
  H: { bg: "#22d3ee", ink: "#04212b" },
  I: { bg: "#a855f7", ink: "#fff" },
  J: { bg: "#14b8a6", ink: "#03241f" },
  K: { bg: "#fb6340", ink: "#231603" },
  L: { bg: "#3b82f6", ink: "#fff" },
};
export const groupColor = (letter?: string | null) =>
  GROUP_COLORS[(letter ?? "").toUpperCase()] ?? { bg: "var(--color-surface2)", ink: "#fff" };

/* ---- asset image that falls back to children if it fails to load ---- */
function AssetImg({
  src, alt, width, height, className, fallback,
}: {
  src: string; alt: string; width: number; height: number; className?: string; fallback: React.ReactNode;
}) {
  const [failed, setFailed] = useState(false);
  if (failed) return <>{fallback}</>;
  return (
    <Image src={src} alt={alt} width={width} height={height} unoptimized className={className}
      onError={() => setFailed(true)} />
  );
}

/* ---- FIFA WORLD CUP 2026 lockup (image already carries the wordmark) - */
export function Logo() {
  const [failed, setFailed] = useState(false);
  if (failed) {
    return (
      <Link href="/" className="flex items-center gap-2.5">
        <span className="grid h-9 w-9 place-items-center rounded-lg bg-accent font-display text-xl font-extrabold leading-none text-[#08163a]">
          26
        </span>
        <span className="font-display text-lg font-extrabold tracking-wide">
          WORLD CUP <span className="text-accent">2026</span>
        </span>
      </Link>
    );
  }
  return (
    <Link href="/" className="flex items-center">
      <Image src="/brand/logo.png" alt="FIFA World Cup 2026" width={150} height={40} unoptimized
        className="h-9 w-auto" onError={() => setFailed(true)} />
    </Link>
  );
}

/* ---- circular trophy / 26 mark for hero & bracket centre ------------ */
export function TrophyMark({ size = 64 }: { size?: number }) {
  const fallback = (
    <span
      className="grid place-items-center rounded-full bg-gold font-display font-extrabold text-[#08163a]"
      style={{ width: size, height: size, fontSize: size * 0.42 }}
    >
      26
    </span>
  );
  return <AssetImg src="/brand/trophy.png" alt="FIFA World Cup trophy" width={size} height={size}
    className="object-contain" fallback={fallback} />;
}

/* ---- colored group badge ("A".."L") --------------------------------- */
export function GroupBadge({ letter, size = 24 }: { letter: string; size?: number }) {
  const c = groupColor(letter);
  return (
    <span
      className="grid place-items-center rounded-md font-display font-extrabold leading-none"
      style={{ width: size, height: size, background: c.bg, color: c.ink, fontSize: size * 0.55 }}
    >
      {letter.toUpperCase()}
    </span>
  );
}

/* ---- white rounded flag container (design/logo/flag container.png) --- *
 * White rounded-rect frame with the flag clipped to rounded corners;
 * radius + padding scale with size so it looks right from 16px to 64px. */
export function FlagCard({ src, alt, size = 26 }: { src: string; alt: string; size?: number }) {
  // Figma flag container: 144×96, border 2px #F7F7F8, radius 24px 0px
  // (top-left + bottom-right rounded, others square). Scaled by `size` = width.
  const w = size;
  const h = Math.round(size * (96 / 144));
  const r = Math.max(3, Math.round(size * (24 / 144)));
  const bw = Math.max(2, Math.round(size * (3 / 144)));
  const radius = `${r}px 0px ${r}px 0px`;
  // Map the flagcdn URL (".../w80/<iso>.png") to the bundled offline SVG so
  // flags never depend on a remote CDN; fall back to the given src otherwise.
  const m = src.match(/\/([a-z]{2}(?:-[a-z]{3})?)\.(?:png|svg)$/i);
  const flagSrc = m ? `/brand/flags/${m[1].toLowerCase()}.svg` : src;
  return (
    <span
      className="wc-flagcard"
      style={{ width: w, height: h, borderRadius: radius, border: `${bw}px solid #F7F7F8`, background: "#5A5B6F" }}
    >
      <Image src={flagSrc} alt={alt} width={w} height={h} unoptimized
        className="h-full w-full object-cover" />
    </span>
  );
}

/* ---- progression odds chips (Adv / R16 / QF …) ---------------------- */
export function StageChips({ stages }: { stages: { label: string; p: number | null | undefined }[] }) {
  return (
    <span className="flex shrink-0 gap-1">
      {stages.map((s) => (
        <span
          key={s.label}
          className="flex items-center gap-0.5 rounded bg-white/[0.07] px-1 py-0.5 text-[10px] font-bold leading-none"
          title={`${s.label}: ${s.p != null ? Math.round(s.p * 100) : 0}%`}
        >
          <span className="text-muted">{s.label}</span>
          <span className="text-accent">{s.p != null ? Math.round(s.p * 100) : 0}%</span>
        </span>
      ))}
    </span>
  );
}

/* ---- dark rounded score box ----------------------------------------- */
export function ScoreBox({ children }: { children: React.ReactNode }) {
  return <span className="wc-score">{children}</span>;
}

/* ---- team jersey shirt (falls back to a flag card) ------------------ */
export function Jersey({ iso, flag, alt, size = 92 }: {
  iso: string | null; flag: string; alt: string; size?: number;
}) {
  const fallback = <FlagCard src={flag} alt={alt} size={Math.round(size * 0.55)} />;
  if (!iso) return fallback;
  return (
    <AssetImg src={`/brand/jerseys/${iso.toLowerCase()}.png`} alt={`${alt} shirt`}
      width={size} height={size} className="h-auto w-full object-contain" fallback={fallback} />
  );
}
