from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import config  # noqa: F401 - fail fast at startup if JWT_SECRET is missing
from app.routers import auth, comments, tickets, users

app = FastAPI(title="Ticket API", version="0.1.0")

# Day 11: allow the ticket-ui React app (Vite dev server on port 5174) to call this API.
# Day 12: + Authorization header (Bearer token). No cookies are used, so no allow_credentials.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://127.0.0.1:5174"],
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tickets.router)
app.include_router(comments.router)


def problem_response(
    status_code: int, title: str, detail: str, headers: dict[str, str] | None = None
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        headers=headers,
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
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        409: "Conflict",
        422: "Validation Error",
        429: "Too Many Requests",
    }.get(exc.status_code, "Error")
    # Keep headers such as WWW-Authenticate: Bearer on 401 responses.
    return problem_response(exc.status_code, title, str(exc.detail), getattr(exc, "headers", None))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Only field + message: never echo submitted values back (they may contain a password).
    errors = [
        {"loc": list(e.get("loc", [])), "msg": e.get("msg", ""), "type": e.get("type", "")}
        for e in exc.errors()
    ]
    return problem_response(422, "Validation Error", str(errors))


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return problem_response(500, "Internal Server Error", "An unexpected error occurred")


@app.get("/health")
def health():
    return {"status": "ok"}
