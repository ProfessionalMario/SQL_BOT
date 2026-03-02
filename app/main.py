import json
import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from app.model_brain import query_model
from app.validator.validator import validate_model_output
from app.db.executer import execute_query
from app.utils.logger import setup_logger
from app.utils.error import (
    InvalidSQLGenerated,
    DatabaseExecutionError,
    LLMError,
)
import re
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
logger = setup_logger("main")
app= FastAPI()

# Jinja2 templates setup
templates = Jinja2Templates(directory="templates")  # make sure home.html is here

class QueryRequest(BaseModel):
    prompt: str

class QueryResponse(BaseModel):
    response: str


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("home3.html", {"request": request})


@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    try:
        total_start = time.perf_counter()

        # ---- Prompt prep timing ----
        prep_start = time.perf_counter()
        prompt = request.prompt
        prep_end = time.perf_counter()

        logger.info("Received query request")

        # ---- Model inference timing ----
        infer_start = time.perf_counter()
        model_output = query_model(prompt)

        # METHOD 1: String find() - Simple, no regex
        start_action = model_output.find('"action": "') + 11
        end_action = model_output.find('"', start_action)
        action = model_output[start_action:end_action].strip()

        start_query = model_output.find('"query": "') + 10
        end_query = model_output.find('"', start_query + 1)  # ← Key fix!
        model_query = model_output[start_query:end_query].strip()

        infer_end = time.perf_counter()

        logger.info("Model inference completed")

        # ---- Validate model output ----
        validate_model_output(model_output)

        # ---- Execute query ----
        exec_start = time.perf_counter()

        db_result = execute_query(
            model_query,
            action
        )
        exec_end = time.perf_counter()

        total_end = time.perf_counter()

        logger.info(
            f"Timing | Prep: {prep_end - prep_start:.4f}s | "
            f"Infer: {infer_end - infer_start:.4f}s | "
            f"Exec: {exec_end - exec_start:.4f}s | "
            f"Total: {total_end - total_start:.4f}s"
        )
        
        return {
            "response": json.dumps(db_result),
            "timing": {
                "prep_time": round(prep_end - prep_start, 4),
                "inference_time": round(infer_end - infer_start, 4),
                "execution_time": round(exec_end - exec_start, 4),
                "total_time": round(total_end - total_start, 4),
            },
        }

    except InvalidSQLGenerated as e:
        logger.warning(f"Validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except DatabaseExecutionError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database execution failed")

    except LLMError as e:
        logger.error(f"LLM error: {e}")
        raise HTTPException(status_code=500, detail="Model processing failed")

    except Exception as e:
        logger.exception("Unexpected server error")
        raise HTTPException(status_code=500, detail="Internal server error")