from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models import Account, Tariff, Operator, Transaction
from ..schemas_payment import (
    OperatorRate,
    PaymentInitiateRequest,
    PaymentInitiateResponse,
    PaymentProvider,
    PaymentStatus,
    RateUpdateRequest,
    ClickCallbackRequest,
    ClickCallbackResponse,
    PaymeCallbackRequest,
    PaymeCallbackResponse,
)
# In a real app, we would inject payment service logic here.
# For now, we will mock the payment provider interactions.

router = APIRouter()

# --- SMS Rate Configuration ---

@router.get("/rates", response_model=List[OperatorRate])
async def list_rates(
    account_id: Optional[UUID] = None,
    session: AsyncSession = Depends(get_session),
):
    """List SMS rates for operators. If account_id provided, returns account-specific overrides."""
    # For simplicity, we assume base rates are stored in the Operator table or a default Tariff
    # Here we query Operators directly and join with Tariff if needed.
    # This is a simplified implementation focusing on the requirement.
    
    query = select(Operator)
    result = await session.execute(query)
    operators = result.scalars().all()
    
    rates = []
    for op in operators:
        # Default logic: use operator price or a standard default
        price = op.price_per_sms if op.price_per_sms is not None else Decimal("50.00")
        rates.append(OperatorRate(
            operator_id=op.id,
            operator_name=op.name,
            price=price,
            currency="UZS", # Default for Uzbekistan
            mcc=op.mcc,
            mnc=op.mnc
        ))
    return rates


@router.put("/rates/{operator_id}", response_model=OperatorRate)
async def update_rate(
    operator_id: int,
    rate_update: RateUpdateRequest,
    session: AsyncSession = Depends(get_session),
):
    """Update base rate for an operator."""
    query = select(Operator).where(Operator.id == operator_id)
    result = await session.execute(query)
    operator = result.scalar_one_or_none()
    
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")
    
    operator.price_per_sms = rate_update.price
    await session.commit()
    await session.refresh(operator)
    
    return OperatorRate(
        operator_id=operator.id,
        operator_name=operator.name,
        price=operator.price_per_sms,
        currency="UZS",
        mcc=operator.mcc,
        mnc=operator.mnc
    )

# --- Payment Gateway Integration ---

@router.post("/payments/initiate", response_model=PaymentInitiateResponse)
async def initiate_payment(
    request: PaymentInitiateRequest,
    session: AsyncSession = Depends(get_session),
):
    """Initiate a payment with Click or Payme."""
    
    # Verify account exists
    query = select(Account).where(Account.id == request.account_id)
    result = await session.execute(query)
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    transaction_id = str(uuid.uuid4())
    
    # Create pending transaction record
    # In a real app, we would save this to DB with 'pending' status
    
    redirect_url = ""
    
    if request.provider == PaymentProvider.CLICK:
        # Click URL format: https://my.click.uz/services/pay?service_id={SERVICE_ID}&merchant_id={MERCHANT_ID}&amount={AMOUNT}&transaction_param={TRANS_ID}
        # Mock values
        service_id = "12345"
        merchant_id = "67890"
        redirect_url = f"https://my.click.uz/services/pay?service_id={service_id}&merchant_id={merchant_id}&amount={request.amount}&transaction_param={transaction_id}"
        
    elif request.provider == PaymentProvider.PAYME:
        # Payme uses a base64 encoded payload in the URL or a form POST
        # Mock URL
        merchant_id = "payme_merchant_id"
        redirect_url = f"https://checkout.paycom.uz/{merchant_id}" 
        # Payme typically requires a base64 string "m=..."
        
    return PaymentInitiateResponse(
        transaction_id=transaction_id,
        redirect_url=redirect_url,
        provider_transaction_id=None
    )


@router.post("/payments/click/callback", response_model=ClickCallbackResponse)
async def click_callback(
    payload: ClickCallbackRequest,
    session: AsyncSession = Depends(get_session),
):
    """Handle Click payment callback (Prepare and Complete)."""
    # Click sends 'action' = 0 for Prepare, 'action' = 1 for Complete
    
    action = payload.action
    
    if action == 0:
        # Prepare: Check if transaction can be performed (e.g. user exists)
        # Return success code 0
        return ClickCallbackResponse(
            click_trans_id=payload.click_trans_id,
            merchant_trans_id=payload.merchant_trans_id,
            merchant_prepare_id=12345, # Mock ID
            error=0,
            error_note="Success"
        )
    elif action == 1:
        # Complete: Perform the actual charge/topup
        # Update user balance here
        return ClickCallbackResponse(
            click_trans_id=payload.click_trans_id,
            merchant_trans_id=payload.merchant_trans_id,
            merchant_confirm_id=12345, # Mock ID
            error=0,
            error_note="Success"
        )
        
    return ClickCallbackResponse(
        click_trans_id=payload.click_trans_id,
        merchant_trans_id=payload.merchant_trans_id,
        error=-1,
        error_note="Unknown action"
    )

@router.post("/payments/payme/callback", response_model=PaymeCallbackResponse)
async def payme_callback(
    payload: PaymeCallbackRequest,
    session: AsyncSession = Depends(get_session),
):
    """Handle Payme JSON-RPC callback."""
    method = payload.method
    
    # Payme methods: CheckPerformTransaction, CreateTransaction, PerformTransaction, etc.
    
    if method == "CheckPerformTransaction":
         return PaymeCallbackResponse(
             id=payload.id,
             result={"allow": True}
         )
    elif method == "CreateTransaction":
         return PaymeCallbackResponse(
             id=payload.id,
             result={
                 "create_time": 1234567890,
                 "transaction": "trans_id_123",
                 "state": 1
             }
         )
    elif method == "PerformTransaction":
        # Finalize payment
         return PaymeCallbackResponse(
             id=payload.id,
             result={
                 "transaction": "trans_id_123",
                 "perform_time": 1234567890,
                 "state": 2
             }
         )
         
    # Default error
    return PaymeCallbackResponse(
        id=payload.id,
        error={"code": -32601, "message": "Method not found"}
    )
