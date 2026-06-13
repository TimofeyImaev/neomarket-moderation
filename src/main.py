from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.errors import ApiError
from src.routes import approve, decline, events, reasons

app = FastAPI(title="NeoMarket Moderation Service")


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return JSONResponse(status_code=exc.status_code, content={"code": exc.code, "message": exc.message})


app.include_router(approve.router, prefix="/api/v1")
app.include_router(decline.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1")
app.include_router(reasons.router, prefix="/api/v1")
