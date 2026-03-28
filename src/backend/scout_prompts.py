"""Scout-specific goals parameterized by seed URL."""

from __future__ import annotations

from scout_schema import OUTPUT_SCHEMA, SHARED_RULES


def _goal(intro: str) -> str:
    parts = [intro.strip(), "", OUTPUT_SCHEMA, "", SHARED_RULES]
    return "\n".join(parts)


def goal_nav_ia(seed_url: str) -> str:
    return _goal(
        f"""You start at: {seed_url}
Scout focus — navigation and information architecture:
- Identify primary nav, footer links, and obvious hero/CTA buttons.
- For each distinct user intent path (browse catalog, learn pricing, read docs, contact sales, etc.), propose one flow.
- Map labels to likely intents (browse, buy, support, account, etc.) in intent_category.
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


SCOUT_SPECS: dict[str, tuple[str, str]] = {
    "nav": ("Navigation / IA", goal_nav_ia),
    "auth": ("Account / auth", goal_account_auth),
    "commerce": ("Commerce", goal_commerce),
    "support": ("Support / legal", goal_support_legal),
}


def list_scout_ids() -> list[str]:
    return list(SCOUT_SPECS.keys())


def build_goal(scout_id: str, seed_url: str) -> str:
    if scout_id not in SCOUT_SPECS:
        raise ValueError(f"Unknown scout_id: {scout_id}. Choose from {list_scout_ids()}")
    _, fn = SCOUT_SPECS[scout_id]
    return fn(seed_url)
