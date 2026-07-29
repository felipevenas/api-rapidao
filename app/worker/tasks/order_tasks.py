from app.worker.core.celery_app import celery_app
import logging

logger = logging.getLogger("celery_worker")


@celery_app.task(name="app.worker.tasks.order_tasks.expire_stale_orders")
def expire_stale_orders():
    """ Tarefa periódica para expirar pedidos que ficaram travados em status pendente """
    logger.info("Executando verificação de expiração de pedidos pendentes...")
    # Lógica de expiração será integrada ao domínio de orders
    return {"status": "success", "expired_orders_count": 0}
