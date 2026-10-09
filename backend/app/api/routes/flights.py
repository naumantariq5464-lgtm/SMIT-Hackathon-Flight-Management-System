import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.flight import FlightResponse
from app.services.flight_service import FlightService

router = APIRouter(prefix="/flights", tags=["Flights"])


@router.get(
    "/{flight_id}",
    response_model=FlightResponse,
    summary="Get flight details by ID",
)
async def get_flight(
    flight_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> FlightResponse:
    flight = await FlightService.get_flight_by_id(db, flight_id)
    avail_first = max(0, flight.first_seats - flight.booked_first)
    avail_business = max(0, flight.business_seats - flight.booked_business)
    avail_economy = max(0, flight.economy_seats - flight.booked_economy)

    res_dict = {
        "id": flight.id,
        "flight_number": flight.flight_number,
        "origin": flight.origin,
        "destination": flight.destination,
        "departure_datetime": flight.departure_datetime,
        "arrival_datetime": flight.arrival_datetime,
        "aircraft_id": flight.aircraft_id,
        "status": flight.status,
        "capacity": flight.capacity,
        "first_seats": flight.first_seats,
        "business_seats": flight.business_seats,
        "economy_seats": flight.economy_seats,
        "booked_first": flight.booked_first,
        "booked_business": flight.booked_business,
        "booked_economy": flight.booked_economy,
        "available_first": avail_first,
        "available_business": avail_business,
        "available_economy": avail_economy,
        "base_price": flight.base_price,
        "currency": flight.currency,
        "overbooking_policy": flight.overbooking_policy,
        "first_cutoff_hours": flight.first_cutoff_hours,
        "business_cutoff_hours": flight.business_cutoff_hours,
        "economy_cutoff_hours": flight.economy_cutoff_hours,
        "created_at": flight.created_at,
        "updated_at": flight.updated_at,
    }
    return FlightResponse.model_validate(res_dict)


@router.get(
    "/fare-rules/all",
    summary="List all fare rules for booking pricing",
)
async def get_all_fare_rules(
    db: AsyncSession = Depends(get_db),
):
    from app.services.fare_service import FareService
    from app.schemas.fare import FareRuleResponse
    rules = await FareService.list_fare_rules(db)
    return [FareRuleResponse.model_validate(r) for r in rules]
