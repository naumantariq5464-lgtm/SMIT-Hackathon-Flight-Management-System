from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.seat import SeatClass
from app.schemas.flight import FlightSearchResult, FlightItineraryResult
from app.services.search_service import SearchService
from app.services.currency_service import CurrencyService

router = APIRouter(prefix="/flights", tags=["Search"])


@router.get(
    "/search",
    response_model=List[FlightSearchResult],
    summary="Search available flights with live inventory and fare options",
    description="Searches flights matching route, date, class, and passenger count with real-time seat availability. "
                "Optionally convert fare prices to a different display currency.",
)
async def search_flights(
    origin: str = Query(..., min_length=2, max_length=50, examples=["UK"]),
    destination: str = Query(..., min_length=2, max_length=50, examples=["Dubai"]),
    flight_date: Optional[date] = Query(None, alias="date", examples=["2026-10-15"]),
    passenger_count: int = Query(1, ge=1, le=9, examples=[1]),
    seat_class: Optional[SeatClass] = Query(None, examples=[SeatClass.ECONOMY]),
    display_currency: Optional[str] = Query(
        None, min_length=3, max_length=3,
        description="Convert all fare prices to this currency (e.g. EUR, GBP, PKR). Default: flight's native currency.",
        examples=["EUR"],
    ),
    db: AsyncSession = Depends(get_db),
) -> List[FlightSearchResult]:
    results = await SearchService.search_flights(
        db=db,
        origin=origin,
        destination=destination,
        flight_date=flight_date,
        passenger_count=passenger_count,
        seat_class=seat_class,
    )

    # Convert fare prices to display_currency if requested
    if display_currency:
        display_currency = display_currency.upper()
        for result in results:
            for fare in result.fare_options:
                fare.price = CurrencyService.convert(fare.price, fare.currency, display_currency)
                fare.currency = display_currency

    return results

@router.get(
    "/itineraries",
    response_model=List[FlightItineraryResult],
    summary="Search multi-leg flight itineraries",
    description="Searches for direct and 1-stop connecting flights.",
)
async def search_itineraries(
    origin: str = Query(..., min_length=2, max_length=50),
    destination: str = Query(..., min_length=2, max_length=50),
    flight_date: Optional[date] = Query(None, alias="date"),
    passenger_count: int = Query(1, ge=1, le=9),
    seat_class: Optional[SeatClass] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> List[FlightItineraryResult]:
    return await SearchService.search_itineraries(
        db=db,
        origin=origin,
        destination=destination,
        flight_date=flight_date,
        passenger_count=passenger_count,
        seat_class=seat_class,
    )
