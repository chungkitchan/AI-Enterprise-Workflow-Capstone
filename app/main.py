from fastapi import FastAPI, Form, File, UploadFile, Request, Depends, Response, HTTPException
from fastapi.openapi.utils import get_openapi
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from typing import Optional
from .routers import ingest, log, model
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()

app.include_router(ingest.router)
app.include_router(model.router)
app.include_router(log.router)

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="AI Enterprise Workflow ",
        version="0.1",
        description="This is AI Enterprise Workflow Capstone Project Submission.",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
