"""
SMS endpoints - matching Eskiz.uz API
POST /api/message/sms/send - Send single SMS
POST /api/message/sms/send-batch - Send batch SMS
POST /api/message/sms/send-global - Send international SMS
POST /api/message/sms/get-user-messages - Get message history
POST /api/message/sms/get-user-messages-by-dispatch - Get messages by dispatch
POST /api/message/sms/get-dispatch-status - Get dispatch status
POST /api/message/sms/normalizer - Normalize SMS
GET /api/message/sms/check - Check SMS
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional

from ...models.sms import (
    SMSSendRequest,
    SMSBatchRequest,
    SMSGlobalRequest,
    SMSResponse,
    SMSBatchResponse,
    MessageHistoryRequest,
    MessageHistoryResponse,
    DispatchMessagesRequest,
    DispatchStatusResponse,
    SMSNormalizerRequest,
    SMSNormalizerResponse,
    SMSCheckRequest,
    SMSCheckResponse,
    SMSStatusResponse,
)
from ...dependencies import get_current_user, get_sms_service, get_billing_client
from ...services.sms_service import SMSService
from ...clients import BillingClient

router = APIRouter()


@router.post("/send", response_model=SMSResponse, status_code=status.HTTP_200_OK)
async def send_sms(
    request: SMSSendRequest,
    current_user: dict = Depends(get_current_user),
    sms_service: SMSService = Depends(get_sms_service),
):
    """
    Send single SMS
    
    Example:
    ```json
    {
        "mobile_phone": "998901234567",
        "message": "Your OTP code is 123456",
        "from": "MyCompany",
        "callback_url": "https://example.com/dlr",
        "user_sms_id": "my-ref-123"
    }
    ```
    
    Response:
    ```json
    {
        "request_id": "uuid",
        "message_id": "jasmin-msg-id",
        "user_sms_id": "my-ref-123",
        "status": "ACCEPTED",
        "sms_count": 1,
        "price": 50.00,
        "currency": "UZS",
        "balance_after": 9950.00
    }
    ```
    """
    try:
        response = await sms_service.send_sms(
            request=request,
            account_id=current_user["account_id"],
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send SMS: {str(e)}",
        )


@router.post("/send-batch", response_model=SMSBatchResponse)
async def send_batch_sms(
    request: SMSBatchRequest,
    current_user: dict = Depends(get_current_user),
    sms_service: SMSService = Depends(get_sms_service),
):
    """
    Send batch SMS
    
    Example:
    ```json
    {
        "messages": [
            {
                "mobile_phone": "998901234567",
                "message": "Hello User 1",
                "user_sms_id": "ref-1"
            },
            {
                "mobile_phone": "998907654321",
                "message": "Hello User 2",
                "user_sms_id": "ref-2"
            }
        ],
        "from": "MyCompany",
        "dispatch_id": "batch-001",
        "callback_url": "https://example.com/dlr"
    }
    ```
    """
    try:
        response = await sms_service.send_batch(
            request=request,
            account_id=current_user["account_id"],
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send batch SMS: {str(e)}",
        )


@router.post("/send-global", response_model=SMSResponse)
async def send_global_sms(
    request: SMSGlobalRequest,
    current_user: dict = Depends(get_current_user),
    sms_service: SMSService = Depends(get_sms_service),
):
    """
    Send international SMS
    
    Example:
    ```json
    {
        "mobile_phone": "+1234567890",
        "message": "International message",
        "country_code": "US",
        "unicode": false,
        "from": "MyCompany",
        "callback_url": "https://example.com/dlr"
    }
    ```
    """
    # TODO: Implement international SMS
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="International SMS not yet implemented",
    )


@router.post("/get-user-messages", response_model=MessageHistoryResponse)
async def get_user_messages(
    request: MessageHistoryRequest,
    current_user: dict = Depends(get_current_user),
    billing_client: BillingClient = Depends(get_billing_client),
):
    """
    Get message history with filters
    
    Example:
    ```json
    {
        "start_date": "2024-01-01T00:00:00Z",
        "to_date": "2024-01-31T23:59:59Z",
        "page_size": 50,
        "count": 0,
        "status": "DELIVRD"
    }
    ```
    """
    try:
        messages = await billing_client.get_cdr_messages(
            account_id=current_user["account_id"],
            start_date=request.start_date,
            end_date=request.to_date,
            limit=request.page_size,
            offset=request.count,
            status=request.status,
            is_ad=request.is_ad,
        )
        
        return MessageHistoryResponse(
            total=messages["total"],
            messages=messages["items"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get messages: {str(e)}",
        )


@router.post("/get-user-messages-by-dispatch", response_model=MessageHistoryResponse)
async def get_messages_by_dispatch(
    request: DispatchMessagesRequest,
    current_user: dict = Depends(get_current_user),
    billing_client: BillingClient = Depends(get_billing_client),
):
    """
    Get messages by dispatch ID
    
    Example:
    ```json
    {
        "dispatch_id": "batch-001",
        "count": 0,
        "status": "DELIVRD"
    }
    ```
    """
    try:
        messages = await billing_client.get_cdr_by_dispatch(
            account_id=current_user["account_id"],
            dispatch_id=request.dispatch_id,
            offset=request.count,
            status=request.status,
            is_ad=request.is_ad,
        )
        
        return MessageHistoryResponse(
            total=messages["total"],
            messages=messages["items"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dispatch messages: {str(e)}",
        )


@router.post("/get-dispatch-status", response_model=DispatchStatusResponse)
async def get_dispatch_status(
    dispatch_id: str,
    current_user: dict = Depends(get_current_user),
    billing_client: BillingClient = Depends(get_billing_client),
):
    """
    Get dispatch status summary
    
    Query params:
    - dispatch_id: Dispatch identifier
    """
    try:
        status_data = await billing_client.get_dispatch_status(
            account_id=current_user["account_id"],
            dispatch_id=dispatch_id,
        )
        
        return DispatchStatusResponse(**status_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dispatch status: {str(e)}",
        )


@router.post("/normalizer", response_model=SMSNormalizerResponse)
async def normalize_sms(
    request: SMSNormalizerRequest,
    sms_service: SMSService = Depends(get_sms_service),
):
    """
    Normalize SMS to reduce special characters and cost
    
    Example:
    ```json
    {
        "message": "Hello "World" — this is a test…"
    }
    ```
    
    Response:
    ```json
    {
        "original_message": "Hello "World" — this is a test…",
        "normalized_message": "Hello \"World\" - this is a test...",
        "original_length": 35,
        "normalized_length": 35,
        "savings_percent": 0.0,
        "recommendations": ["Removed 3 special characters"]
    }
    ```
    """
    return sms_service.normalize_message(request.message)


@router.get("/check", response_model=SMSCheckResponse)
async def check_sms(
    message: str = Query(..., description="Message to check"),
    to: Optional[str] = Query(None, description="Phone number for operator-specific pricing"),
    current_user: dict = Depends(get_current_user),
    sms_service: SMSService = Depends(get_sms_service),
):
    """
    Check SMS for parts count, encoding, blacklist, and pricing
    
    Query params:
    - message: Message text
    - to: Optional phone number for operator-specific pricing
    
    Response:
    ```json
    {
        "message": "Test message",
        "length": 12,
        "parts_count": 1,
        "encoding": "GSM7",
        "is_blacklisted": false,
        "pricing": [
            {
                "operator": "Ucell",
                "price_per_sms": 50.00,
                "currency": "UZS"
            }
        ]
    }
    ```
    """
    try:
        response = await sms_service.check_message(
            message=message,
            to=to,
            account_id=current_user["account_id"],
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check SMS: {str(e)}",
        )


@router.get("/{message_id}", response_model=SMSStatusResponse)
async def get_message_status(
    message_id: str,
    current_user: dict = Depends(get_current_user),
    billing_client: BillingClient = Depends(get_billing_client),
):
    """
    Get message status by message_id
    
    Path params:
    - message_id: Message identifier
    """
    try:
        message = await billing_client.get_message_by_id(
            account_id=current_user["account_id"],
            message_id=message_id,
        )
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found",
            )
        
        return SMSStatusResponse(**message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get message status: {str(e)}",
        )

