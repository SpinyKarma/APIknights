from fastapi import FastAPI

app = FastAPI()


@app.get("/api/", status_code=200)
async def root():
    return {"message": "Hello World"}
