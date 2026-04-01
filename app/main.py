from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import inference
from app.routers import welcome, health, subnet

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description="FastAPI web app for interacting with BitTensor subnets",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(welcome.router)
    app.include_router(health.router)
    app.include_router(subnet.router, prefix=settings.API_V1_PREFIX)
    app.include_router(inference.router, prefix=settings.API_V1_PREFIX)

    @app.on_event("startup")
    async def startup_event():
        print(f"Starting {settings.APP_NAME} on {settings.HOST}:{settings.PORT}")
        print(f"BitTensor network: {settings.SUBTENSOR_NETWORK}")
        print(f"API docs available at /docs")

    @app.on_event("shutdown")
    async def shutdown_event():
        print("Shutting down...")

    return app

app = create_app()