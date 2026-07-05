import { motion } from "framer-motion";
import { skills } from "@/data/registry";
import { SectionHeading } from "./Pipeline";

const tones = [
  "bg-gradient-gold text-brown-deep",
  "bg-coffee text-cream",
  "bg-gold-warm text-brown-deep",
  "bg-gradient-brown text-cream",
  "bg-secondary text-cream",
];

export function SkillBubbles() {
  const max = Math.max(...skills.map((s) => s.value));
  return (
    <section>
      <SectionHeading eyebrow="Skills" title="Floating Skill Bubbles"
        note="The capabilities young members are building right now." />
      <div className="mt-8 flex flex-wrap items-center justify-center gap-4 md:gap-6">
        {skills.map((s, i) => {
          const size = 90 + (s.value / max) * 120;
          return (
            <motion.div
              key={s.name}
              initial={{ scale: 0, opacity: 0 }}
              whileInView={{ scale: 1, opacity: 1 }}
              viewport={{ once: true }}
              transition={{ type: "spring", stiffness: 120, damping: 12, delay: i * 0.06 }}
              className={`flex shrink-0 flex-col items-center justify-center rounded-full text-center shadow-block ${tones[i % tones.length]} animate-float`}
              style={{ width: size, height: size, animationDelay: `${i * 0.4}s` }}
            >
              <span className="px-2 font-display text-sm font-bold leading-tight">{s.name}</span>
              <span className="mt-1 text-xs font-medium opacity-80 tabular-nums">{s.value.toLocaleString()}</span>
            </motion.div>
          );
        })}
      </div>
    </section>
  );
}
