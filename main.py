from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.core.database import Base, engine
from app.api import auth, users, students, textbooks, transactions, damage_reports, found_reports

app = FastAPI(title="Textbook Management System", version="0.1.0")

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключение роутов
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(students.router, prefix="/api/students", tags=["students"])
app.include_router(textbooks.router, prefix="/api/textbooks", tags=["textbooks"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(damage_reports.router, prefix="/api/damage-reports", tags=["damage-reports"])
app.include_router(found_reports.router, prefix="/api/found-reports", tags=["found-reports"])

@app.get("/")
async def root():
    return {"message": "Textbook Management System API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)