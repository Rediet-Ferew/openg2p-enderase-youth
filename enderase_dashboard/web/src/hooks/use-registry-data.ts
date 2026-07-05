// Live registry datapoints from the dashboard API, merged over the
// illustrative dataset in @/data/registry. Anything the registry can
// answer (totals, gender/age, pipeline stages, regions, sectors, growth)
// is overridden when the API returns real numbers; everything else —
// and everything, when the API is down or the registry is still empty —
// stays on the dummy data.

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  registry as fallbackRegistry,
  demographics as fallbackDemographics,
  pipeline as fallbackPipeline,
  regions as fallbackRegions,
  treemap as fallbackTreemap,
  growth as fallbackGrowth,
} from "@/data/registry";

type Summary = {
  totals: { registeredYouth: number; beneficiaries: number; groups: number; regions: number };
  demographics: { female: number; male: number; ageBands: { band: string; value: number }[] };
  pipeline: { stage: string; value: number }[];
  regions: { region: string; youth: number; beneficiaries: number; groups: number }[];
  sectors: { name: string; size: number }[];
  growth: { year: string; youth: number; beneficiaries: number }[];
};

async function fetchSummary(): Promise<Summary> {
  const res = await fetch("/api/dashboard/summary");
  if (!res.ok) throw new Error(`dashboard API ${res.status}`);
  return res.json();
}

// Dummy Leadership ÷ Member ratio — leadership isn't tracked in the
// registry yet, so it is estimated off live member counts.
const LEADERSHIP_RATIO = 3120 / 33890;

function merge(live: Summary | undefined) {
  // An unreachable API or an empty registry keeps the illustrative story.
  if (!live || live.totals.registeredYouth <= 0) {
    return {
      registry: fallbackRegistry,
      demographics: fallbackDemographics,
      pipeline: fallbackPipeline,
      regions: fallbackRegions,
      treemap: fallbackTreemap,
      growth: fallbackGrowth,
      isLive: false,
    };
  }

  const registry = {
    ...fallbackRegistry,
    registeredYouth: live.totals.registeredYouth,
    beneficiaries: live.totals.beneficiaries,
    groups: live.totals.groups,
    regions: live.totals.regions > 0 ? live.totals.regions : fallbackRegistry.regions,
  };

  const g = live.growth;
  if (g.length >= 2 && g[g.length - 2].youth > 0) {
    registry.growthYoY = Math.round(
      (g[g.length - 1].youth / g[g.length - 2].youth - 1) * 100
    );
  }

  const haveGender = live.demographics.female + live.demographics.male > 0;
  const haveAges = live.demographics.ageBands.some((b) => b.value > 0);
  const demographics = {
    female: haveGender ? live.demographics.female : fallbackDemographics.female,
    male: haveGender ? live.demographics.male : fallbackDemographics.male,
    ageBands: haveAges ? live.demographics.ageBands : fallbackDemographics.ageBands,
  };

  const liveStages = new Map(live.pipeline.map((s) => [s.stage, s.value]));
  const member = liveStages.get("Member") ?? 0;
  const pipeline = fallbackPipeline.map((s) =>
    s.stage === "Leadership"
      ? { ...s, value: Math.max(1, Math.round(member * LEADERSHIP_RATIO)) }
      : { ...s, value: liveStages.get(s.stage) ?? s.value }
  );

  // The stylized map needs x/y positions, so live counts are merged into
  // the known region list by name; regions the registry hasn't reached
  // keep their illustrative numbers.
  const byName = new Map(live.regions.map((r) => [r.region.toLowerCase(), r]));
  const regions = fallbackRegions.map((r) => {
    const hit = byName.get(r.name.toLowerCase());
    return hit
      ? { ...r, youth: hit.youth, beneficiaries: hit.beneficiaries, groups: hit.groups }
      : r;
  });

  return {
    registry,
    demographics,
    pipeline,
    regions,
    treemap: live.sectors.length > 0 ? live.sectors : fallbackTreemap,
    growth: g.length > 0 ? g : fallbackGrowth,
    isLive: true,
  };
}

export function useRegistryData() {
  const { data } = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: fetchSummary,
    staleTime: 30_000,
    refetchInterval: 60_000,
    retry: 1,
  });
  return useMemo(() => merge(data), [data]);
}
