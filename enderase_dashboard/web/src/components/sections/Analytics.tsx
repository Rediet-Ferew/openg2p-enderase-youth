import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, PieChart, Pie, Cell,
  Treemap, RadialBarChart, RadialBar, PolarAngleAxis, AreaChart, Area,
} from "recharts";
import { motion } from "framer-motion";
import { training, trainingWheels, entrepreneurship } from "@/data/registry";
import { useRegistryData } from "@/hooks/use-registry-data";
import { SectionHeading } from "./Pipeline";

const gold = "hsl(44 92% 52%)";
const warm = "hsl(38 88% 58%)";
const coffee = "hsl(30 45% 34%)";
const brown = "hsl(28 62% 22%)";
const cream = "hsl(40 43% 96%)";

const box = "rounded-[2rem] bg-card p-6 shadow-block ring-1 ring-border";

function CardLabel({ children }: { children: React.ReactNode }) {
  return <h3 className="mb-4 font-display text-xl font-bold text-ink">{children}</h3>;
}

export function Analytics() {
  const { growth, treemap, demographics } = useRegistryData();
  return (
    <section>
      <SectionHeading eyebrow="Analytics" title="The Numbers, Reimagined"
        note="Growth, training, skills sectors and split-profile demographics." />

      <div className="mt-8 grid gap-5 lg:grid-cols-3">
        {/* Growth stacked area */}
        <div className={`${box} lg:col-span-2`}>
          <CardLabel>Registry Growth</CardLabel>
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={growth} margin={{ left: -18, right: 8, top: 8 }}>
              <defs>
                <linearGradient id="gYouth" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={gold} stopOpacity={0.9} />
                  <stop offset="100%" stopColor={gold} stopOpacity={0.1} />
                </linearGradient>
                <linearGradient id="gBen" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={coffee} stopOpacity={0.8} />
                  <stop offset="100%" stopColor={coffee} stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <XAxis dataKey="year" tickLine={false} axisLine={false} tick={{ fill: coffee, fontSize: 12 }} />
              <YAxis tickLine={false} axisLine={false} tick={{ fill: coffee, fontSize: 11 }} />
              <Tooltip contentStyle={{ borderRadius: 16, border: "none", boxShadow: "0 10px 30px rgba(0,0,0,.15)" }} />
              <Area type="monotone" dataKey="youth" stroke={gold} strokeWidth={3} fill="url(#gYouth)" />
              <Area type="monotone" dataKey="beneficiaries" stroke={coffee} strokeWidth={3} fill="url(#gBen)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Training donut */}
        <div className={box}>
          <CardLabel>Training Status</CardLabel>
          <div className="relative">
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={training} dataKey="value" innerRadius={68} outerRadius={100} paddingAngle={3} strokeWidth={0}>
                  {[gold, warm, coffee].map((c, i) => <Cell key={i} fill={c} />)}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: 16, border: "none" }} />
              </PieChart>
            </ResponsiveContainer>
            <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
              <span className="font-display text-3xl font-extrabold text-ink">{training[0].value}%</span>
              <span className="text-xs text-muted-foreground">completed</span>
            </div>
          </div>
          <div className="mt-3 flex justify-center gap-4 text-xs">
            {training.map((t, i) => (
              <span key={t.name} className="inline-flex items-center gap-1.5 text-coffee">
                <span className="h-2.5 w-2.5 rounded-full" style={{ background: [gold, warm, coffee][i] }} /> {t.name}
              </span>
            ))}
          </div>
        </div>

        {/* Split profile demographics */}
        <div className={box}>
          <CardLabel>Split Profile — Gender & Age</CardLabel>
          <div className="mb-5 flex overflow-hidden rounded-full">
            <div className="flex h-9 items-center justify-center bg-gradient-gold text-xs font-bold text-brown-deep" style={{ width: `${(demographics.female / (demographics.female + demographics.male)) * 100}%` }}>
              Female {Math.round((demographics.female / (demographics.female + demographics.male)) * 100)}%
            </div>
            <div className="flex h-9 flex-1 items-center justify-center bg-coffee text-xs font-bold text-cream">
              Male {Math.round((demographics.male / (demographics.female + demographics.male)) * 100)}%
            </div>
          </div>
          <ResponsiveContainer width="100%" height={150}>
            <BarChart data={demographics.ageBands} margin={{ left: -22 }}>
              <XAxis dataKey="band" tickLine={false} axisLine={false} tick={{ fill: coffee, fontSize: 11 }} />
              <YAxis hide />
              <Tooltip cursor={{ fill: "hsl(44 92% 52% / 0.1)" }} contentStyle={{ borderRadius: 16, border: "none" }} />
              <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                {demographics.ageBands.map((_, i) => <Cell key={i} fill={[gold, warm, coffee, brown][i]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Radial training wheels */}
        <div className={box}>
          <CardLabel>Training Wheels</CardLabel>
          <ResponsiveContainer width="100%" height={210}>
            <RadialBarChart innerRadius="30%" outerRadius="100%" data={trainingWheels} startAngle={90} endAngle={-270}>
              <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
              <RadialBar background dataKey="value" cornerRadius={12}>
                {trainingWheels.map((_, i) => <Cell key={i} fill={[gold, warm, coffee, brown][i]} />)}
              </RadialBar>
            </RadialBarChart>
          </ResponsiveContainer>
          <div className="mt-2 grid grid-cols-2 gap-1 text-xs">
            {trainingWheels.map((w, i) => (
              <span key={w.label} className="inline-flex items-center gap-1.5 text-coffee">
                <span className="h-2 w-2 rounded-full" style={{ background: [gold, warm, coffee, brown][i] }} /> {w.label} {w.value}%
              </span>
            ))}
          </div>
        </div>

        {/* Treemap sectors */}
        <div className={box}>
          <CardLabel>Skill Sectors</CardLabel>
          <ResponsiveContainer width="100%" height={240}>
            <Treemap data={treemap} dataKey="size" stroke={cream} fill={gold} content={<TreeCell />} />
          </ResponsiveContainer>
        </div>
      </div>

      {/* Entrepreneurship ecosystem */}
      <div className={`${box} mt-5`}>
        <CardLabel>Entrepreneurship Ecosystem</CardLabel>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
          {entrepreneurship.map((e, i) => (
            <motion.div key={e.name}
              initial={{ scale: 0.6, opacity: 0 }} whileInView={{ scale: 1, opacity: 1 }} viewport={{ once: true }}
              transition={{ type: "spring", stiffness: 140, delay: i * 0.08 }}
              className="flex flex-col items-center justify-center rounded-full bg-gradient-cream p-5 text-center ring-2 ring-gold/40"
              style={{ aspectRatio: "1" }}>
              <span className="font-display text-2xl font-extrabold text-brown-deep tabular-nums">{e.value.toLocaleString()}</span>
              <span className="text-xs font-medium text-coffee">{e.name}</span>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

type TreeCellProps = {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  index?: number;
  name?: string;
};

function TreeCell({ x = 0, y = 0, width = 0, height = 0, index = 0, name = "" }: TreeCellProps) {
  const colors = ["hsl(44 92% 52%)", "hsl(38 88% 58%)", "hsl(30 45% 34%)", "hsl(28 62% 22%)", "hsl(30 45% 44%)", "hsl(38 60% 46%)"];
  return (
    <g>
      <rect x={x} y={y} width={width} height={height} rx={12} fill={colors[index % colors.length]} stroke="hsl(40 43% 96%)" strokeWidth={3} />
      {width > 60 && height > 30 && (
        <text x={x + 12} y={y + 24} fill="hsl(40 43% 96%)" fontSize={13} fontWeight={700}>{name}</text>
      )}
    </g>
  );
}
