from fastapi import FastAPI

app = FastAPI()

items: list[dict] = [
    {"id": 1, "name": "Pen"},
    {"id": 2, "name": "Notebook"},
    {"id": 3, "name": "Bag"},
]

@app.get("/items")
def get_items() -> list[dict]:
    return items