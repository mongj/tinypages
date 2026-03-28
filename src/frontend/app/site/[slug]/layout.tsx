import { notFound } from "next/navigation";
import { getSite } from "../../data/sites";
import { Sidebar } from "../../components/site/Sidebar";

export default async function SiteLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const site = getSite(slug);
  if (!site) notFound();

  return (
    <div className="flex">
      <Sidebar
        flows={site.flows.merged_flows}
        slug={slug}
      />
      <div className="flex-1 min-w-0 p-8 max-w-4xl">
        {children}
      </div>
    </div>
  );
}
