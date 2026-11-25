from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.routers import comments, tickets, users

app = FastAPI(title="Ticket API", version="0.1.0")

# Day 11: allow the ticket-ui React app (Vite dev server on port 5174) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://127.0.0.1:5174"],
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)

app.include_router(users.router)
app.include_router(tickets.router)
app.include_router(comments.router)


def problem_response(status_code: int, title: str, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "type": "about:blank",
            "title": title,
            "status": status_code,
            "detail": detail,
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    title = {
        400: "Bad Request",
        404: "Not Found",
        409: "Conflict",
        422: "Validation Error",
    }.get(exc.status_code, "Error")
    return problem_response(exc.status_code, title, str(exc.detail))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return problem_response(422, "Validation Error", str(exc.errors()))


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return problem_response(500, "Internal Server Error", "An unexpected error occurred")


@app.get("/health")
def health():
    return {"status": "ok"}
