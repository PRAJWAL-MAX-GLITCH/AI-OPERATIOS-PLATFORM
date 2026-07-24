from fastapi import APIRouter
from app.api.v1 import (
    health, auth, users, projects, datasets, validation,
    preprocessing, training, evaluation, mlops, serving,
    deep_learning, rag, chat, agents, workflows, observability, monitoring
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(datasets.router, tags=["datasets"])
api_router.include_router(validation.router, tags=["validation"])
api_router.include_router(preprocessing.router, tags=["preprocessing"])
api_router.include_router(training.router, tags=["training"])
api_router.include_router(evaluation.router, tags=["evaluation"])
api_router.include_router(mlops.router, prefix="/mlops", tags=["mlops"])
api_router.include_router(serving.router, tags=["serving"])
api_router.include_router(deep_learning.router, tags=["deep-learning"])
api_router.include_router(rag.router, tags=["rag"])
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(agents.router, tags=["agents"])
api_router.include_router(workflows.router, tags=["workflows"])
api_router.include_router(observability.router, tags=["observability"])
api_router.include_router(monitoring.router, tags=["monitoring"])


