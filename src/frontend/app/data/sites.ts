import type { SiteFlows, SiteMeta } from "../types/flows";

export interface SiteEntry {
  meta: SiteMeta;
  flows: SiteFlows;
}

interface IndexedPageRow {
  page_url: string;
  last_indexed_by: string;
  data: Record<string, unknown>;
  created_at?: string;
}

const API_BASE = process.env.BACKEND_URL || "http://localhost:8000";

function deriveSlug(seedUrl: string): string {
  try {
    return new URL(seedUrl).host;
  } catch {
    return seedUrl.replace(/^https?:\/\//, "");
  }
}

function deriveName(host: string): string {
  return host.replace(/^www\./, "");
}

function rowToSiteEntry(row: IndexedPageRow): SiteEntry {
  const data = row.data as unknown as Omit<SiteFlows, "seed_url" | "created_at">;
  const slug = deriveSlug(row.page_url);

  const flows: SiteFlows = {
    seed_url: row.page_url,
    created_at: row.created_at || new Date().toISOString(),
    merged_flows: data.merged_flows ?? [],
    merge_count: data.merge_count ?? 0,
    source_runs: data.source_runs ?? 0,
    collected_notes: data.collected_notes ?? [],
    site_understanding: data.site_understanding,
  };

  const su = flows.site_understanding;
  return {
    meta: {
      slug,
      name: su?.organization_or_brand || deriveName(slug),
      seed_url: row.page_url,
      host: slug,
      flowCount: flows.merge_count,
      scoutCount: flows.source_runs,
      created_at: flows.created_at,
      one_line_summary: su?.one_line_summary,
    },
    flows,
  };
}

export async function getAllSites(): Promise<SiteEntry[]> {
  const res = await fetch(`${API_BASE}/sites`, { cache: "no-store" });
  if (!res.ok) return [];
  const rows: IndexedPageRow[] = await res.json();
  return rows.map(rowToSiteEntry);
}

export async function getSite(slug: string): Promise<SiteEntry | undefined> {
  const res = await fetch(`${API_BASE}/sites/${slug}`, { cache: "no-store" });
  if (!res.ok) return undefined;
  const row: IndexedPageRow = await res.json();
  return rowToSiteEntry(row);
}
