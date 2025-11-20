"""
User endpoints - matching Eskiz.uz API
GET /api/user/get-limit - Get balance
GET /api/nick/me - Get sender IDs
POST /api/user/totals - Get monthly totals
POST /api/user/export-csv - Export CSV
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
import csv
import io
from datetime import datetime

from ...models.user import (
    BalanceResponse,
    NicknameResponse,
    TotalsRequest,
    TotalsResponse,
    ExportCSVRequest,
)
from ...dependencies import get_current_user, get_billing_client
from ...clients import BillingClient

router = APIRouter()


@router.get("/get-limit", response_model=BalanceResponse)
async def get_balance(
    current_user: dict = Depends(get_current_user),
    billing_client: BillingClient = Depends(get_billing_client),
):
    """
    Get current balance and credit limit
    Similar to Eskiz.uz /api/user/get-limit
    
    Response:
    ```json
    {
        "balance": 1000000.00,
        "currency": "UZS",
        "credit_limit": 0.00,
        "available_balance": 1000000.00
    }
    ```
    """
    try:
        account_data = await billing_client.get_account(current_user["account_id"])
        
        balance = account_data["balance"]
        credit_limit = account_data.get("credit_limit", 0)
        
        return BalanceResponse(
            balance=balance,
            currency=account_data["currency"],
            credit_limit=credit_limit,
            available_balance=balance + credit_limit,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get balance: {str(e)}",
        )


@router.get("/nick/me", response_model=NicknameResponse)
async def get_nicknames(
    current_user: dict = Depends(get_current_user),
    billing_client: BillingClient = Depends(get_billing_client),
):
    """
    Get list of sender IDs (nicknames) for current user
    Similar to Eskiz.uz /api/nick/me
    
    Response:
    ```json
    {
        "nicknames": ["MyCompany", "MyBrand", "OTP"]
    }
    ```
    """
    try:
        nicknames = await billing_client.get_account_nicknames(
            current_user["account_id"]
        )
        
        return NicknameResponse(nicknames=nicknames)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get nicknames: {str(e)}",
        )


@router.post("/totals", response_model=TotalsResponse)
async def get_monthly_totals(
    request: TotalsRequest,
    current_user: dict = Depends(get_current_user),
    billing_client: BillingClient = Depends(get_billing_client),
):
    """
    Get monthly SMS totals by status
    Similar to Eskiz.uz /api/user/totals
    
    Example:
    ```json
    {
        "year": 2024,
        "month": 1,
        "is_global": false
    }
    ```
    
    Response:
    ```json
    {
        "year": 2024,
        "month": 1,
        "total_messages": 5000,
        "total_price": 250000.00,
        "currency": "UZS",
        "by_status": [
            {"status": "DELIVRD", "count": 4800, "total_price": 240000.00},
            {"status": "UNDELIV", "count": 150, "total_price": 7500.00},
            {"status": "EXPIRED", "count": 50, "total_price": 2500.00}
        ]
    }
    ```
    """
    try:
        totals = await billing_client.get_monthly_totals(
            account_id=current_user["account_id"],
            year=request.year,
            month=request.month,
            is_global=request.is_global,
        )
        
        return TotalsResponse(**totals)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get totals: {str(e)}",
        )


@router.post("/export-csv")
async def export_csv(
    request: ExportCSVRequest,
    current_user: dict = Depends(get_current_user),
    billing_client: BillingClient = Depends(get_billing_client),
):
    """
    Export message history as CSV
    Similar to Eskiz.uz /api/user/export-csv
    
    Example:
    ```json
    {
        "start_date": "2024-01-01T00:00:00Z",
        "end_date": "2024-01-31T23:59:59Z",
        "status": "DELIVRD"
    }
    ```
    
    Returns: CSV file download
    """
    try:
        # Get messages
        messages = await billing_client.get_cdr_messages(
            account_id=current_user["account_id"],
            start_date=request.start_date,
            end_date=request.end_date,
            status=request.status,
            is_ad=request.is_ad,
            limit=100000,  # Large limit for export
            offset=0,
        )
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Request ID",
            "Message ID",
            "User SMS ID",
            "Phone Number",
            "Message",
            "Status",
            "Submit Time",
            "Delivery Time",
            "SMS Count",
            "Price",
            "Currency",
            "Operator",
            "Country",
            "Error Code",
        ])
        
        # Write data
        for msg in messages["items"]:
            writer.writerow([
                msg.get("request_id", ""),
                msg.get("message_id", ""),
                msg.get("user_sms_id", ""),
                msg.get("phone_number", ""),
                msg.get("message", ""),
                msg.get("status", ""),
                msg.get("submit_time", ""),
                msg.get("delivery_time", ""),
                msg.get("sms_count", 0),
                msg.get("price", 0),
                msg.get("currency", ""),
                msg.get("operator", ""),
                msg.get("country", ""),
                msg.get("error_code", ""),
            ])
        
        # Prepare response
        output.seek(0)
        
        filename = f"sms_export_{request.start_date.strftime('%Y%m%d')}_{request.end_date.strftime('%Y%m%d')}.csv"
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export CSV: {str(e)}",
        )

