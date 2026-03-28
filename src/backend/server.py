from urllib.parse import urlparse

import modal
from db import get_supabase
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()


class IndexRequest(BaseModel):
    url: str


@app.get("/hello")
async def hello():
    return JSONResponse(
        status_code=418,
        content={"message": "not enough coffee"},
    )


@app.post("/index")
async def index_page(request: IndexRequest):
    parsed = urlparse(request.url)
    url = parsed.hostname or parsed.path.split("/")[0]
    # add https:// in front if not there
    if not url.startswith("https://"):
        url = "https://" + url

    row = (
        get_supabase()
        .table("jobs")
        .insert({"page_url": url, "status": "pending"})
        .execute()
    )
    job_id = row.data[0]["job_id"]

    run_job = modal.Function.from_name("tinypages-indexer", "run_job_remote")
    run_job.spawn(job_id, url)

    return {"job_id": job_id, "url": url, "status": "pending"}


@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    row = get_supabase().table("jobs").select("*").eq("job_id", job_id).single().execute()
    return row.data
