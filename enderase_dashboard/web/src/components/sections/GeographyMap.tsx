import { useState } from "react";
import { motion } from "framer-motion";
import { useRegistryData } from "@/hooks/use-registry-data";
import { SectionHeading } from "./Pipeline";
import { MapPin } from "lucide-react";

export function GeographyMap() {
  const { regions } = useRegistryData();
  // Track the hovered region by id so the detail card picks up fresh
  // numbers when live registry data arrives mid-session.
  const [hoverId, setHoverId] = useState(regions[4].id);
  const hover = regions.find((r) => r.id === hoverId) ?? regions[0];
  const max = Math.max(...regions.map((r) => r.youth));

  return (
    <section>
      <SectionHeading eyebrow="Geography" title="Across Ethiopia"
        note="Registered youth density by region. Hover a node for details." />
      <div className="mt-8 grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <div className="relative aspect-[4/3] overflow-hidden rounded-[2rem] bg-gradient-cream p-4 shadow-block ring-1 ring-border">
          <div className="pointer-events-none absolute inset-0 bg-gradient-sun opacity-[0.06]" />
          <svg viewBox="0 0 100 90" className="h-full w-full">
            {/* connective mesh */}
            {regions.map((r, i) =>
              regions.slice(i + 1).map((o) => {
                const d = Math.hypot(r.x - o.x, r.y - o.y);
                if (d > 26) return null;
                return <line key={r.id + o.id} x1={r.x} y1={r.y} x2={o.x} y2={o.y} stroke="hsl(30 45% 34% / 0.15)" strokeWidth={0.3} />;
              })
            )}
            {regions.map((r) => {
              const t = r.youth / max;
              const rad = 2.2 + t * 5;
              const isHover = hover?.id === r.id;
              return (
                <g key={r.id} onMouseEnter={() => setHoverId(r.id)} className="cursor-pointer">
                  {isHover && <circle cx={r.x} cy={r.y} r={rad + 3} fill="hsl(44 92% 52% / 0.25)" className="animate-pulse-ring" />}
                  <motion.circle
                    cx={r.x} cy={r.y}
                    initial={{ r: 0 }} whileInView={{ r: rad }} viewport={{ once: true }}
                    transition={{ type: "spring", stiffness: 120, damping: 12 }}
                    fill={isHover ? "hsl(44 92% 52%)" : `hsl(30 45% ${44 - t * 22}%)`}
                    stroke="hsl(40 43% 96%)" strokeWidth={0.5}
                  />
                </g>
              );
            })}
          </svg>
        </div>

        <div className="flex flex-col justify-between gap-4">
          <motion.div
            key={hover?.id}
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
            className="rounded-[2rem] bg-gradient-brown p-7 text-cream shadow-soft"
          >
            <span className="inline-flex items-center gap-2 text-sm text-gold"><MapPin className="h-4 w-4" /> Region</span>
            <h3 className="mt-1 font-display text-4xl font-extrabold">{hover?.name}</h3>
            <div className="mt-6 grid grid-cols-3 gap-3">
              {[
                { l: "Youth", v: hover?.youth },
                { l: "Beneficiaries", v: hover?.beneficiaries },
                { l: "Groups", v: hover?.groups },
              ].map((x) => (
                <div key={x.l}>
                  <div className="font-display text-2xl font-extrabold tabular-nums text-gold">{x.v?.toLocaleString()}</div>
                  <div className="text-xs text-cream/60">{x.l}</div>
                </div>
              ))}
            </div>
          </motion.div>
          <div className="grid grid-cols-2 gap-2">
            {regions.slice(0, 6).map((r) => (
              <button key={r.id} onMouseEnter={() => setHoverId(r.id)}
                className={`rounded-xl px-3 py-2 text-left text-sm font-medium transition-colors ${hover?.id === r.id ? "bg-gold text-brown-deep" : "bg-muted text-coffee hover:bg-gold/20"}`}>
                {r.name}
              </button>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
