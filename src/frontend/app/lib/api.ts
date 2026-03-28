export interface IndexResponse {
  job_id: string;
  url: string;
  status: string;
}

export interface Job {
  job_id: string;
  page_url: string;
  status: "pending" | "running" | "completed" | "failed";
  start_time?: string;
  end_time?: string;
}

export async function startIndexing(url: string): Promise<IndexResponse> {
  const res = await fetch("/api/index", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to start indexing: ${text}`);
  }
  return res.json();
}

export async function getJob(jobId: string): Promise<Job> {
  const res = await fetch(`/api/jobs/${jobId}`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to fetch job: ${text}`);
  }
  return res.json();
}
