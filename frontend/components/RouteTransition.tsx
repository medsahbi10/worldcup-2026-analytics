"use client";

/* "Logo passes by" route transition: on every navigation the World Cup trophy
 * sweeps across a royal-blue wipe. Triggered by pathname changes (re-keyed so
 * the CSS animation restarts each time). */
import Image from "next/image";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";

export function RouteTransition() {
  const pathname = usePathname();
  const [run, setRun] = useState(0);
  const mounted = useRef(false);

  useEffect(() => {
    if (!mounted.current) { mounted.current = true; return; } // skip first paint
    setRun((n) => n + 1);
  }, [pathname]);

  if (run === 0) return null;
  return (
    <div key={run} className="route-trans" aria-hidden>
      <span className="route-trans__wipe" />
      <Image
        src="/brand/trophy-pass.png"
        alt=""
        width={150}
        height={250}
        priority
        unoptimized
        className="route-trans__trophy"
      />
    </div>
  );
}
