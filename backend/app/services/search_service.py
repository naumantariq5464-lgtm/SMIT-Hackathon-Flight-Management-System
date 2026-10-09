from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import select, and_, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.flight import Flight, FlightStatus
from app.models.fare_rule import FareRule
from app.models.seat import SeatClass
from app.schemas.flight import FlightSearchResult, FlightFareOption
from app.services.fare_service import FareService


class SearchService:
    @staticmethod
    async def search_flights(
        db: AsyncSession,
        origin: str,
        destination: str,
        flight_date: Optional[date] = None,
        passenger_count: int = 1,
        seat_class: Optional[SeatClass] = None,
    ) -> List[FlightSearchResult]:
        """Search flights with current available inventory and fare options."""
        query = select(Flight).where(
            Flight.origin.ilike(origin.strip()),
            Flight.destination.ilike(destination.strip()),
            Flight.status.in_([FlightStatus.SCHEDULED, FlightStatus.DELAYED]),
        )

        if flight_date:
            start_dt = datetime(flight_date.year, flight_date.month, flight_date.day, 0, 0, 0)
            end_dt = datetime(flight_date.year, flight_date.month, flight_date.day, 23, 59, 59, 999999)
            query = query.where(
                Flight.departure_datetime >= start_dt,
                Flight.departure_datetime <= end_dt,
            )

        query = query.order_by(Flight.departure_datetime.asc())
        result = await db.execute(query)
        flights = list(result.scalars().all())

        # Fetch fare rules
        fare_rules = await FareService.list_fare_rules(db)

        results: List[FlightSearchResult] = []
        for flight in flights:
            avail_first = max(0, flight.first_seats - flight.booked_first)
            avail_business = max(0, flight.business_seats - flight.booked_business)
            avail_economy = max(0, flight.economy_seats - flight.booked_economy)

            # Filter by class and passenger count if requested
            if seat_class == SeatClass.FIRST and avail_first < passenger_count:
                continue
            if seat_class == SeatClass.BUSINESS and avail_business < passenger_count:
                continue
            if seat_class == SeatClass.ECONOMY and avail_economy < passenger_count:
                continue

            # Check if any class has sufficient capacity
            has_capacity = (
                avail_first >= passenger_count
                or avail_business >= passenger_count
                or avail_economy >= passenger_count
            )
            if not has_capacity:
                continue

            # Calculate duration
            duration = int((flight.arrival_datetime - flight.departure_datetime).total_seconds() / 60)

            # Build available fare options
            fare_options: List[FlightFareOption] = []
            for rule in fare_rules:
                if seat_class and rule.seat_class != seat_class:
                    continue
                # Check class capacity for this rule
                if rule.seat_class == SeatClass.FIRST and avail_first < passenger_count:
                    continue
                if rule.seat_class == SeatClass.BUSINESS and avail_business < passenger_count:
                    continue
                if rule.seat_class == SeatClass.ECONOMY and avail_economy < passenger_count:
                    continue

                calculated_price = FareService.calculate_fare_price(flight.base_price, rule)
                fare_options.append(
                    FlightFareOption(
                        fare_rule_id=rule.id,
                        fare_name=rule.name,
                        fare_type=rule.fare_type.value,
                        seat_class=rule.seat_class,
                        price=calculated_price,
                        currency=flight.currency,
                        is_refundable=rule.is_refundable,
                        seat_selection_allowed=rule.seat_selection_allowed,
                        change_allowed=rule.change_allowed,
                        baggage_allowance_kg=rule.baggage_allowance_kg,
                    )
                )

            results.append(
                FlightSearchResult(
                    flight_id=flight.id,
                    flight_number=flight.flight_number,
                    origin=flight.origin,
                    destination=flight.destination,
                    departure_datetime=flight.departure_datetime,
                    arrival_datetime=flight.arrival_datetime,
                    duration_minutes=duration,
                    status=flight.status,
                    available_first=avail_first,
                    available_business=avail_business,
                    available_economy=avail_economy,
                    fare_options=fare_options,
                )
            )

        return results

    @staticmethod
    async def search_itineraries(
        db: AsyncSession,
        origin: str,
        destination: str,
        flight_date: Optional[date] = None,
        passenger_count: int = 1,
        seat_class: Optional[SeatClass] = None,
    ) -> List[FlightItineraryResult]:
        from decimal import Decimal
        from app.schemas.flight import FlightItineraryResult

        # Get all valid flights for the given day/timeframe (or all upcoming)
        query = select(Flight).where(
            Flight.status.in_([FlightStatus.SCHEDULED, FlightStatus.DELAYED])
        )
        if flight_date:
            start_dt = datetime(flight_date.year, flight_date.month, flight_date.day, 0, 0, 0)
            end_dt = datetime(flight_date.year, flight_date.month, flight_date.day, 23, 59, 59, 999999)
            query = query.where(Flight.departure_datetime >= start_dt, Flight.departure_datetime <= end_dt)

        query = query.order_by(Flight.departure_datetime.asc())
        all_flights = list((await db.execute(query)).scalars().all())

        # First, run the normal search_flights to get all processed FlightSearchResults
        all_results = await SearchService.search_flights(
            db=db, origin="", destination="", flight_date=flight_date, passenger_count=passenger_count, seat_class=seat_class
        )
        
        # Build graph/map for easy lookup
        from collections import defaultdict
        origin_map = defaultdict(list)
        for res in all_results:
            origin_map[res.origin.lower()].append(res)

        itineraries: List[FlightItineraryResult] = []

        # 1. Find Direct Flights
        for res in origin_map[origin.lower()]:
            if res.destination.lower() == destination.lower():
                # Get minimum base price for this flight
                # We can approximate total_price_base from fare_options
                min_price = min([f.price for f in res.fare_options]) if res.fare_options else Decimal("0")
                itineraries.append(
                    FlightItineraryResult(
                        flights=[res],
                        total_duration_minutes=res.duration_minutes,
                        total_price_base=min_price
                    )
                )

        # 2. Find 1-stop Connections
        for leg1 in origin_map[origin.lower()]:
            if leg1.destination.lower() == destination.lower():
                continue # Already handled

            for leg2 in origin_map[leg1.destination.lower()]:
                if leg2.destination.lower() == destination.lower():
                    # Check connection time (min 45 mins, max 12 hours)
                    layover_mins = int((leg2.departure_datetime - leg1.arrival_datetime).total_seconds() / 60)
                    if 45 <= layover_mins <= 720:
                        min_price1 = min([f.price for f in leg1.fare_options]) if leg1.fare_options else Decimal("0")
                        min_price2 = min([f.price for f in leg2.fare_options]) if leg2.fare_options else Decimal("0")
                        total_dur = leg1.duration_minutes + layover_mins + leg2.duration_minutes

                        itineraries.append(
                            FlightItineraryResult(
                                flights=[leg1, leg2],
                                total_duration_minutes=total_dur,
                                total_price_base=min_price1 + min_price2
                            )
                        )

        # Sort by total duration
        itineraries.sort(key=lambda x: x.total_duration_minutes)
        return itineraries
