from fastapi import FastAPI

app = FastAPI(title="College Event Registration API")


@app.get("/health")
def health_check():
    return {"status": "success", "message": "API is running"}