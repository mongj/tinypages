"""Scout-specific goals parameterized by seed URL."""

from __future__ import annotations

from collections.abc import Callable

from scout_schema import OUTPUT_SCHEMA, PURPOSE_OUTPUT_SCHEMA, SHARED_RULES


def _goal(intro: str, schema: str = OUTPUT_SCHEMA) -> str:
    parts = [intro.strip(), "", schema, "", SHARED_RULES]
    return "\n".join(parts)


def goal_purpose(seed_url: str) -> str:
    return _goal(
        f"""You start at: {seed_url}
Scout focus — site purpose and context (for downstream AI agents, not user journeys):
- Read the homepage and shallow linked pages only; infer what the organization offers and who it serves.
- Ground claims in visible copy, navigation labels, and page structure.
- Output summary metadata only; keep flows as an empty array [].""",
        PURPOSE_OUTPUT_SCHEMA,
    )


def goal_nav_ia(seed_url: str) -> str:
    return _goal(
        f"""You start at: {seed_url}
Scout focus — navigation and information architecture:
- Identify primary nav, footer links, and obvious hero/CTA buttons.
- For each distinct user intent path (browse catalog, learn pricing, read docs, contact sales, etc.), propose one flow.
- Map labels to likely intents using intent_category values from the OUTPUT_SCHEMA union below.
- Do not duplicate the same destination URL as multiple flows unless the user intent clearly differs."""
    )


def goal_account_auth(seed_url: str) -> str:
    return _goal(
        f"""You start at: {seed_url}
Scout focus — account and authentication:
- Find sign in, sign up, register, and password-reset or account-recovery entry points.
- Outline the shortest plausible path from the homepage to each auth-related screen WITHOUT signing in.
- If login is required to proceed, record login_required blockers and any visible entry_points you found."""
    )


def goal_commerce(seed_url: str) -> str:
    return _goal(
        f"""You start at: {seed_url}
Scout focus — commerce (only if relevant to this site):
- Look for product listing, product detail, add-to-cart, cart, checkout, and payment UI.
- Stop before submitting payment; do not place orders.
- If the site is not commercial, return flows: [] and explain in notes."""
    )


def goal_support_legal(seed_url: str) -> str:
    return _goal(
        f"""You start at: {seed_url}
Scout focus — support, trust, and legal:
- Find help center, docs, contact/support, privacy policy, terms of service, security, and status pages if visible from main IA.
- One flow per major destination (e.g. Help center, Contact, Privacy).
- Keep steps shallow; note blockers if content is behind login."""
    )


def goal_search_discovery(seed_url: str) -> str:
    return _goal(
        f"""You start at: {seed_url}
Scout focus — search and discovery:
- Find global or site search entry points (header, nav, mobile menu).
- If reachable without logging in, open search, run a simple query or observe empty state, filters, facets, and category/browse vs search overlap.
- One flow per distinct search or discovery path; use intent_category search where appropriate.
- If there is no on-site search, return flows: [] and explain in notes."""
    )


def goal_leads_forms(seed_url: str) -> str:
    return _goal(
        f"""You start at: {seed_url}
Scout focus — forms and lead capture (not checkout):
- Find contact, demo or trial request, newsletter signup, webinar or event registration, and “talk to sales” style CTAs.
- Outline shallow paths to each form’s first screen; do not submit with real personal data.
- Stop before completing sensitive submissions; use intent_category lead.
- If none apply, return flows: [] and explain in notes."""
    )


def goal_content(seed_url: str) -> str:
    return _goal(
        f"""You start at: {seed_url}
Scout focus — content and marketing resources:
- Find blog, news, resources or downloads, case studies, changelog, and press-style pages reachable from shallow navigation.
- One flow per major content hub or listing; prefer intent_category content.
- Do not duplicate pure help-center or legal pages (those belong to support); focus on editorial or marketing journeys."""
    )


def goal_dev_platform(seed_url: str) -> str:
    return _goal(
        f"""You start at: {seed_url}
Scout focus — developer and API surfaces:
- Find developer docs, API reference, SDKs, “get API key” or console signup, sandboxes or playgrounds, and API-oriented status pages.
- Shallow paths only; do not create real API keys or production resources.
- Use intent_category dev; if the site has no developer area, return flows: [] and explain in notes."""
    )


def goal_booking(seed_url: str) -> str:
    return _goal(
        f"""You start at: {seed_url}
Scout focus — booking and scheduling:
- Find appointment booking, reservations, calendar or slot pickers, and service selection flows (without completing a real booking).
- Stop before confirming a real reservation; note login or payment gates.
- Use intent_category booking; if not relevant, return flows: [] and explain in notes."""
    )


def goal_locale(seed_url: str) -> str:
    return _goal(
        f"""You start at: {seed_url}
Scout focus — localization and region:
- Find language or region switchers, country or currency selectors, and geo-specific entry behavior from the homepage and main nav.
- One flow per way users change locale or region; use intent_category locale.
- If only a single locale is offered with no controls, return flows: [] or a minimal flow describing that in notes."""
    )


def goal_onboarding(seed_url: str) -> str:
    return _goal(
        f"""You start at: {seed_url}
Scout focus — onboarding gates and consent:
- Observe cookie or consent banners, age gates, newsletter or modal prompts, first-run tours, and obvious paywall teasers from the landing experience.
- Record how a user would accept, dismiss, or bypass each gate without deceptive interaction.
- Use intent_category onboarding; keep steps shallow and safe (no real account creation unless it is clearly a public sign-up CTA already covered elsewhere)."""
    )


def goal_careers(seed_url: str) -> str:
    return _goal(
        f"""You start at: {seed_url}
Scout focus — careers and recruiting:
- Find careers, jobs, hiring, or “join us” entry points and paths to job listings or detail pages.
- If apply flows leave to an external ATS, capture the handoff in steps and evidence.
- Use intent_category careers; if absent, return flows: [] and explain in notes."""
    )


def goal_partners(seed_url: str) -> str:
    return _goal(
        f"""You start at: {seed_url}
Scout focus — partners and ecosystem:
- Find partner programs, reseller or affiliate signup, marketplaces, integrations or app directories, and “become a partner” flows.
- Shallow exploration only; use intent_category partner.
- If none exist, return flows: [] and explain in notes."""
    )


def goal_community(seed_url: str) -> str:
    return _goal(
        f"""You start at: {seed_url}
Scout focus — community and social engagement:
- Find forums, community portals, Discord or social links as primary CTAs, comments, and user-generated content entry points.
- Distinguish from support tickets: intent is discussion or social follow. Use intent_category community.
- If only footer social icons with no journey, one short flow or flows: [] with notes."""
    )


def goal_locations(seed_url: str) -> str:
    return _goal(
        f"""You start at: {seed_url}
Scout focus — maps and store or location finder:
- Find store locator, dealer finder, “find us,” or embedded map flows from shallow nav.
- Stop before submitting personal location queries if that would be invasive; prefer browsing the locator UI.
- Use intent_category location; if not present, return flows: [] and explain in notes."""
    )


def goal_configure(seed_url: str) -> str:
    return _goal(
        f"""You start at: {seed_url}
Scout focus — comparison and configurators:
- Find product comparison, configurators, build-your-own, or “get a quote” builders distinct from standard add-to-cart.
- Shallow paths; do not submit real quote requests with personal data.
- Use intent_category configure; if none, return flows: [] and explain in notes."""
    )


def goal_billing(seed_url: str) -> str:
    return _goal(
        f"""You start at: {seed_url}
Scout focus — subscriptions and account billing (when separate from storefront checkout):
- From public or account-adjacent entry points only, look for plan management, billing portal links, invoice history, or cancel-subscription paths.
- Do not complete cancellation or change real payment methods; record login_required blockers.
- Use intent_category billing; if only standard checkout exists, return flows: [] and note overlap with commerce."""
    )


def goal_ir(seed_url: str) -> str:
    return _goal(
        f"""You start at: {seed_url}
Scout focus — investor relations and corporate governance:
- Find investor relations, annual reports, SEC or filings links, ESG or sustainability reports if clearly labeled from main or footer nav.
- One flow per major IR destination; use intent_category investor.
- If not a public company or no IR section, return flows: [] and explain in notes."""
    )


def goal_media_a11y(seed_url: str) -> str:
    return _goal(
        f"""You start at: {seed_url}
Scout focus — media players and accessibility affordances visible in the UI:
- Find prominent video or audio players, transcript or caption controls, and skip links or similar patterns you can observe without specialized tooling.
- Only record what is visibly present; do not guess compliance. Use intent_category media.
- If no notable media or a11y UI, return flows: [] and explain in notes."""
    )


SCOUT_SPECS: dict[str, tuple[str, Callable[[str], str]]] = {
    "purpose": ("Site purpose / context", goal_purpose),
    "nav": ("Navigation / IA", goal_nav_ia),
    "auth": ("Account / auth", goal_account_auth),
    "commerce": ("Commerce", goal_commerce),
    "support": ("Support / legal", goal_support_legal),
    "search": ("Search / discovery", goal_search_discovery),
    "leads": ("Forms / lead capture", goal_leads_forms),
    "content": ("Content / resources", goal_content),
    "dev": ("Developer / API", goal_dev_platform),
    "booking": ("Booking / scheduling", goal_booking),
    "locale": ("Localization / region", goal_locale),
    "onboarding": ("Onboarding / consent", goal_onboarding),
    "careers": ("Careers / recruiting", goal_careers),
    "partners": ("Partners / ecosystem", goal_partners),
    "community": ("Community / social", goal_community),
    "locations": ("Store / location finder", goal_locations),
    "configure": ("Compare / configurators", goal_configure),
    "billing": ("Subscription / billing", goal_billing),
    "ir": ("Investor relations", goal_ir),
    "media_a11y": ("Media / a11y affordances", goal_media_a11y),
}


def list_scout_ids() -> list[str]:
    return list(SCOUT_SPECS.keys())


def build_goal(scout_id: str, seed_url: str) -> str:
    if scout_id not in SCOUT_SPECS:
        raise ValueError(f"Unknown scout_id: {scout_id}. Choose from {list_scout_ids()}")
    _, fn = SCOUT_SPECS[scout_id]
    return fn(seed_url)
