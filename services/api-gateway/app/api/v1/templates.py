"""
Template endpoints - matching Eskiz.uz API
POST /api/user/template - Create template
GET /api/user/templates - Get templates
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from uuid import UUID

from ...models.template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateListResponse,
    TemplateUsageRequest,
)
from ...models.sms import SMSResponse
from ...dependencies import get_current_user, get_billing_client, get_sms_service
from ...clients import BillingClient
from ...services.sms_service import SMSService

router = APIRouter()


@router.post("/template", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    request: TemplateCreate,
    current_user: dict = Depends(get_current_user),
    billing_client: BillingClient = Depends(get_billing_client),
):
    """
    Create new message template for moderation
    Similar to Eskiz.uz /api/user/template
    
    Example:
    ```json
    {
        "name": "OTP Template",
        "category": "otp",
        "content": "Your verification code is {code}. Valid for 5 minutes.",
        "variables": ["code"],
        "description": "OTP code template"
    }
    ```
    
    Response:
    ```json
    {
        "id": "uuid",
        "account_id": "uuid",
        "name": "OTP Template",
        "category": "otp",
        "content": "Your verification code is {code}. Valid for 5 minutes.",
        "variables": ["code"],
        "status": "pending",
        "created_at": "2024-01-01T00:00:00Z"
    }
    ```
    """
    try:
        template = await billing_client.create_template(
            account_id=current_user["account_id"],
            name=request.name,
            category=request.category.value,
            content=request.content,
            variables=request.variables,
            description=request.description,
        )
        
        return TemplateResponse(**template)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}",
        )


@router.get("/templates", response_model=TemplateListResponse)
async def get_templates(
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user: dict = Depends(get_current_user),
    billing_client: BillingClient = Depends(get_billing_client),
):
    """
    Get list of templates
    Similar to Eskiz.uz /api/user/templates
    
    Query params:
    - status: Filter by status (pending, approved, rejected)
    - category: Filter by category (otp, transactional, etc.)
    
    Response:
    ```json
    {
        "total": 5,
        "templates": [
            {
                "id": "uuid",
                "name": "OTP Template",
                "status": "approved",
                ...
            }
        ]
    }
    ```
    """
    try:
        templates = await billing_client.get_templates(
            account_id=current_user["account_id"],
            status=status,
            category=category,
        )
        
        return TemplateListResponse(
            total=len(templates),
            templates=templates,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get templates: {str(e)}",
        )


@router.get("/template/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: UUID,
    current_user: dict = Depends(get_current_user),
    billing_client: BillingClient = Depends(get_billing_client),
):
    """
    Get template by ID
    """
    try:
        template = await billing_client.get_template(
            account_id=current_user["account_id"],
            template_id=template_id,
        )
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found",
            )
        
        return TemplateResponse(**template)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get template: {str(e)}",
        )


@router.put("/template/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: UUID,
    request: TemplateUpdate,
    current_user: dict = Depends(get_current_user),
    billing_client: BillingClient = Depends(get_billing_client),
):
    """
    Update template (only if not approved)
    """
    try:
        template = await billing_client.update_template(
            account_id=current_user["account_id"],
            template_id=template_id,
            **request.model_dump(exclude_unset=True),
        )
        
        return TemplateResponse(**template)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update template: {str(e)}",
        )


@router.delete("/template/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    current_user: dict = Depends(get_current_user),
    billing_client: BillingClient = Depends(get_billing_client),
):
    """
    Delete template
    """
    try:
        await billing_client.delete_template(
            account_id=current_user["account_id"],
            template_id=template_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete template: {str(e)}",
        )


@router.post("/template/{template_id}/send", response_model=SMSResponse)
async def send_with_template(
    template_id: UUID,
    request: TemplateUsageRequest,
    current_user: dict = Depends(get_current_user),
    billing_client: BillingClient = Depends(get_billing_client),
    sms_service: SMSService = Depends(get_sms_service),
):
    """
    Send SMS using template
    
    Example:
    ```json
    {
        "template_id": "uuid",
        "to": "998901234567",
        "variables": {
            "code": "123456"
        },
        "callback_url": "https://example.com/dlr"
    }
    ```
    """
    try:
        # Get template
        template = await billing_client.get_template(
            account_id=current_user["account_id"],
            template_id=template_id,
        )
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found",
            )
        
        if template["status"] != "approved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Template is not approved",
            )
        
        # Replace variables in template
        message = template["content"]
        if request.variables:
            for key, value in request.variables.items():
                message = message.replace(f"{{{key}}}", value)
        
        # Send SMS
        from ...models.sms import SMSSendRequest
        
        sms_request = SMSSendRequest(
            mobile_phone=request.to,
            message=message,
            **{"from": template.get("sender_id", "Default")},
            callback_url=request.callback_url,
        )
        
        response = await sms_service.send_sms(
            request=sms_request,
            account_id=current_user["account_id"],
        )
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send with template: {str(e)}",
        )

