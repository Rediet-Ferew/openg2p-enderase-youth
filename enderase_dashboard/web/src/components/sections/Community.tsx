import { motion } from "framer-motion";
import { quotes, organizations, sunburst } from "@/data/registry";
import { SectionHeading } from "./Pipeline";
import { Quote } from "lucide-react";

const quoteTones = ["bg-gradient-gold text-brown-deep", "bg-gradient-brown text-cream", "bg-coffee text-cream"];
const orgTones: Record<string, string> = {
  gold: "bg-gradient-gold text-brown-deep",
  brown: "bg-gradient-brown text-cream",
  coffee: "bg-coffee text-cream",
};

export function Community() {
  return (
    <section>
      <SectionHeading eyebrow="Community" title="Voices & Organizations"
        note="Stories from the ground and the collectives youth are building." />

      {/* quote blocks */}
      <div className="mt-8 grid gap-5 md:grid-cols-3">
        {quotes.map((q, i) => (
          <motion.blockquote key={i}
            initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
            transition={{ delay: i * 0.1 }}
            className={`relative flex flex-col justify-between rounded-[2rem] p-7 shadow-block ${quoteTones[i]} ${i === 1 ? "md:-translate-y-4" : ""}`}>
            <Quote className="h-8 w-8 opacity-40" />
            <p className="mt-4 font-display text-lg font-semibold leading-snug">“{q.text}”</p>
            <footer className="mt-6 text-sm font-medium opacity-80">{q.name} · {q.region}</footer>
          </motion.blockquote>
        ))}
      </div>

      {/* Pinterest-style organization showcase (masonry columns) */}
      <h3 className="mt-14 font-display text-2xl font-bold text-ink">Organization Showcase</h3>
      <div className="mt-5 columns-2 gap-4 md:columns-4 [&>*]:mb-4">
        {organizations.map((o, i) => (
          <motion.div key={o.name}
            initial={{ opacity: 0, scale: 0.9 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }}
            transition={{ delay: (i % 4) * 0.06 }}
            className={`break-inside-avoid rounded-3xl p-5 shadow-block ${orgTones[o.tone]}`}
            style={{ minHeight: 110 + (i % 3) * 46 }}>
            <span className="text-xs font-medium uppercase opacity-70">{o.type}</span>
            <h4 className="mt-1 font-display text-lg font-bold leading-tight">{o.name}</h4>
            <p className="mt-3 font-display text-2xl font-extrabold tabular-nums">{o.members}</p>
            <span className="text-xs opacity-70">members</span>
          </motion.div>
        ))}
      </div>

      {/* Sunburst-style geographic hierarchy */}
      <h3 className="mt-14 font-display text-2xl font-bold text-ink">Geographic Hierarchy</h3>
      <div className="mt-5 flex flex-wrap gap-3">
        {sunburst.map((s) => (
          <div key={s.region} className="rounded-3xl bg-gradient-cream p-5 ring-1 ring-border">
            <span className="rounded-full bg-gradient-gold px-3 py-1 text-sm font-bold text-brown-deep">{s.region}</span>
            <div className="mt-3 flex flex-wrap gap-2">
              {s.zones.map((z) => (
                <span key={z} className="rounded-full bg-coffee/10 px-3 py-1 text-sm font-medium text-coffee">{z}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
