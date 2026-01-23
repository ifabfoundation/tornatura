#!/usr/bin/env python
from typing import Union

from fastapi import FastAPI, Depends, logger
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
import uvicorn

from core.serializers import ErrorResponse
from core.api.v1 import router as v1_router
# from core.routes import router

app = FastAPI()


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    payload = ErrorResponse(status=exc.status_code, detail=str(exc.detail)).model_dump()
    return JSONResponse(payload, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    payload = ErrorResponse(status=422, detail={
        "errors": exc.errors(),
    }).model_dump()
    return JSONResponse(payload, status_code=422)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the router
app.include_router(
    v1_router, 
    prefix="/v1",
    responses={
        401: {
            "description": "Unauthorized to access this resource",
            "model": ErrorResponse,
        },
        403: {
            "description": "Unauthorized to access this resource",
            "model": ErrorResponse,
        },
        422: {
            "description": "Validation error",
            "model": ErrorResponse,
        }, 
        400: {
            "description": "Bad Request",
            "model": ErrorResponse,
        },
    },
)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
