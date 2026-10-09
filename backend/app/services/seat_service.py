import uuid
from typing import List, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.models.seat import Seat, SeatClass, SeatStatus
from app.models.flight import Flight
from app.schemas.seat import SeatMapResponse, SeatResponse


class SeatService:
    @staticmethod
    async def generate_flight_seats(
        db: AsyncSession,
        flight_id: uuid.UUID,
        first_seats: int,
        business_seats: int,
        economy_seats: int,
    ) -> List[Seat]:
        """Generate physical seat layout rows for a newly created flight."""
        seats: List[Seat] = []
        row_index = 1
        cols_4 = ["A", "B", "C", "D"]
        cols_6 = ["A", "B", "C", "D", "E", "F"]

        # 1. Generate First Class Seats (4 per row)
        f_count = 0
        while f_count < first_seats:
            for col in cols_4:
                if f_count >= first_seats:
                    break
                seats.append(
                    Seat(
                        flight_id=flight_id,
                        seat_number=f"{row_index}{col}",
                        seat_class=SeatClass.FIRST,
                        status=SeatStatus.AVAILABLE,
                    )
                )
                f_count += 1
            row_index += 1

        # 2. Generate Business Class Seats (4 per row)
        b_count = 0
        while b_count < business_seats:
            for col in cols_4:
                if b_count >= business_seats:
                    break
                seats.append(
                    Seat(
                        flight_id=flight_id,
                        seat_number=f"{row_index}{col}",
                        seat_class=SeatClass.BUSINESS,
                        status=SeatStatus.AVAILABLE,
                    )
                )
                b_count += 1
            row_index += 1

        # 3. Generate Economy Class Seats (6 per row)
        e_count = 0
        while e_count < economy_seats:
            for col in cols_6:
                if e_count >= economy_seats:
                    break
                seats.append(
                    Seat(
                        flight_id=flight_id,
                        seat_number=f"{row_index}{col}",
                        seat_class=SeatClass.ECONOMY,
                        status=SeatStatus.AVAILABLE,
                    )
                )
                e_count += 1
            row_index += 1

        db.add_all(seats)
        await db.flush()
        return seats

    @staticmethod
    async def get_flight_seat_map(db: AsyncSession, flight_id: uuid.UUID) -> SeatMapResponse:
        """Retrieve full seat map for a flight with status breakdown."""
        res_flight = await db.execute(select(Flight).where(Flight.id == flight_id))
        flight = res_flight.scalars().first()
        if not flight:
            raise NotFoundException(f"Flight {flight_id} not found")

        res_seats = await db.execute(
            select(Seat).where(Seat.flight_id == flight_id).order_by(Seat.seat_number.asc())
        )
        seats = list(res_seats.scalars().all())

        available_count = sum(1 for s in seats if s.status == SeatStatus.AVAILABLE)
        held_count = sum(1 for s in seats if s.status == SeatStatus.HELD)
        booked_count = sum(1 for s in seats if s.status == SeatStatus.BOOKED)
        blocked_count = sum(1 for s in seats if s.status == SeatStatus.BLOCKED)

        return SeatMapResponse(
            flight_id=flight.id,
            flight_number=flight.flight_number,
            total_seats=len(seats),
            available_seats=available_count,
            held_seats=held_count,
            booked_seats=booked_count,
            blocked_seats=blocked_count,
            seats=[SeatResponse.model_validate(s) for s in seats],
        )
