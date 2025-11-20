"""Public operators endpoints used by admin-web.

These endpoints are mounted under `/api/operators` and provide a slightly
simplified shape compared to the internal admin routes:

- GET    /api/operators         -> list operators (returns `Operator[]`)
- GET    /api/operators/{id}    -> get single operator
- POST   /api/operators         -> create operator
- PUT    /api/operators/{id}    -> update operator
- DELETE /api/operators/{id}    -> delete operator

All endpoints require an authenticated admin user.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from ...dependencies import get_current_user, get_operator_service
from ...models.operator import OperatorCreate, OperatorResponse, OperatorUpdate
from ...services.operator_service import OperatorService

router = APIRouter()


def require_admin(current_user: dict = Depends(get_current_user)):
    """Dependency to require admin role for operator management."""

    if current_user["account_type"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


@router.get("", response_model=list[OperatorResponse])
async def list_operators(
    filter_status: Optional[str] = Query(None, description="Filter by status", alias="status"),
    country: Optional[str] = Query(None, description="Filter by country"),
    current_user: dict = Depends(require_admin),
    operator_service: OperatorService = Depends(get_operator_service),
) -> list[OperatorResponse]:
    """List all operators.

    This is the endpoint used by the Next.js admin-web when rendering the
    Operators table.
    """

    try:
        operators = await operator_service.list_operators(
            status=filter_status,
            country=country,
        )
        return operators
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list operators: {exc}",
        )


@router.get("/{operator_id}", response_model=OperatorResponse)
async def get_operator(
    operator_id: str,
    current_user: dict = Depends(require_admin),
    operator_service: OperatorService = Depends(get_operator_service),
) -> OperatorResponse:
    """Get single operator by ID."""

    try:
        operator = await operator_service.get_operator(operator_id)
        if not operator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Operator not found",
            )
        return operator
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get operator: {exc}",
        )


@router.post("", response_model=OperatorResponse, status_code=status.HTTP_201_CREATED)
async def create_operator(
    request: OperatorCreate,
    current_user: dict = Depends(require_admin),
    operator_service: OperatorService = Depends(get_operator_service),
) -> OperatorResponse:
    """Create a new SMPP operator connection."""

    try:
        operator = await operator_service.create_operator(request)
        return operator
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create operator: {exc}",
        )


@router.put("/{operator_id}", response_model=OperatorResponse)
async def update_operator(
    operator_id: str,
    request: OperatorUpdate,
    current_user: dict = Depends(require_admin),
    operator_service: OperatorService = Depends(get_operator_service),
) -> OperatorResponse:
    """Update an existing SMPP operator."""

    try:
        operator = await operator_service.update_operator(operator_id, request)
        return operator
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update operator: {exc}",
        )


@router.delete("/{operator_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_operator(
    operator_id: str,
    current_user: dict = Depends(require_admin),
    operator_service: OperatorService = Depends(get_operator_service),
) -> None:
    """Delete an operator.

    If the operator is currently connected, the underlying service will
    disconnect it as part of the deletion process.
    """

    try:
        await operator_service.delete_operator(operator_id)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete operator: {exc}",
        )
