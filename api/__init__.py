from .customers import router as customers_router
from .connections import router as connections_router
from .accounts import router as accounts_router
from .transactions import router as transactions_router
from .sync import router as sync_router
from .dashboards import router as dashboards_router
from .status import router as status_router
from .callbacks import router as callbacks_router

__all__ = ["customers_router", "connections_router", "accounts_router", "transactions_router", "sync_router", "dashboards_router", "status_router", "callbacks_router"]
