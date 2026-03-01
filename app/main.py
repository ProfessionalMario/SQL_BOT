from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from app.model_brain import query_model
import time

app = FastAPI()

# Jinja2 templates setup
templates = Jinja2Templates(directory="templates")  # make sure home.html is here

# Pydantic models
class QueryRequest(BaseModel):
    prompt: str

class QueryResponse(BaseModel):
    response: str

# Root endpoint serving home.html
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

# POST endpoint to query the model
@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    try:
        total_start = time.perf_counter()

        # ---- Prompt prep timing (if you add logic later) ----
        prep_start = time.perf_counter()
        prompt = request.prompt
        prep_end = time.perf_counter()

        # ---- Model inference timing ----
        infer_start = time.perf_counter()
        result = query_model(prompt)
        infer_end = time.perf_counter()

        total_end = time.perf_counter()

        print("\n===== TIMING BREAKDOWN =====")
        print(f"Prompt prep time  : {prep_end - prep_start:.4f} sec")
        print(f"Inference time    : {infer_end - infer_start:.4f} sec")
        print(f"Total request time: {total_end - total_start:.4f} sec")
        print("============================\n")

        return {"response": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))