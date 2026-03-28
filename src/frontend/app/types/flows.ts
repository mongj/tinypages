export interface EntryPoint {
  label: string;
  url: string | null;
  location:
    | "nav"
    | "footer"
    | "cta"
    | "hero"
    | "modal"
    | "breadcrumb"
    | "other";
}

export interface Step {
  order: number;
  action: "click" | "navigate" | "type" | "scroll" | "submit" | "other";
  description: string;
}

export interface Evidence {
  urls_seen: string[];
  labels_seen: string[];
  notes?: string;
}

export interface Blocker {
  type:
    | "captcha"
    | "login_required"
    | "payment_required"
    | "blocked"
    | "none"
    | "unknown";
  detail: string;
}

export interface Provenance {
  scout_id: string;
  run_id: string;
}

export interface Flow {
  id: string;
  name: string;
  intent_category: string;
  confidence: number;
  entry_points: EntryPoint[];
  steps: Step[];
  evidence: Evidence;
  blockers: Blocker[];
  _provenance?: Provenance[];
}

export interface SiteUnderstanding {
  one_line_summary: string;
  what_the_site_does: string;
  organization_or_brand: string;
  offerings: string[];
  primary_audiences: string[];
  confidence: number;
  evidence: Evidence;
  _provenance?: Provenance;
}

export interface SiteFlows {
  seed_url: string;
  created_at: string;
  merged_flows: Flow[];
  merge_count: number;
  source_runs: number;
  collected_notes: string[];
  site_understanding?: SiteUnderstanding;
}

export interface SiteMeta {
  slug: string;
  name: string;
  seed_url: string;
  host: string;
  flowCount: number;
  scoutCount: number;
  created_at: string;
  one_line_summary?: string;
}
