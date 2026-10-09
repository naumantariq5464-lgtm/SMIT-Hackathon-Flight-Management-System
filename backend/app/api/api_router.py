from fastapi import APIRouter
from app.api.routes import (
    auth,
    users,
    search,
    seats,
    flights,
    price_holds,
    bookings,
    cancellations,
    refunds,
    travel_credits,
    waitlist,
    admin,
    chat,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(search.router)
api_router.include_router(seats.router)
api_router.include_router(flights.router)
api_router.include_router(price_holds.router)
api_router.include_router(bookings.router)
api_router.include_router(cancellations.router)
api_router.include_router(refunds.router)
api_router.include_router(travel_credits.router)
api_router.include_router(waitlist.router)
api_router.include_router(admin.router)
api_router.include_router(chat.router)
