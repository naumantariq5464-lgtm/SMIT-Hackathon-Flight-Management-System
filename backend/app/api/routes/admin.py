import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.role import RoleEnum
from app.models.user import User
from app.models.aircraft import Aircraft
from app.models.fare_rule import FareRule
from app.models.audit_log import AuditLog
from app.schemas.common import PaginatedResponse, MessageResponse
from app.schemas.aircraft import AircraftCreate, AircraftResponse
from app.schemas.flight import FlightCreate, FlightUpdate, FlightResponse, FlightCancelRequest
from app.schemas.seat import InventoryAdjustmentRequest
from app.schemas.fare import FareRuleCreate, FareRuleResponse
from app.schemas.audit_log import AuditLogResponse
from app.services.flight_service import FlightService
from app.services.fare_service import FareService

router = APIRouter(
    prefix="/admin",
    tags=["Admin & Operations"],
    dependencies=[Depends(require_role([RoleEnum.OPS_AGENT, RoleEnum.SUPER_ADMIN]))],
)


# ---------------- Flight Management ---------------- #

@router.post(
    "/flights",
    response_model=FlightResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new flight with seat layout and inventory",
    description="Validates that First + Business + Economy == Capacity, prevents duplicate flight numbers for date/route, and generates physical seat layout.",
)
async def create_flight(
    request: FlightCreate,
    current_user: User = Depends(require_role([RoleEnum.OPS_AGENT, RoleEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
) -> FlightResponse:
    flight = await FlightService.create_flight(db, current_user.id, request)
    avail_first = flight.first_seats - flight.booked_first
    avail_business = flight.business_seats - flight.booked_business
    avail_economy = flight.economy_seats - flight.booked_economy

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
    "/flights",
    response_model=List[FlightResponse],
    summary="List all flights for operations and admin portal",
)
async def list_all_flights_admin(
    db: AsyncSession = Depends(get_db),
) -> List[FlightResponse]:
    from app.models.flight import Flight
    from sqlalchemy.orm import selectinload
    res = await db.execute(
        select(Flight)
        .options(selectinload(Flight.aircraft))
        .order_by(Flight.departure_datetime.desc())
    )
    flights = res.scalars().all()
    results = []
    for f in flights:
        results.append(FlightResponse.model_validate({
            "id": f.id,
            "flight_number": f.flight_number,
            "origin": f.origin,
            "destination": f.destination,
            "departure_datetime": f.departure_datetime,
            "arrival_datetime": f.arrival_datetime,
            "aircraft_id": f.aircraft_id,
            "status": f.status,
            "capacity": f.capacity,
            "first_seats": f.first_seats,
            "business_seats": f.business_seats,
            "economy_seats": f.economy_seats,
            "booked_first": f.booked_first,
            "booked_business": f.booked_business,
            "booked_economy": f.booked_economy,
            "available_first": max(0, f.first_seats - f.booked_first),
            "available_business": max(0, f.business_seats - f.booked_business),
            "available_economy": max(0, f.economy_seats - f.booked_economy),
            "base_price": f.base_price,
            "currency": f.currency,
            "overbooking_policy": f.overbooking_policy,
            "first_cutoff_hours": f.first_cutoff_hours,
            "business_cutoff_hours": f.business_cutoff_hours,
            "economy_cutoff_hours": f.economy_cutoff_hours,
            "created_at": f.created_at,
            "updated_at": f.updated_at,
        }))
    return results


@router.patch(
    "/flights/{flight_id}",
    response_model=FlightResponse,
    summary="Edit flight schedule/details with booking impact analysis",
)
async def update_flight(
    flight_id: uuid.UUID,
    request: FlightUpdate,
    current_user: User = Depends(require_role([RoleEnum.OPS_AGENT, RoleEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
) -> FlightResponse:
    flight, affected = await FlightService.update_flight(db, current_user.id, flight_id, request)
    avail_first = flight.first_seats - flight.booked_first
    avail_business = flight.business_seats - flight.booked_business
    avail_economy = flight.economy_seats - flight.booked_economy

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


@router.patch(
    "/flights/{flight_id}/inventory",
    response_model=FlightResponse,
    summary="Safely adjust class seat inventory allocations",
    description="Adjusts class breakdown (First, Business, Economy). Rejects if proposed class capacity is lower than already booked seats.",
)
async def adjust_inventory(
    flight_id: uuid.UUID,
    request: InventoryAdjustmentRequest,
    current_user: User = Depends(require_role([RoleEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
) -> FlightResponse:
    flight = await FlightService.adjust_inventory_allocation(db, current_user.id, flight_id, request)
    avail_first = flight.first_seats - flight.booked_first
    avail_business = flight.business_seats - flight.booked_business
    avail_economy = flight.economy_seats - flight.booked_economy

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


@router.post(
    "/flights/{flight_id}/cancel",
    response_model=MessageResponse,
    summary="Cancel flight and trigger downstream resolution",
    description="Cancels flight, preserves booking records, and generates downstream refund or travel credit records for all affected passengers.",
)
async def cancel_flight(
    flight_id: uuid.UUID,
    request: FlightCancelRequest,
    current_user: User = Depends(require_role([RoleEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    flight, affected_count = await FlightService.cancel_flight(db, current_user.id, flight_id, request)
    return MessageResponse(
        message=f"Flight {flight.flight_number} successfully cancelled.",
        detail=f"{affected_count} bookings resolved via {request.default_resolution}.",
    )


# ---------------- Aircraft Management ---------------- #

@router.post(
    "/aircraft",
    response_model=AircraftResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create aircraft configuration",
)
async def create_aircraft(
    request: AircraftCreate,
    current_user: User = Depends(require_role([RoleEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
) -> AircraftResponse:
    aircraft = Aircraft(
        model=request.model,
        registration_number=request.registration_number.strip().upper(),
        total_capacity=request.total_capacity,
        first_seats=request.first_seats,
        business_seats=request.business_seats,
        economy_seats=request.economy_seats,
    )
    db.add(aircraft)
    await db.commit()
    await db.refresh(aircraft)
    return AircraftResponse.model_validate(aircraft)


@router.get(
    "/aircraft",
    response_model=List[AircraftResponse],
    summary="List all aircraft",
)
async def list_aircraft(
    db: AsyncSession = Depends(get_db),
) -> List[AircraftResponse]:
    res = await db.execute(select(Aircraft).order_by(Aircraft.created_at.desc()))
    return [AircraftResponse.model_validate(a) for a in res.scalars().all()]


# ---------------- Fare Rules Management ---------------- #

@router.post(
    "/fare-rules",
    response_model=FareRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new fare rule",
)
async def create_fare_rule(
    request: FareRuleCreate,
    current_user: User = Depends(require_role([RoleEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
) -> FareRuleResponse:
    rule = await FareService.create_fare_rule(db, request)
    return FareRuleResponse.model_validate(rule)


@router.get(
    "/fare-rules",
    response_model=List[FareRuleResponse],
    summary="List all fare rules",
)
async def list_fare_rules(
    db: AsyncSession = Depends(get_db),
) -> List[FareRuleResponse]:
    rules = await FareService.list_fare_rules(db)
    return [FareRuleResponse.model_validate(r) for r in rules]


# ---------------- Audit Logs ---------------- #

@router.get(
    "/audit-logs",
    response_model=PaginatedResponse[AuditLogResponse],
    summary="Query audit logs (Super Admin only)",
    dependencies=[Depends(require_role([RoleEnum.SUPER_ADMIN]))],
)
async def get_audit_logs(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[AuditLogResponse]:
    skip = (page - 1) * size
    total = await db.scalar(select(func.count(AuditLog.id))) or 0
    query = select(AuditLog).order_by(AuditLog.timestamp.desc()).offset(skip).limit(size)
    res = await db.execute(query)
    logs = list(res.scalars().all())
    pages = (total + size - 1) // size if size > 0 else 0
    return PaginatedResponse[AuditLogResponse](
        items=[AuditLogResponse.model_validate(l) for l in logs],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


# ---------------- Approval & Autonomy Boundaries ---------------- #

@router.get(
    "/pending-approvals",
    response_model=List[AuditLogResponse],
    summary="List all actions pending human approval (Super Admin only)",
    description="Returns audit log entries flagged as requiring approval but not yet approved or rejected.",
    dependencies=[Depends(require_role([RoleEnum.SUPER_ADMIN]))],
)
async def list_pending_approvals(
    db: AsyncSession = Depends(get_db),
) -> List[AuditLogResponse]:
    from app.models.audit_log import ApprovalStatus
    query = (
        select(AuditLog)
        .where(AuditLog.approval_status == ApprovalStatus.PENDING_APPROVAL)
        .order_by(AuditLog.timestamp.desc())
    )
    res = await db.execute(query)
    return [AuditLogResponse.model_validate(l) for l in res.scalars().all()]


@router.post(
    "/audit-logs/{audit_log_id}/approve",
    response_model=AuditLogResponse,
    summary="Approve a pending audit action",
    description="Super Admin approves a sensitive action (e.g., schedule change compensation, rebooking).",
    dependencies=[Depends(require_role([RoleEnum.SUPER_ADMIN]))],
)
async def approve_audit_action(
    audit_log_id: uuid.UUID,
    current_user: User = Depends(require_role([RoleEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
) -> AuditLogResponse:
    from app.services.audit_service import AuditService
    log_entry = await AuditService.approve_action(db, audit_log_id, current_user.id)
    await db.commit()
    return AuditLogResponse.model_validate(log_entry)


@router.post(
    "/audit-logs/{audit_log_id}/reject",
    response_model=AuditLogResponse,
    summary="Reject a pending audit action",
    description="Super Admin rejects a sensitive action.",
    dependencies=[Depends(require_role([RoleEnum.SUPER_ADMIN]))],
)
async def reject_audit_action(
    audit_log_id: uuid.UUID,
    current_user: User = Depends(require_role([RoleEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
) -> AuditLogResponse:
    from app.services.audit_service import AuditService
    log_entry = await AuditService.reject_action(db, audit_log_id, current_user.id)
    await db.commit()
    return AuditLogResponse.model_validate(log_entry)
