from app.api.routes.chat import router as chat_router
from app.api.routes.customers import router as customers_router
from app.api.routes.health import router as health_router
from app.api.routes.knowledge import router as knowledge_router
from app.api.routes.metrics import router as metrics_router
from app.api.routes.product_chat import router as product_chat_router
from app.api.routes.queue import router as queue_router
from app.api.routes.seed import router as seed_router
from app.api.routes.tickets import router as tickets_router

__all__ = [
    "chat_router",
    "customers_router",
    "health_router",
    "knowledge_router",
    "metrics_router",
    "product_chat_router",
    "queue_router",
    "seed_router",
    "tickets_router",
]
