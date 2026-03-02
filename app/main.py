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

@app.post("/query")
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
        infer_end = time.perf_counter()

        logger.info(f"Raw model output: {model_output}")

        #  STEP 1: Try parsing JSON safely
        try:
            parsed_output = json.loads(model_output)
        except json.JSONDecodeError:
            # Model returned plain text → return directly
            logger.info("Model returned plain text response")
            return {
                "response": model_output
            }

        action = parsed_output.get("action")
        model_query = parsed_output.get("query")

        #  STEP 2: Handle message-type responses
        if action == "message":
            logger.info("Model returned conversational response")
            return {
                "response": model_query
            }

        #  STEP 3: Basic safety checks
        if not action or not model_query:
            logger.warning("Missing action or query in model output")
            return {
                "response": "Invalid model response format."
            }

        #  STEP 4: Allow only SELECT queries
        if not re.match(r"^\s*select\b", model_query, re.IGNORECASE):
            logger.warning("Blocked non-SELECT query attempt")
            return {
                "response": "Only SELECT queries are allowed."
            }

        # ---- Validate SQL ----
        validate_model_output(model_query)

        # ---- Execute query ----
        exec_start = time.perf_counter()
        db_result = execute_query(model_query, action)
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
    


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)