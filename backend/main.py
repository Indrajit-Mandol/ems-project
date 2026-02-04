from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import create_tables
from routes import auth, employees
from config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
    create_tables()
    print("Database tables created successfully")
    yield
    # Shutdown: Cleanup if needed
    print("Application shutdown")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(employees.router)

# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Welcome to Employee Management System API",
        "version": settings.VERSION,
        "docs": "/docs"
    }

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
