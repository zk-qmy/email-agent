from pydantic import BaseModel
from typing import Optional
from fastapi import HTTPException
import json

from src.agent.tools.rag.pipeline import query_guide
from src.agent.tools.rag.config import INDEX_CACHE_PATH
from src.integrations.llm.client import get_llm
from src.agent.utils import extract_text
from config.tool_prompts.rag import rag_prompts
import os


class SuggestDepartmentRequest(BaseModel):
    student_request: str


class SuggestDepartmentResponse(BaseModel):
    department: Optional[str] = None
    contact: Optional[str] = None
    reply_time: Optional[str] = None
    reason: Optional[str] = None
    notes: Optional[str] = None


class AskGuideRequest(BaseModel):
    question: str


class AskGuideResponse(BaseModel):
    answer: Optional[str] = None
    source_section: Optional[str] = None
    found_in_guide: bool = False


class SearchRequest(BaseModel):
    query: str
    top_k: int = 3


class RagStatusResponse(BaseModel):
    index_loaded: bool = False
    index_exists: bool = False
    chunk_count: int = 0
    cache_path: str = ""


async def handle_suggest_department(request: SuggestDepartmentRequest):
    try:
        context = query_guide(request.student_request)
        rendered = rag_prompts.suggest_department.render(
            context=context,
            student_request=request.student_request
        )
        result = extract_text(get_llm().invoke(rendered.to_prompt()))
        clean = result.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(clean)
        return SuggestDepartmentResponse(**data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Invalid JSON from LLM")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"suggest_department failed: {str(e)}")


async def handle_ask_guide(request: AskGuideRequest):
    try:
        context = query_guide(request.question)
        rendered = rag_prompts.ask_guide.render(
            context=context,
            question=request.question
        )
        result = extract_text(get_llm().invoke(rendered.to_prompt()))
        clean = result.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(clean)
        return AskGuideResponse(**data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Invalid JSON from LLM")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ask_guide failed: {str(e)}")


async def handle_search(request: SearchRequest):
    try:
        context = query_guide(request.query, request.top_k)
        rendered = rag_prompts.search_docs.render(
            context=context,
            query=request.query
        )
        result = extract_text(get_llm().invoke(rendered.to_prompt()))
        clean = result.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(clean)
        return AskGuideResponse(**data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Invalid JSON from LLM")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"search failed: {str(e)}")


async def handle_rag_status():
    cache_exists = os.path.exists(INDEX_CACHE_PATH)
    chunk_count = 0
    index_loaded = False

    if cache_exists:
        try:
            from src.agent.tools.rag.embedder import load_index
            _, chunks = load_index()
            chunk_count = len(chunks)
            index_loaded = True
        except Exception:
            pass

    return RagStatusResponse(
        index_loaded=index_loaded,
        index_exists=cache_exists,
        chunk_count=chunk_count,
        cache_path=INDEX_CACHE_PATH,
    )
