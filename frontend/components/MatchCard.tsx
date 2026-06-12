"use client";

/* Match Card — built from the Figma spec (design/fonts/image.png).
 * Grey "Detail Row" (date · time • venue + group pill) over a dark "Match Row"
 * (NAME + flag · lime time/score box · flag + NAME). Sizes use clamp() so it
 * scales from mobile up to the 1417px design width. */
import { useState } from "react";
import { FlagCard, groupColor } from "@/components/brand";
import { MatchModal } from "@/components/MatchModal";
import { toTunisia } from "@/lib/tz";

export interface MatchCardProps {
  home: string;
  away: string;
  homeFlag: string;
  awayFlag: string;
  group?: string | null;
  matchDate: string;
  kickoff?: string | null;
  venue?: string | null;
  homeScore?: number | null;
  awayScore?: number | null;
  status?: string;
}

const fmt = (iso: string, opts: Intl.DateTimeFormatOptions) => {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? "" : d.toLocaleDateString("en-GB", opts);
};

const NAME = "truncate font-display font-black uppercase text-[#F7F7F8]";
const NAME_STYLE = { fontSize: "clamp(16px,2.1vw,30px)", lineHeight: 1 } as const;

export function MatchCard({
  home, away, homeFlag, awayFlag, group, matchDate, kickoff, venue, homeScore, awayScore, status,
}: MatchCardProps) {
  const [open, setOpen] = useState(false);
  const c = groupColor(group);
  const weekday = fmt(matchDate, { weekday: "long" });
  const dayMonth = fmt(matchDate, { day: "numeric", month: "long" });
  const tz = toTunisia(kickoff, venue);
  const time = tz ? tz.time : (kickoff ?? fmt(matchDate, { hour: "2-digit", minute: "2-digit" }));
  const timeLabel = time ? `${time} TN${tz?.nextDay ? " (+1)" : ""}` : "";
  const played = status === "played" && homeScore != null && awayScore != null;
  const center = played ? `${homeScore} - ${awayScore}` : (time || "VS");
  const venueShort = venue ? venue.split(" (")[0] : null;

  return (
    <>
    <div
      className="w-full cursor-pointer overflow-hidden transition-transform hover:-translate-y-0.5"
      style={{ borderRadius: 36 }}
      role="button"
      tabIndex={0}
      onClick={() => setOpen(true)}
      onKeyDown={(e) => { if (e.key === "Enter") setOpen(true); }}
    >
      {/* Detail Row */}
      <div
        className="flex items-center justify-between gap-4"
        style={{ background: "#3F404D", padding: "7px 14px 7px 24px" }}
      >
        <div
          className="flex min-w-0 items-center gap-3 font-display text-[#F7F7F8]"
          style={{ fontSize: "clamp(13px,1.4vw,22px)", lineHeight: 1.2 }}
        >
          <span className="truncate">
            {[weekday, dayMonth, timeLabel].filter(Boolean).join(" ")}
          </span>
          {venueShort && (
            <>
              <span className="inline-block shrink-0 rounded-full" style={{ width: 7, height: 7, background: "rgba(255,255,255,0.5)" }} />
              <span className="truncate">{venueShort}</span>
            </>
          )}
        </div>
        {group && (
          <div
            className="flex shrink-0 items-center justify-center rounded-full"
            style={{ background: c.bg, padding: "2px 14px", minHeight: 36 }}
          >
            <span className="font-display leading-none" style={{ color: c.ink, fontSize: "clamp(15px,1.8vw,28px)" }}>
              Group {group}
            </span>
          </div>
        )}
      </div>

      {/* Match Row */}
      <div className="flex items-center gap-2 sm:gap-4" style={{ background: "#151519", padding: "10px 18px" }}>
        <div className="flex min-w-0 flex-1 items-center justify-end gap-2 sm:gap-5">
          <span className={`text-right ${NAME}`} style={NAME_STYLE}>{home}</span>
          <span className="shrink-0"><FlagCard src={homeFlag} alt={home} size={52} /></span>
        </div>

        <div
          className="flex shrink-0 items-center justify-center font-display text-[#F7F7F8]"
          style={{
            border: `4px solid ${c.bg}`,
            borderRadius: 12,
            width: "clamp(88px,11vw,168px)",
            height: "clamp(44px,5vw,72px)",
            fontSize: "clamp(18px,2.1vw,30px)",
            lineHeight: 1,
          }}
        >
          {center}
        </div>

        <div className="flex min-w-0 flex-1 items-center gap-2 sm:gap-5">
          <span className="shrink-0"><FlagCard src={awayFlag} alt={away} size={52} /></span>
          <span className={NAME} style={NAME_STYLE}>{away}</span>
        </div>
      </div>
    </div>
    {open && (
      <MatchModal
        home={home} away={away} homeFlag={homeFlag} awayFlag={awayFlag}
        group={group} homeScore={homeScore} awayScore={awayScore} status={status}
        onClose={() => setOpen(false)}
      />
    )}
    </>
  );
}
