from fastapi import FastAPI

app = FastAPI(title="XPlain API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/meta")
def meta() -> dict[str, str]:
    return {
        "service": "xplain-api",
        "stage": "bootstrap",
        "message": "API scaffold is ready"
    }
