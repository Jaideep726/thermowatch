from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ThermoWatch API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # fine for hackathon demo
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health():
    return {"status": "ThermoWatch backend is running"}
