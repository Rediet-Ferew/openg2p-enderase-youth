import { motion } from "framer-motion";
import { useCountUp } from "@/hooks/use-count-up";
import { useRegistryData } from "@/hooks/use-registry-data";
import { TrendingUp, UserRound, PersonStanding } from "lucide-react";

function Ring({ pct, r, stroke, color, delay = 0 }: { pct: number; r: number; stroke: number; color: string; delay?: number }) {
  const c = 2 * Math.PI * r;
  return (
    <circle
      cx="140" cy="140" r={r} fill="none" stroke={color} strokeWidth={stroke}
      strokeLinecap="round" strokeDasharray={c}
      style={{ animation: "none" }}
      strokeDashoffset={0}
      transform="rotate(-90 140 140)"
    >
      <animate attributeName="stroke-dashoffset" from={c} to={c * (1 - pct)} dur="1.6s" begin={`${delay}s`} fill="freeze" calcMode="spline" keySplines="0.16 1 0.3 1" keyTimes="0;1" />
    </circle>
  );
}

export function Hero() {
  const { registry, demographics } = useRegistryData();
  const count = useCountUp(registry.registeredYouth);
  const femalePct = demographics.female / registry.registeredYouth;

  return (
    <section className="relative overflow-hidden rounded-[2.5rem] bg-gradient-brown px-6 py-12 text-cream shadow-soft md:px-12 md:py-16">
      {/* decorative sun blob */}
      <div className="pointer-events-none absolute -right-24 -top-24 h-80 w-80 rounded-full bg-gradient-sun opacity-30 blur-2xl" />
      <div className="pointer-events-none absolute -left-16 bottom-0 h-56 w-56 blob bg-gold/10 blur-xl" />

      <div className="relative grid items-center gap-10 lg:grid-cols-[1.1fr_0.9fr]">
        <div>
          <motion.span
            initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
            className="inline-flex items-center gap-2 rounded-full bg-cream/10 px-4 py-1.5 text-sm font-medium text-gold ring-1 ring-gold/30"
          >
            <span className="h-2 w-2 rounded-full bg-gold" /> Enderase Youth Association
          </motion.span>
          <motion.h1
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.1 }}
            className="mt-5 font-display text-5xl font-extrabold leading-[0.95] md:text-7xl"
          >
            Enderase<br />Registry <span className="text-gradient-gold">Overview</span>
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.7, delay: 0.3 }}
            className="mt-5 max-w-md text-lg text-cream/70"
          >
            Empowering Ethiopian Youth Through Data — a living story of hope, community and leadership across all 11 regions.
          </motion.p>

          <div className="mt-8 flex flex-wrap gap-3">
            <span className="rounded-full bg-gold px-5 py-2.5 font-display font-bold text-brown-deep shadow-gold">
              {registry.growthYoY}% growth YoY
            </span>
            <span className="rounded-full bg-cream/10 px-5 py-2.5 font-medium text-cream ring-1 ring-cream/20">
              {registry.regions} regions · {registry.groups.toLocaleString()} groups
            </span>
          </div>
        </div>

        {/* circular hero visualization */}
        <div className="relative mx-auto flex h-[300px] w-[300px] items-center justify-center">
          <div className="absolute inset-0 animate-pulse-ring rounded-full bg-gold/20" />
          <svg viewBox="0 0 280 280" className="h-full w-full drop-shadow-2xl">
            <Ring r={128} stroke={10} color="hsl(40 43% 96% / 0.12)" pct={1} />
            <Ring r={128} stroke={10} color="hsl(44 92% 52%)" pct={0.86} delay={0.2} />
            <Ring r={108} stroke={8} color="hsl(40 43% 96% / 0.12)" pct={1} />
            <Ring r={108} stroke={8} color="hsl(38 88% 58%)" pct={femalePct} delay={0.4} />
            <Ring r={88} stroke={6} color="hsl(40 43% 96% / 0.1)" pct={1} />
            <Ring r={88} stroke={6} color="hsl(30 45% 60%)" pct={0.35} delay={0.6} />
          </svg>
          <div className="absolute flex flex-col items-center text-center">
            <span className="font-display text-5xl font-extrabold tabular-nums text-cream">
              {count.toLocaleString()}
            </span>
            <span className="mt-1 max-w-[130px] text-sm font-medium uppercase text-gold">
              Registered Youth
            </span>
            <span className="mt-2 inline-flex items-center gap-1 text-xs text-cream/60">
              <TrendingUp className="h-3 w-3" /> live registry
            </span>
          </div>
        </div>
      </div>

      {/* floating stat badges */}
      <div className="relative mt-10 grid grid-cols-2 gap-4 md:grid-cols-4">
        {[
          { label: "Beneficiaries", value: registry.beneficiaries, tone: "gold" },
          { label: "Active Groups", value: registry.groups, tone: "cream" },
          { label: "Programs", value: registry.programs, tone: "cream" },
          { label: "Organizations", value: registry.organizations, tone: "gold" },
        ].map((s) => (
          <div key={s.label}
            className={`rounded-3xl px-5 py-5 ${s.tone === "gold" ? "bg-gradient-gold text-brown-deep" : "bg-cream/10 text-cream ring-1 ring-cream/15"}`}>
            <div className="font-display text-3xl font-extrabold tabular-nums">{s.value.toLocaleString()}</div>
            <div className="mt-1 text-sm font-medium opacity-80">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="relative mt-6 flex gap-4 text-sm">
        <span className="inline-flex items-center gap-2 text-cream/70"><UserRound className="h-4 w-4 text-gold" /> {demographics.female.toLocaleString()} female</span>
        <span className="inline-flex items-center gap-2 text-cream/70"><PersonStanding className="h-4 w-4 text-gold-warm" /> {demographics.male.toLocaleString()} male</span>
      </div>
    </section>
  );
}
