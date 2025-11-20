"""
SMS service - business logic for SMS operations
"""

import asyncio
import re
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from ..models.sms import (
    SMSSendRequest,
    SMSBatchRequest,
    SMSResponse,
    SMSBatchResponse,
    SMSNormalizerResponse,
    SMSCheckResponse,
    OperatorPricing,
)


class SMSService:
    """SMS business logic service"""
    
    def __init__(self, jasmin_client, billing_client, routing_client):
        self.jasmin_client = jasmin_client
        self.billing_client = billing_client
        self.routing_client = routing_client
    
    def calculate_sms_parts(self, message: str, encoding: str = "auto") -> tuple[int, str]:
        """
        Calculate number of SMS parts and encoding
        
        Returns: (parts_count, encoding)
        """
        # GSM 7-bit alphabet
        gsm7_basic = set(
            "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?"
            "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà"
        )
        gsm7_extended = set("^{}\\[~]|€")
        
        # Check if message can be encoded in GSM7
        can_use_gsm7 = True
        extended_chars = 0
        
        for char in message:
            if char not in gsm7_basic:
                if char in gsm7_extended:
                    extended_chars += 1
                else:
                    can_use_gsm7 = False
                    break
        
        if encoding == "auto":
            encoding = "GSM7" if can_use_gsm7 else "UCS2"
        
        # Calculate parts
        if encoding == "GSM7":
            # Extended chars count as 2
            effective_length = len(message) + extended_chars
            
            if effective_length <= 160:
                return 1, "GSM7"
            else:
                # Multipart: 153 chars per part
                return (effective_length + 152) // 153, "GSM7"
        else:
            # UCS2 (Unicode)
            if len(message) <= 70:
                return 1, "UCS2"
            else:
                # Multipart: 67 chars per part
                return (len(message) + 66) // 67, "UCS2"
    
    def normalize_message(self, message: str) -> SMSNormalizerResponse:
        """
        Normalize message to reduce special characters and cost
        Similar to Eskiz.uz /api/message/sms/normalizer
        """
        original_message = message
        original_length = len(message)
        
        # Normalization rules
        replacements = {
            '"': '"',
            '"': '"',
            ''': "'",
            ''': "'",
            '—': '-',
            '–': '-',
            '…': '...',
            '№': 'N',
            '°': ' ',
            '™': '(TM)',
            '©': '(C)',
            '®': '(R)',
        }
        
        normalized_message = message
        for old, new in replacements.items():
            normalized_message = normalized_message.replace(old, new)
        
        normalized_length = len(normalized_message)
        
        # Calculate savings
        original_parts, _ = self.calculate_sms_parts(original_message)
        normalized_parts, _ = self.calculate_sms_parts(normalized_message)
        
        savings_percent = 0.0
        if original_parts > normalized_parts:
            savings_percent = ((original_parts - normalized_parts) / original_parts) * 100
        
        # Generate recommendations
        recommendations = []
        if original_parts != normalized_parts:
            recommendations.append(
                f"Normalized message reduces SMS parts from {original_parts} to {normalized_parts}"
            )
        
        if len(normalized_message) < len(original_message):
            recommendations.append(
                f"Removed {len(original_message) - len(normalized_message)} special characters"
            )
        
        # Check for URLs
        if re.search(r'https?://', normalized_message):
            recommendations.append("Consider using URL shortener to reduce message length")
        
        # Check for repeated spaces
        if '  ' in normalized_message:
            recommendations.append("Remove extra spaces to reduce message length")
        
        return SMSNormalizerResponse(
            original_message=original_message,
            normalized_message=normalized_message,
            original_length=original_length,
            normalized_length=normalized_length,
            savings_percent=savings_percent,
            recommendations=recommendations,
        )
    
    async def check_message(
        self,
        message: str,
        to: Optional[str] = None,
        account_id: Optional[uuid.UUID] = None,
    ) -> SMSCheckResponse:
        """
        Check message for parts, encoding, blacklist, and pricing
        Similar to Eskiz.uz /api/message/sms/check
        """
        # Calculate parts and encoding
        parts_count, encoding = self.calculate_sms_parts(message)
        
        # Check blacklist (placeholder - implement actual blacklist check)
        is_blacklisted = False
        blacklist_reason = None
        
        # TODO: Implement blacklist check
        # blacklisted_words = await self.check_blacklist(message)
        # if blacklisted_words:
        #     is_blacklisted = True
        #     blacklist_reason = f"Contains prohibited words: {', '.join(blacklisted_words)}"
        
        # Get pricing per operator
        pricing = []
        
        if to:
            # Get operator from phone number
            operator_info = await self.routing_client.get_operator_by_phone(to)
            if operator_info:
                price = operator_info.get("price_per_sms", Decimal("0"))
                pricing.append(
                    OperatorPricing(
                        operator=operator_info["name"],
                        price_per_sms=price * parts_count,
                        currency=operator_info.get("currency", "UZS"),
                    )
                )
        else:
            # Get pricing for all operators
            operators = await self.routing_client.get_all_operators()
            for op in operators:
                pricing.append(
                    OperatorPricing(
                        operator=op["name"],
                        price_per_sms=op["price_per_sms"] * parts_count,
                        currency=op.get("currency", "UZS"),
                    )
                )
        
        return SMSCheckResponse(
            message=message,
            length=len(message),
            parts_count=parts_count,
            encoding=encoding,
            is_blacklisted=is_blacklisted,
            blacklist_reason=blacklist_reason,
            pricing=pricing,
        )
    
    async def send_sms(
        self,
        request: SMSSendRequest,
        account_id: uuid.UUID,
    ) -> SMSResponse:
        """
        Send single SMS
        """
        # Calculate parts
        parts_count, encoding = self.calculate_sms_parts(request.message)
        
        # Get routing decision
        route = await self.routing_client.get_route(
            phone=request.mobile_phone,
            account_id=account_id,
        )
        
        # Check balance
        total_price = route["price_per_sms"] * parts_count
        balance_check = await self.billing_client.check_balance(
            account_id=account_id,
            amount=total_price,
        )
        
        if not balance_check["sufficient"]:
            raise ValueError("Insufficient balance")
        
        # Generate request_id
        request_id = uuid.uuid4()
        
        # Send via Jasmin
        jasmin_response = await self.jasmin_client.send_sms(
            to=request.mobile_phone,
            message=request.message,
            from_=request.from_,
            dlr_url=request.callback_url,
            user_sms_id=request.user_sms_id,
        )
        
        # Charge account
        await self.billing_client.charge(
            account_id=account_id,
            amount=total_price,
            message_id=jasmin_response["message_id"],
            request_id=request_id,
        )
        
        # Get updated balance
        balance_after = await self.billing_client.get_balance(account_id)
        
        return SMSResponse(
            request_id=request_id,
            message_id=jasmin_response["message_id"],
            user_sms_id=request.user_sms_id,
            status="ACCEPTED",
            sms_count=parts_count,
            price=total_price,
            currency=route["currency"],
            balance_after=balance_after["balance"],
        )
    
    async def send_batch(
        self,
        request: SMSBatchRequest,
        account_id: uuid.UUID,
    ) -> SMSBatchResponse:
        """
        Send batch SMS with concurrent processing

        Process:
        1. Pre-validate all messages and calculate total cost
        2. Check balance (single transaction)
        3. Send messages in parallel (with concurrency limit)
        4. Charge individually for each successful send
        5. Return batch response with per-message status
        """
        # Generate dispatch ID
        dispatch_id = request.dispatch_id or str(uuid.uuid4())

        # Phase 1: Pre-validation and cost calculation
        total_cost = Decimal("0.00")
        message_costs = []

        for msg in request.messages:
            parts_count, encoding = self.calculate_sms_parts(msg.message)

            # Get routing decision (cached, so fast for same operator)
            route = await self.routing_client.get_route(
                phone=msg.mobile_phone,
                account_id=account_id,
            )

            msg_cost = route["price_per_sms"] * parts_count
            total_cost += msg_cost

            message_costs.append({
                "phone": msg.mobile_phone,
                "message": msg.message,
                "user_sms_id": msg.user_sms_id,
                "parts": parts_count,
                "encoding": encoding,
                "cost": msg_cost,
                "route": route,
            })

        # Phase 2: Check balance (bulk check before sending)
        balance_check = await self.billing_client.check_balance(
            account_id=account_id,
            amount=total_cost,
        )

        if not balance_check["sufficient"]:
            raise ValueError(
                f"Insufficient balance. Required: {total_cost}, "
                f"Available: {balance_check['available']}"
            )

        # Phase 3: Send messages concurrently (max 50 parallel)
        semaphore = asyncio.Semaphore(50)

        async def send_single_message(msg_data: dict) -> SMSResponse:
            """Send single message with error handling"""
            async with semaphore:
                request_id = uuid.uuid4()

                try:
                    # Send via Jasmin
                    jasmin_response = await self.jasmin_client.send_sms(
                        to=msg_data["phone"],
                        message=msg_data["message"],
                        from_=request.from_,
                        dlr_url=request.callback_url,
                        user_sms_id=msg_data["user_sms_id"],
                    )

                    # Charge account
                    await self.billing_client.charge(
                        account_id=account_id,
                        amount=msg_data["cost"],
                        message_id=jasmin_response["message_id"],
                        request_id=request_id,
                    )

                    return SMSResponse(
                        request_id=request_id,
                        message_id=jasmin_response["message_id"],
                        user_sms_id=msg_data["user_sms_id"],
                        status="ACCEPTED",
                        sms_count=msg_data["parts"],
                        price=msg_data["cost"],
                        currency=msg_data["route"]["currency"],
                        balance_after=Decimal("0.00"),  # Will be updated later
                    )

                except Exception as e:
                    # Return error response for this message
                    return SMSResponse(
                        request_id=request_id,
                        message_id="ERROR",
                        user_sms_id=msg_data["user_sms_id"],
                        status=f"REJECTED: {str(e)[:100]}",
                        sms_count=msg_data["parts"],
                        price=Decimal("0.00"),  # No charge for failed messages
                        currency=msg_data["route"]["currency"],
                        balance_after=Decimal("0.00"),
                    )

        # Send all messages in parallel
        results = await asyncio.gather(
            *[send_single_message(msg_data) for msg_data in message_costs],
            return_exceptions=False,
        )

        # Phase 4: Aggregate results
        accepted = sum(1 for r in results if r.status == "ACCEPTED")
        rejected = len(results) - accepted
        actual_cost = sum(r.price for r in results)

        # Get final balance
        balance_after = await self.billing_client.get_balance(account_id)

        # Update balance_after in all responses
        for result in results:
            result.balance_after = balance_after["balance"]

        return SMSBatchResponse(
            dispatch_id=dispatch_id,
            total_messages=len(request.messages),
            accepted=accepted,
            rejected=rejected,
            total_price=actual_cost,
            currency=message_costs[0]["route"]["currency"] if message_costs else "USD",
            balance_after=balance_after["balance"],
            messages=results,
        )

