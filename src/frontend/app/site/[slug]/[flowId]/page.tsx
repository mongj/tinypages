import { notFound } from "next/navigation";
import { getSite } from "../../../data/sites";
import { FlowDetail } from "../../../components/site/FlowDetail";

export default async function FlowPage({
  params,
}: {
  params: Promise<{ slug: string; flowId: string }>;
}) {
  const { slug, flowId } = await params;
  const site = await getSite(slug);
  if (!site) notFound();

  const flow = site.flows.merged_flows.find((f) => f.id === flowId);
  if (!flow) notFound();

  return <FlowDetail flow={flow} />;
}
