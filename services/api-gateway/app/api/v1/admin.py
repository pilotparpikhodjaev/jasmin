"""
Admin endpoints - for operator and system management
POST /api/admin/operators - Create operator
GET /api/admin/operators - List operators
PUT /api/admin/operators/{id} - Update operator
DELETE /api/admin/operators/{id} - Delete operator
GET /api/admin/operators/{id}/health - Get operator health
POST /api/admin/operators/{id}/connect - Connect operator
POST /api/admin/operators/{id}/disconnect - Disconnect operator
POST /api/admin/templates/{id}/moderate - Moderate template
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from uuid import UUID

from ...models.operator import (
    OperatorCreate,
    OperatorUpdate,
    OperatorResponse,
    OperatorListResponse,
    OperatorHealthMetrics,
    OperatorStatsResponse,
)
from ...models.template import TemplateDecision, TemplateResponse
from ...dependencies import get_current_user, get_operator_service, get_billing_client
from ...services.operator_service import OperatorService
from ...clients import BillingClient

router = APIRouter()


def require_admin(current_user: dict = Depends(get_current_user)):
    """Dependency to require admin role"""
    if current_user["account_type"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


@router.post("/operators", response_model=OperatorResponse, status_code=status.HTTP_201_CREATED)
async def create_operator(
    request: OperatorCreate,
    current_user: dict = Depends(require_admin),
    operator_service: OperatorService = Depends(get_operator_service),
):
    """
    Create new SMPP operator connection
    
    Example:
    ```json
    {
        "name": "Ucell Uzbekistan",
        "code": "UZ_UCELL",
        "country": "UZ",
        "mcc": "434",
        "mnc": "05",
        "price_per_sms": 50.00,
        "currency": "UZS",
        "smpp_config": {
            "host": "smpp.ucell.uz",
            "port": 2775,
            "system_id": "username",
            "password": "password",
            "bind_mode": "transceiver",
            "submit_sm_throughput": 100
        },
        "priority": 100,
        "weight": 100,
        "status": "active"
    }
    ```
    """
    try:
        operator = await operator_service.create_operator(request)
        return operator
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create operator: {str(e)}",
        )


@router.get("/operators", response_model=OperatorListResponse)
async def list_operators(
    status: Optional[str] = Query(None, description="Filter by status"),
    country: Optional[str] = Query(None, description="Filter by country"),
    current_user: dict = Depends(require_admin),
    operator_service: OperatorService = Depends(get_operator_service),
):
    """
    List all operators with optional filters
    """
    try:
        operators = await operator_service.list_operators(
            status=status,
            country=country,
        )
        
        return OperatorListResponse(
            total=len(operators),
            operators=operators,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list operators: {str(e)}",
        )


@router.get("/operators/{operator_id}", response_model=OperatorResponse)
async def get_operator(
    operator_id: str,
    current_user: dict = Depends(require_admin),
    operator_service: OperatorService = Depends(get_operator_service),
):
    """
    Get operator by ID
    """
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get operator: {str(e)}",
        )


@router.put("/operators/{operator_id}", response_model=OperatorResponse)
async def update_operator(
    operator_id: str,
    request: OperatorUpdate,
    current_user: dict = Depends(require_admin),
    operator_service: OperatorService = Depends(get_operator_service),
):
    """
    Update operator configuration
    """
    try:
        operator = await operator_service.update_operator(operator_id, request)
        return operator
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update operator: {str(e)}",
        )


@router.delete("/operators/{operator_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_operator(
    operator_id: str,
    current_user: dict = Depends(require_admin),
    operator_service: OperatorService = Depends(get_operator_service),
):
    """
    Delete operator (will disconnect if connected)
    """
    try:
        await operator_service.delete_operator(operator_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete operator: {str(e)}",
        )


@router.get("/operators/{operator_id}/health", response_model=OperatorHealthMetrics)
async def get_operator_health(
    operator_id: str,
    current_user: dict = Depends(require_admin),
    operator_service: OperatorService = Depends(get_operator_service),
):
    """
    Get operator health metrics
    """
    try:
        health = await operator_service.get_operator_health(operator_id)
        return health
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get operator health: {str(e)}",
        )


@router.post("/operators/{operator_id}/connect")
async def connect_operator(
    operator_id: str,
    current_user: dict = Depends(require_admin),
    operator_service: OperatorService = Depends(get_operator_service),
):
    """
    Connect operator (establish SMPP connection)
    """
    try:
        result = await operator_service.connect_operator(operator_id)
        return {"message": "Operator connection initiated", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect operator: {str(e)}",
        )


@router.post("/operators/{operator_id}/disconnect")
async def disconnect_operator(
    operator_id: str,
    current_user: dict = Depends(require_admin),
    operator_service: OperatorService = Depends(get_operator_service),
):
    """
    Disconnect operator (close SMPP connection)
    """
    try:
        result = await operator_service.disconnect_operator(operator_id)
        return {"message": "Operator disconnected", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect operator: {str(e)}",
        )


@router.get("/operators/{operator_id}/stats", response_model=OperatorStatsResponse)
async def get_operator_stats(
    operator_id: str,
    start_date: str = Query(..., description="Start date (ISO format)"),
    end_date: str = Query(..., description="End date (ISO format)"),
    current_user: dict = Depends(require_admin),
    operator_service: OperatorService = Depends(get_operator_service),
):
    """
    Get operator statistics for a period
    """
    try:
        stats = await operator_service.get_operator_stats(
            operator_id=operator_id,
            start_date=start_date,
            end_date=end_date,
        )
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get operator stats: {str(e)}",
        )


@router.post("/templates/{template_id}/moderate", response_model=TemplateResponse)
async def moderate_template(
    template_id: UUID,
    decision: TemplateDecision,
    current_user: dict = Depends(require_admin),
    billing_client: BillingClient = Depends(get_billing_client),
):
    """
    Moderate template (approve or reject)
    
    Example:
    ```json
    {
        "status": "approved",
        "comment": "Template approved for use"
    }
    ```
    """
    try:
        template = await billing_client.moderate_template(
            template_id=template_id,
            status=decision.status.value,
            comment=decision.comment,
        )
        
        return TemplateResponse(**template)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to moderate template: {str(e)}",
        )
