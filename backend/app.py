"""API Layer (Skill 6). Owner: feature/api branch.

Exposes /fields and /search per API_CONTRACT.md.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fields import FIELDS
from search import search_conferences

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/fields")
def get_fields():
    return {"fields": FIELDS}


@app.get("/search")
def search(field: str | None = None, query: str | None = None):
    # TODO: call search_conferences(field, query) and return {"results": [...]}
    raise NotImplementedError
