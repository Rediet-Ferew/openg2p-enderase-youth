import { SideNav } from "@/components/SideNav";
import { Hero } from "@/components/sections/Hero";
import { Pipeline } from "@/components/sections/Pipeline";
import { GeographyMap } from "@/components/sections/GeographyMap";
import { Analytics } from "@/components/sections/Analytics";
import { SkillBubbles } from "@/components/sections/SkillBubbles";
import { Community } from "@/components/sections/Community";
import { Timeline } from "@/components/sections/Timeline";
import { Footer } from "@/components/sections/Footer";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <SideNav />
      <main className="ml-[76px] lg:ml-[84px]">
        <div className="mx-auto flex max-w-7xl flex-col gap-20 px-4 py-6 md:px-8 md:py-10">
          <Hero />
          <Pipeline />
          <GeographyMap />
          <Analytics />
          <SkillBubbles />
          <Community />
          <Timeline />
          <Footer />
        </div>
      </main>
    </div>
  );
};

export default Index;
