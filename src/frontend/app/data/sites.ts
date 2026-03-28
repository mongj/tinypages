import type { SiteFlows, SiteMeta } from "../types/flows";

import wikiWwwFlows from "./mock/www.wikipedia.org.json";
import wikiFlows from "./mock/wikipedia.org.json";
import irasFlows from "./mock/www.iras.gov.sg.json";
import tinyfishFlows from "./mock/tinyfish.ai.json";
import tinyfishDocsFlows from "./mock/docs.tinyfish.ai.json";
import hckrFlows from "./mock/hckr.cc.json";

export interface SiteEntry {
  meta: SiteMeta;
  flows: SiteFlows;
}

function deriveSlug(seedUrl: string): string {
  try {
    return new URL(seedUrl).host;
  } catch {
    return seedUrl;
  }
}

function deriveName(host: string): string {
  return host.replace(/^www\./, "");
}

function buildSiteEntry(flows: SiteFlows): SiteEntry {
  const slug = deriveSlug(flows.seed_url);
  return {
    meta: {
      slug,
      name: flows.site_understanding?.organization_or_brand || deriveName(slug),
      seed_url: flows.seed_url,
      host: slug,
      flowCount: flows.merge_count,
      scoutCount: flows.source_runs,
      created_at: flows.created_at,
      one_line_summary: flows.site_understanding?.one_line_summary,
    },
    flows,
  };
}

const ALL_FLOWS: SiteFlows[] = [
  wikiWwwFlows as SiteFlows,
  wikiFlows as SiteFlows,
  irasFlows as SiteFlows,
  tinyfishFlows as SiteFlows,
  tinyfishDocsFlows as SiteFlows,
  hckrFlows as SiteFlows,
];

const SITES: Record<string, SiteEntry> = Object.fromEntries(
  ALL_FLOWS.map((f) => {
    const entry = buildSiteEntry(f);
    return [entry.meta.slug, entry];
  })
);

export function getSite(slug: string): SiteEntry | undefined {
  return SITES[slug];
}

export function getAllSites(): SiteEntry[] {
  return Object.values(SITES);
}
