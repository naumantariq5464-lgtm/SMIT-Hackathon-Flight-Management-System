import hashlib
import json
import uuid
from typing import Any, Dict, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ConflictException, UnprocessableException
from app.models.idempotency import IdempotencyKey, IdempotencyStatus


class IdempotencyService:
    @staticmethod
    def compute_hash(payload: Any) -> str:
        """Compute SHA-256 hash of the request payload."""
        if payload is None:
            raw = ""
        elif isinstance(payload, (dict, list)):
            raw = json.dumps(payload, sort_keys=True, default=str)
        else:
            raw = str(payload)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    async def check_or_create(
        db: AsyncSession,
        user_id: uuid.UUID,
        endpoint: str,
        idempotency_key: Optional[str],
        payload: Any,
    ) -> Optional[IdempotencyKey]:
        """Check for existing idempotency key or create an in-progress record."""
        if not idempotency_key:
            return None

        request_hash = IdempotencyService.compute_hash(payload)

        query = select(IdempotencyKey).where(
            IdempotencyKey.user_id == user_id,
            IdempotencyKey.key == idempotency_key,
            IdempotencyKey.endpoint == endpoint,
        )
        result = await db.execute(query)
        existing = result.scalars().first()

        if existing:
            if existing.request_hash != request_hash:
                raise UnprocessableException(
                    "Idempotency key has already been used with a different request payload"
                )
            if existing.status == IdempotencyStatus.IN_PROGRESS:
                raise ConflictException(
                    "A request with this Idempotency-Key is currently in progress"
                )
            # Return existing record so the caller can return the cached response
            return existing

        # Create new IN_PROGRESS record
        new_record = IdempotencyKey(
            user_id=user_id,
            key=idempotency_key,
            endpoint=endpoint,
            request_hash=request_hash,
            status=IdempotencyStatus.IN_PROGRESS,
        )
        db.add(new_record)
        await db.flush()
        return new_record

    @staticmethod
    async def mark_completed(
        db: AsyncSession,
        idempotency_record: Optional[IdempotencyKey],
        response_code: int,
        response_data: Any,
    ) -> None:
        """Mark idempotency record as completed with response cache."""
        if not idempotency_record:
            return

        body_str = (
            json.dumps(response_data, default=str)
            if isinstance(response_data, (dict, list))
            else str(response_data)
        )
        idempotency_record.status = IdempotencyStatus.COMPLETED
        idempotency_record.response_code = response_code
        idempotency_record.response_body = body_str
        await db.flush()
