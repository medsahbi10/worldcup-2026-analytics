import { PageTitle } from "@/components/ui";
import { ScoreBox, TrophyMark } from "@/components/brand";

/* Official FIFA 2026 knockout template — mirrors src/wc2026/models/simulate.py.
 * A slot is a fixed group position ("1A"/"2B") or a best-third slot
 * (["T", matchNo]); later rounds feed from prior match winners. Until the group
 * stage resolves we show the slot codes (exactly like the printed bracket). */
type Slot = string | ["T", number];

const R32: [number, Slot, Slot][] = [
  [73, "2A", "2B"], [74, "1E", ["T", 74]], [75, "1F", "2C"], [76, "1C", "2F"],
  [77, "1I", ["T", 77]], [78, "2E", "2I"], [79, "1A", ["T", 79]], [80, "1L", ["T", 80]],
  [81, "1D", ["T", 81]], [82, "1G", ["T", 82]], [83, "2K", "2L"], [84, "1H", "2J"],
  [85, "1B", ["T", 85]], [86, "1J", "2H"], [87, "1K", ["T", 87]], [88, "2D", "2G"],
];
const THIRD_ALLOWED: Record<number, string> = {
  74: "ABCDF", 77: "CDFGH", 79: "CEFHI", 80: "EHIJK",
  81: "BEFIJ", 82: "AEHIJ", 85: "EFGIJ", 87: "DEIJL",
};
const R16: [number, number, number][] = [
  [89, 74, 77], [90, 73, 75], [91, 76, 78], [92, 79, 80],
  [93, 83, 84], [94, 81, 82], [95, 86, 88], [96, 85, 87],
];
const QF: [number, number, number][] = [[97, 89, 90], [98, 93, 94], [99, 91, 92], [100, 95, 96]];
const SF: [number, number, number][] = [[101, 97, 98], [102, 99, 100]];
const FINAL: [number, number, number] = [104, 101, 102];

const slotLabel = (s: Slot): string =>
  Array.isArray(s) ? `3rd · ${THIRD_ALLOWED[s[1]].split("").join("/")}` : s;

function Match({ no, a, b, gold = false }: { no: number; a: string; b: string; gold?: boolean }) {
  return (
    <div className={`rounded-lg border bg-[#06122e]/80 ${gold ? "border-gold shadow-[0_0_0_2px_var(--color-gold)]" : "border-white/15"}`}>
      <div className="px-2 pt-1 text-[9px] uppercase tracking-wide text-white/40">Match {no}</div>
      {[a, b].map((label, i) => (
        <div key={i} className={`flex items-center gap-2 px-2 py-1.5 ${i === 0 ? "border-b border-white/10" : ""}`}>
          <span className="flex-1 truncate font-display text-xs font-bold">{label}</span>
          <ScoreBox>–</ScoreBox>
        </div>
      ))}
    </div>
  );
}

function Column({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="flex min-w-[150px] flex-1 flex-col">
      <div className="mb-2 text-center font-display text-xs font-bold uppercase text-white/60">{title}</div>
      <div className="flex flex-1 flex-col justify-around gap-2">{children}</div>
    </div>
  );
}

export default function BracketPage() {
  const feeder = (n: number) => `Winner M${n}`;
  return (
    <div>
      <PageTitle title="Knockout Bracket" sub="The official 2026 round-of-32 slot template · results fill in once the group stage ends." />
      <div className="wc-board overflow-x-auto border border-border p-4">
        <div className="flex min-w-[1100px] gap-3">
          <Column title="Round of 32">
            {R32.map(([no, a, b]) => <Match key={no} no={no} a={slotLabel(a)} b={slotLabel(b)} />)}
          </Column>
          <Column title="Round of 16">
            {R16.map(([no, a, b]) => <Match key={no} no={no} a={feeder(a)} b={feeder(b)} />)}
          </Column>
          <Column title="Quarter-finals">
            {QF.map(([no, a, b]) => <Match key={no} no={no} a={feeder(a)} b={feeder(b)} />)}
          </Column>
          <Column title="Semi-finals">
            {SF.map(([no, a, b]) => <Match key={no} no={no} a={feeder(a)} b={feeder(b)} />)}
          </Column>
          <Column title="Final">
            <div className="flex flex-col items-center gap-4">
              <TrophyMark size={72} />
              <div className="w-full">
                <Match no={FINAL[0]} a={feeder(FINAL[1])} b={feeder(FINAL[2])} gold />
              </div>
            </div>
          </Column>
        </div>
      </div>
      <p className="mt-4 text-xs text-muted">
        Round-of-32 ties follow FIFA&apos;s fixed-slot template (matches 73–88); the eight best
        third-placed teams fill the marked &ldquo;3rd&rdquo; slots under the official group-combination rules.
      </p>
    </div>
  );
}
