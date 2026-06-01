from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.labs import router as labs_router
from app.api.v1.lab_templates import router as lab_templates_router
from app.api.v1.tickets import my_router as my_attempts_router
from app.api.v1.tickets import router as tickets_router
from app.api.v1.verification import my_router as my_verification_router
from app.api.v1.verification import router as verification_router
from app.api.v1.system import router as system_router
from app.api.v1.users import router as users_router

api_router = APIRouter()
api_router.include_router(system_router)
api_router.include_router(auth_router, prefix="/api/v1/auth")
api_router.include_router(users_router, prefix="/api/v1/users")
api_router.include_router(lab_templates_router, prefix="/api/v1/lab-templates")
api_router.include_router(labs_router, prefix="/api/v1/labs")
api_router.include_router(tickets_router, prefix="/api/v1/tickets")
api_router.include_router(my_attempts_router, prefix="/api/v1/my")
api_router.include_router(verification_router, prefix="/api/v1")
api_router.include_router(my_verification_router, prefix="/api/v1/my")
