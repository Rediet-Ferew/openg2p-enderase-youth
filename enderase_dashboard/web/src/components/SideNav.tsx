import { useState } from "react";
import Image from "next/image";
import {
  LayoutDashboard, ClipboardList, HeartHandshake, Users, GraduationCap,
  MapPin, Sparkles, Dumbbell, BarChart3, FileText, Settings,
} from "lucide-react";

const items = [
  { icon: LayoutDashboard, label: "Dashboard" },
  { icon: ClipboardList, label: "Registry" },
  { icon: HeartHandshake, label: "Beneficiaries" },
  { icon: Users, label: "Groups" },
  { icon: GraduationCap, label: "Programs" },
  { icon: MapPin, label: "Geography" },
  { icon: Sparkles, label: "Skills" },
  { icon: Dumbbell, label: "Training" },
  { icon: BarChart3, label: "Analytics" },
  { icon: FileText, label: "Reports" },
  { icon: Settings, label: "Settings" },
];

export function SideNav() {
  const [active, setActive] = useState("Dashboard");
  return (
    <nav className="fixed left-0 top-0 z-40 flex h-screen w-[76px] flex-col items-center gap-1 bg-sidebar py-6 lg:w-[84px]">
      <Image src="/enderase-logo.png" alt="Enderase Youth Association logo" width={44} height={44}
        className="mb-6 h-11 w-11 rounded-2xl bg-cream/95 p-1.5 shadow-gold" />
      <div className="no-scrollbar flex flex-1 flex-col items-center gap-1 overflow-y-auto">
        {items.map(({ icon: Icon, label }) => {
          const isActive = active === label;
          return (
            <button
              key={label}
              onClick={() => setActive(label)}
              title={label}
              className={`group relative flex h-12 w-12 items-center justify-center rounded-2xl transition-all duration-300 ${
                isActive
                  ? "bg-gradient-gold text-brown-deep shadow-gold scale-105"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-gold"
              }`}
            >
              <Icon className="h-5 w-5" strokeWidth={2} />
              <span className="pointer-events-none absolute left-16 z-50 whitespace-nowrap rounded-lg bg-ink px-2.5 py-1 text-xs font-medium text-cream opacity-0 shadow-block transition-opacity group-hover:opacity-100">
                {label}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
