import { notFound } from "next/navigation";
import { getSite } from "../../data/sites";
import { SiteOverview } from "../../components/site/SiteOverview";

export default async function SitePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const site = await getSite(slug);
  if (!site) notFound();

  return <SiteOverview meta={site.meta} flows={site.flows} />;
}
