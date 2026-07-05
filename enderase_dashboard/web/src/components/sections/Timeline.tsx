import { motion } from "framer-motion";
import { timeline } from "@/data/registry";
import { SectionHeading } from "./Pipeline";

export function Timeline() {
  return (
    <section>
      <SectionHeading eyebrow="Timeline" title="Flowing Registration Story"
        note="How Enderase grew into a national youth movement." />
      <div className="relative mt-10 pl-4">
        <div className="absolute bottom-2 left-[7px] top-2 w-0.5 bg-gradient-to-b from-gold via-coffee to-brown-deep" />
        <div className="space-y-8">
          {timeline.map((t, i) => (
            <motion.div key={t.year}
              initial={{ opacity: 0, x: -20 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              className="relative pl-8">
              <span className="absolute -left-[3px] top-1.5 h-4 w-4 rounded-full bg-gold ring-4 ring-cream" />
              <div className="rounded-3xl bg-card p-5 shadow-block ring-1 ring-border">
                <span className="font-display text-3xl font-extrabold text-gradient-gold">{t.year}</span>
                <h3 className="mt-1 font-display text-lg font-bold text-ink">{t.title}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{t.text}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
