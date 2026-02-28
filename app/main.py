from fastapi import FastAPI,Request
from pydantic import BaseModel
# from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

app= FastAPI()

templates = Jinja2Templates(directory="../templates")

class QueryRequest(BaseModel):
    question: str

@app.get("/")
def root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.post('/query')
def receive_query(request: QueryRequest):
    print(request.question)
    return {"Received question": request.question}