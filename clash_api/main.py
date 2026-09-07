from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict

from .routers import review, balance, cards

app = FastAPI(
    title="Clash Royale Analytics & Tactical Engine API",
    description="""
    API REST de alto rendimiento para analitica cuantitativa de Clash Royale:
    1. **Game Review & Blunder Detection**: Auditoria tactica de partidas jugada a jugada estilo Chess.com.
    2. **Game Balance & Patch Simulator**: Simulacion predictiva de parches de balance multi-carta y deteccion de dano colateral.
    3. **Autonomous Meta Radar**: Escaneo de salud del meta, Z-scores y watchlist de balance acotada por hard breakpoints.
    4. **Breakpoints & Card Stats**: Fichas tecnicas canonicas oficiales e interacciones de supervivencia frente a hechizos.
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Habilitar CORS para permitir consumo desde apps moviles (React Native/Expo) y web dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(review.router)
app.include_router(balance.router)
app.include_router(cards.router)

@app.get("/", tags=["Health"])
def health_check() -> Dict[str, str]:
    return {
        "status": "online",
        "engine": "Clash Royale Analytics & Physics Core v2.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }
