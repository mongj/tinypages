import { getAllSites } from "./data/sites";
import { SiteCard } from "./components/home/SiteCard";

export default function HomePage() {
  const sites = getAllSites();

  return (
    <div className="max-w-4xl mx-auto px-6 py-16">
      {/* Hero */}
      <div className="mb-16 text-center">
        <h1 className="text-4xl font-semibold mb-4">
          <span className="text-accent-teal">tiny</span>
          <span className="text-text-primary">pages</span>
        </h1>
        <p className="text-lg text-text-secondary max-w-lg mx-auto">
          The web, pre-read for agents. Every user flow mapped, so AI agents
          don&apos;t have to rediscover a website from scratch.
        </p>
      </div>

      {/* Site grid */}
      <div>
        <h2 className="text-sm font-medium text-text-muted uppercase tracking-wide mb-4">
          Indexed Sites
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {sites.map((site) => (
            <SiteCard key={site.meta.slug} meta={site.meta} />
          ))}
        </div>
      </div>
    </div>
  );
}
