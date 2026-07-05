import { motion } from "framer-motion";
import { useRegistryData } from "@/hooks/use-registry-data";

const tones = [
  "bg-gradient-gold text-brown-deep",
  "bg-gold-warm text-brown-deep",
  "bg-coffee text-cream",
  "bg-secondary text-cream",
  "bg-gradient-brown text-cream",
];

export function Pipeline() {
  const { pipeline } = useRegistryData();
  const max = pipeline[0].value;
  return (
    <section>
      <SectionHeading eyebrow="Journey" title="Membership Pipeline"
        note="From first registration to youth leadership." />
      <div className="mt-8 space-y-3">
        {pipeline.map((s, i) => {
          const pct = (s.value / max) * 100;
          return (
            <div key={s.stage} className="flex items-center gap-4">
              <div className="w-28 shrink-0 text-right font-display text-sm font-bold text-coffee md:w-40 md:text-base">
                {s.stage}
              </div>
              <div className="relative h-14 flex-1 overflow-hidden rounded-full bg-muted">
                <motion.div
                  initial={{ width: 0 }} whileInView={{ width: `${pct}%` }} viewport={{ once: true }}
                  transition={{ duration: 1.1, delay: i * 0.12, ease: [0.16, 1, 0.3, 1] }}
                  className={`flex h-full items-center justify-end rounded-full pr-5 ${tones[i]} shadow-block`}
                >
                  <span className="font-display text-lg font-extrabold tabular-nums">
                    {s.value.toLocaleString()}
                  </span>
                </motion.div>
                {i < pipeline.length - 1 && (
                  <span className="absolute right-4 top-1/2 hidden -translate-y-1/2 text-xs font-medium text-muted-foreground md:block" style={{ left: `calc(${pct}% + 12px)` }}>
                    {Math.round((pipeline[i + 1].value / s.value) * 100)}% →
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

export function SectionHeading({ eyebrow, title, note }: { eyebrow: string; title: string; note?: string }) {
  return (
    <div>
      <span className="inline-flex items-center gap-2 rounded-full bg-gold/15 px-3 py-1 text-xs font-bold uppercase text-coffee">
        <span className="h-1.5 w-1.5 rounded-full bg-gold" /> {eyebrow}
      </span>
      <h2 className="mt-3 font-display text-4xl font-extrabold text-ink md:text-5xl">{title}</h2>
      {note && <p className="mt-2 max-w-xl text-muted-foreground">{note}</p>}
    </div>
  );
}
