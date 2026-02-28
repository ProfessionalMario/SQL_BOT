from fastapi import FastAPI,Request
from pydantic import BaseModel
import sqlite3
from fastapi.templating import Jinja2Templates
import os 

app= FastAPI()

templates = Jinja2Templates(directory="templates")

class QueryRequest(BaseModel):
    question: str

@app.get("/")
def root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.post("/query")
def receive_query(request: QueryRequest):
    try:

        conn = sqlite3.connect("Chinook_Sqlite.sqlite")
        cursor = conn.cursor()
        

        cursor.execute(request.question)
        rows = cursor.fetchall()

        conn.commit()
        conn.close()

        return {"result": rows}

    except Exception as e:
        return {"error": str(e)}