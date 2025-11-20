from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

import httpx

from . import schemas
from .config import Settings
from .exceptions import BillingError, UpstreamError


class BillingClient:
    def __init__(self, settings: Settings, http_client: httpx.AsyncClient):
        self._base_url = settings.billing_url.rstrip("/")
        self._client = http_client
        self._settings = settings

    async def resolve_api_key(self, token: str) -> schemas.AuthContext:
        url = f"{self._base_url}/internal/api-keys/{token}"
        resp = await self._client.get(url, timeout=5)
        if resp.status_code != 200:
            raise BillingError(f"Billing service rejected API key: {resp.text}")
        data = resp.json()
        return schemas.AuthContext(**data)

    async def charge_message(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._base_url}/v1/charges"
        resp = await self._client.post(url, json=payload, timeout=5)
        if resp.status_code not in (200, 201):
            raise BillingError(f"Billing charge failed: {resp.text}")
        return resp.json()

    async def get_balance(self, account_id: str) -> dict[str, Any]:
        url = f"{self._base_url}/v1/accounts/{account_id}/balance"
        resp = await self._client.get(url, timeout=5)
        if resp.status_code != 200:
            raise BillingError(f"Failed to fetch balance: {resp.text}")
        return resp.json()

    async def get_message(self, message_id: str) -> dict[str, Any]:
        url = f"{self._base_url}/v1/messages/{message_id}"
        resp = await self._client.get(url, timeout=5)
        if resp.status_code != 200:
            raise BillingError(f"Message lookup failed: {resp.text}")
        return resp.json()

    async def authenticate_user(self, email: str, password: str) -> dict[str, Any]:
        """Authenticate user with email/password"""
        url = f"{self._base_url}/v1/auth/login"
        resp = await self._client.post(url, json={"email": email, "password": password}, timeout=5)
        if resp.status_code != 200:
            raise BillingError(f"Authentication failed: {resp.text}")
        return resp.json()

    async def get_account(self, account_id: uuid.UUID) -> dict[str, Any]:
        """Get account details"""
        url = f"{self._base_url}/v1/accounts/{account_id}"
        resp = await self._client.get(url, timeout=5)
        if resp.status_code != 200:
            raise BillingError(f"Failed to fetch account: {resp.text}")
        return resp.json()

    async def list_accounts(
        self,
        account_type: str | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        """List accounts with basic stats for admin dashboard."""
        url = f"{self._base_url}/v1/accounts/"
        params: dict[str, Any] = {}
        if account_type:
            params["type"] = account_type
        if status:
            params["status"] = status
        if search:
            params["search"] = search

        resp = await self._client.get(url, params=params or None, timeout=10)
        if resp.status_code != 200:
            raise BillingError(f"Failed to list accounts: {resp.text}")
        return resp.json()

    async def get_account_stats(self, account_id: uuid.UUID) -> dict[str, Any]:
        """Get account statistics"""
        url = f"{self._base_url}/v1/accounts/{account_id}/stats"
        resp = await self._client.get(url, timeout=5)
        if resp.status_code != 200:
            raise BillingError(f"Failed to fetch stats: {resp.text}")
        return resp.json()

    async def get_dashboard_overview(self) -> dict[str, Any]:
        """Get global dashboard statistics for admin"""
        url = f"{self._base_url}/internal/stats/overview"
        resp = await self._client.get(url, timeout=10)
        if resp.status_code != 200:
            raise BillingError(f"Failed to fetch dashboard stats: {resp.text}")
        return resp.json()


    async def check_balance(self, account_id: uuid.UUID, amount: Decimal) -> dict[str, Any]:
        """Check if account has sufficient balance"""
        url = f"{self._base_url}/v1/accounts/{account_id}/check-balance"
        resp = await self._client.post(url, json={"amount": float(amount)}, timeout=5)
        if resp.status_code != 200:
            raise BillingError(f"Balance check failed: {resp.text}")
        return resp.json()

    async def charge(self, account_id: uuid.UUID, amount: Decimal, message_id: str, request_id: uuid.UUID) -> dict[str, Any]:
        """Charge account for SMS"""
        url = f"{self._base_url}/v1/charges"
        payload = {
            "account_id": str(account_id),
            "amount": float(amount),
            "message_id": message_id,
            "request_id": str(request_id),
        }
        resp = await self._client.post(url, json=payload, timeout=5)
        if resp.status_code not in (200, 201):
            raise BillingError(f"Charge failed: {resp.text}")
        return resp.json()

    async def get_cdr_messages(
        self,
        account_id: uuid.UUID,
        start_date: str,
        end_date: str,
        limit: int = 50,
        offset: int = 0,
        status: str = None,
        is_ad: bool = None,
    ) -> dict[str, Any]:
        """Get CDR messages"""
        url = f"{self._base_url}/v1/cdr/messages"
        params = {
            "account_id": str(account_id),
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
            "offset": offset,
        }
        if status:
            params["status"] = status
        if is_ad is not None:
            params["is_ad"] = is_ad

        resp = await self._client.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            raise BillingError(f"Failed to fetch CDR: {resp.text}")
        return resp.json()

    async def get_cdr_by_dispatch(
        self,
        account_id: uuid.UUID,
        dispatch_id: str,
        offset: int = 0,
        status: str = None,
        is_ad: bool = None,
    ) -> dict[str, Any]:
        """Get CDR messages by dispatch ID"""
        url = f"{self._base_url}/v1/cdr/dispatch/{dispatch_id}"
        params = {
            "account_id": str(account_id),
            "offset": offset,
        }
        if status:
            params["status"] = status
        if is_ad is not None:
            params["is_ad"] = is_ad

        resp = await self._client.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            raise BillingError(f"Failed to fetch dispatch CDR: {resp.text}")
        return resp.json()

    async def get_dispatch_status(self, account_id: uuid.UUID, dispatch_id: str) -> dict[str, Any]:
        """Get dispatch status summary"""
        url = f"{self._base_url}/v1/cdr/dispatch/{dispatch_id}/status"
        params = {"account_id": str(account_id)}
        resp = await self._client.get(url, params=params, timeout=5)
        if resp.status_code != 200:
            raise BillingError(f"Failed to fetch dispatch status: {resp.text}")
        return resp.json()

    async def get_message_by_id(self, account_id: uuid.UUID, message_id: str) -> dict[str, Any]:
        """Get message by ID"""
        url = f"{self._base_url}/v1/messages/{message_id}"
        params = {"account_id": str(account_id)}
        resp = await self._client.get(url, params=params, timeout=5)
        if resp.status_code != 200:
            raise BillingError(f"Failed to fetch message: {resp.text}")
        return resp.json()

    async def get_account_nicknames(self, account_id: uuid.UUID) -> list[str]:
        """Get account sender IDs (nicknames)"""
        url = f"{self._base_url}/v1/accounts/{account_id}/nicknames"
        resp = await self._client.get(url, timeout=5)
        if resp.status_code != 200:
            raise BillingError(f"Failed to fetch nicknames: {resp.text}")
        return resp.json()

    async def get_monthly_totals(
        self,
        account_id: uuid.UUID,
        year: int,
        month: int,
        is_global: bool = False,
    ) -> dict[str, Any]:
        """Get monthly SMS totals"""
        url = f"{self._base_url}/v1/cdr/totals"
        params = {
            "account_id": str(account_id),
            "year": year,
            "month": month,
            "is_global": is_global,
        }
        resp = await self._client.get(url, params=params, timeout=5)
        if resp.status_code != 200:
            raise BillingError(f"Failed to fetch totals: {resp.text}")
        return resp.json()

    async def create_template(
        self,
        account_id: uuid.UUID,
        name: str,
        category: str,
        content: str,
        variables: list[str] = None,
        description: str = None,
    ) -> dict[str, Any]:
        """Create message template"""
        url = f"{self._base_url}/v1/templates"
        payload = {
            "account_id": str(account_id),
            "name": name,
            "category": category,
            "content": content,
            "variables": variables or [],
            "description": description,
        }
        resp = await self._client.post(url, json=payload, timeout=5)
        if resp.status_code not in (200, 201):
            raise BillingError(f"Failed to create template: {resp.text}")
        return resp.json()

    async def get_templates(
        self,
        account_id: uuid.UUID,
        status: str = None,
        category: str = None,
    ) -> list[dict[str, Any]]:
        """Get templates"""
        url = f"{self._base_url}/v1/templates"
        params = {"account_id": str(account_id)}
        if status:
            params["status"] = status
        if category:
            params["category"] = category

        resp = await self._client.get(url, params=params, timeout=5)
        if resp.status_code != 200:
            raise BillingError(f"Failed to fetch templates: {resp.text}")
        return resp.json()

    async def get_template(self, account_id: uuid.UUID, template_id: uuid.UUID) -> dict[str, Any]:
        """Get template by ID"""
        url = f"{self._base_url}/v1/templates/{template_id}"
        params = {"account_id": str(account_id)}
        resp = await self._client.get(url, params=params, timeout=5)
        if resp.status_code != 200:
            raise BillingError(f"Failed to fetch template: {resp.text}")
        return resp.json()

    async def update_template(self, account_id: uuid.UUID, template_id: uuid.UUID, **kwargs) -> dict[str, Any]:
        """Update template"""
        url = f"{self._base_url}/v1/templates/{template_id}"
        payload = {"account_id": str(account_id), **kwargs}
        resp = await self._client.put(url, json=payload, timeout=5)
        if resp.status_code != 200:
            raise BillingError(f"Failed to update template: {resp.text}")
        return resp.json()

    async def delete_template(self, account_id: uuid.UUID, template_id: uuid.UUID) -> None:
        """Delete template"""
        url = f"{self._base_url}/v1/templates/{template_id}"
        params = {"account_id": str(account_id)}
        resp = await self._client.delete(url, params=params, timeout=5)
        if resp.status_code != 204:
            raise BillingError(f"Failed to delete template: {resp.text}")

    async def moderate_template(self, template_id: uuid.UUID, status: str, comment: str = None) -> dict[str, Any]:
        """Moderate template (admin only)"""
        url = f"{self._base_url}/v1/templates/{template_id}/moderate"
        payload = {"status": status, "comment": comment}
        resp = await self._client.post(url, json=payload, timeout=5)
        if resp.status_code != 200:
            raise BillingError(f"Failed to moderate template: {resp.text}")
        return resp.json()

    async def create_operator(self, operator_data: dict[str, Any]) -> dict[str, Any]:
        """Create operator"""
        url = f"{self._base_url}/v1/operators"
        resp = await self._client.post(url, json=operator_data, timeout=5)
        if resp.status_code not in (200, 201):
            raise BillingError(f"Failed to create operator: {resp.text}")
        return resp.json()

    async def list_operators(self, status: str = None, country: str = None) -> list[dict[str, Any]]:
        """List operators"""
        url = f"{self._base_url}/v1/operators"
        params = {}
        if status:
            params["status"] = status
        if country:
            params["country"] = country

        resp = await self._client.get(url, params=params, timeout=5)
        if resp.status_code != 200:
            raise BillingError(f"Failed to list operators: {resp.text}")
        return resp.json()

    async def get_operator(self, operator_id: uuid.UUID) -> dict[str, Any]:
        """Get operator by ID"""
        url = f"{self._base_url}/v1/operators/{operator_id}"
        resp = await self._client.get(url, timeout=5)
        if resp.status_code != 200:
            raise BillingError(f"Failed to fetch operator: {resp.text}")
        return resp.json()

    async def update_operator(self, operator_id: uuid.UUID, update_data: dict[str, Any]) -> dict[str, Any]:
        """Update operator"""
        url = f"{self._base_url}/v1/operators/{operator_id}"
        resp = await self._client.put(url, json=update_data, timeout=5)
        if resp.status_code != 200:
            raise BillingError(f"Failed to update operator: {resp.text}")
        return resp.json()

    async def delete_operator(self, operator_id: uuid.UUID) -> None:
        """Delete operator"""
        url = f"{self._base_url}/v1/operators/{operator_id}"
        resp = await self._client.delete(url, timeout=5)
        if resp.status_code != 204:
            raise BillingError(f"Failed to delete operator: {resp.text}")

    async def get_operator_stats(
        self,
        operator_id: uuid.UUID,
        start_date: str,
        end_date: str,
    ) -> dict[str, Any]:
        """Get operator statistics"""
        url = f"{self._base_url}/v1/operators/{operator_id}/stats"
        params = {"start_date": start_date, "end_date": end_date}
        resp = await self._client.get(url, params=params, timeout=5)
        if resp.status_code != 200:
            raise BillingError(f"Failed to fetch operator stats: {resp.text}")
        return resp.json()

    async def update_message_status(self, message_id: str, payload: dict[str, Any]) -> None:
        url = f"{self._base_url}/v1/messages/{message_id}"
        resp = await self._client.patch(url, json=payload, timeout=5)
        if resp.status_code != 200:
            raise BillingError(f"Failed to update message status: {resp.text}")




class JasminHttpClient:
    """Client for Jasmin HTTP API"""

    def __init__(self, settings: Settings, http_client: httpx.AsyncClient):
        self._base_url = settings.jasmin_http_url.rstrip("/")
        self._jcli_url = settings.jasmin_jcli_url.rstrip("/") if hasattr(settings, 'jasmin_jcli_url') else None
        self._client = http_client
        self._username = settings.jasmin_user
        self._password = settings.jasmin_password

    async def send_sms(
        self,
        to: str,
        message: str,
        from_: str,
        dlr_url: str = None,
        user_sms_id: str = None,
    ) -> dict[str, Any]:
        """Send SMS via Jasmin HTTP API"""
        url = f"{self._base_url}/send"
        payload = {
            "to": to,
            "content": message,
            "from": from_,
            "username": self._username,
            "password": self._password,
        }

        if dlr_url:
            payload["dlr-url"] = dlr_url
            payload["dlr-level"] = 2  # Request delivery receipt

        resp = await self._client.post(url, json=payload, timeout=10)
        if resp.status_code != 200:
            raise UpstreamError(f"Jasmin HTTP API error ({resp.status_code}): {resp.text}")

        body = resp.text.strip()
        if body.startswith('Success "') and body.endswith('"'):
            message_id = body.split('"')[1]
            return {
                "message_id": message_id,
                "status": "ACCEPTED",
            }
        raise UpstreamError(f"Unexpected Jasmin response: {body}")

    async def get_balance(self, username: str) -> dict[str, Any]:
        """Get balance via Jasmin HTTP API"""
        url = f"{self._base_url}/balance"
        params = {
            "username": username,
            "password": self._password,
        }
        resp = await self._client.get(url, params=params, timeout=5)
        if resp.status_code != 200:
            raise UpstreamError(f"Jasmin balance API error: {resp.text}")

        return resp.json()

    async def execute_jcli_commands(self, commands: list[str]) -> dict[str, Any]:
        """
        Execute jCli commands via HTTP API (if available)

        This requires a custom HTTP wrapper around jCli telnet interface
        or direct telnet connection

        For now, this is a placeholder that would need implementation
        """
        if not self._jcli_url:
            raise NotImplementedError("jCli HTTP API not configured")

        url = f"{self._jcli_url}/execute"
        payload = {"commands": commands}

        resp = await self._client.post(url, json=payload, timeout=30)
        if resp.status_code != 200:
            raise UpstreamError(f"jCli API error: {resp.text}")

        return resp.json()


class RoutingClient:
    """Client for routing-service"""

    def __init__(self, settings: Settings, http_client: httpx.AsyncClient):
        self._base_url = settings.routing_service_url.rstrip("/") if hasattr(settings, 'routing_service_url') else None
        self._client = http_client

    async def get_route(self, phone: str, account_id: uuid.UUID, message_parts: int = 1) -> dict[str, Any]:
        """
        Get routing decision for phone number

        Returns:
            {
                "primary_connector_id": "smpp-beeline-uz",
                "backup_connector_ids": ["smpp-ucell-uz"],
                "cost_per_part": 50.00,
                "operator_name": "Beeline"
            }
        """
        if not self._base_url:
            # Fallback: return default route
            return {
                "primary_connector_id": "smpp-default",
                "backup_connector_ids": [],
                "cost_per_part": 50.0,
                "operator_name": "Default",
                "price_per_sms": 50.0,
                "currency": "UZS",
            }

        url = f"{self._base_url}/v1/routing/decision"
        payload = {
            "destination_msisdn": phone,
            "account_id": str(account_id),
            "message_parts": message_parts,
        }

        resp = await self._client.post(url, json=payload, timeout=5)
        if resp.status_code != 200:
            raise UpstreamError(f"Routing service error: {resp.text}")

        data = resp.json()
        # Add price_per_sms and currency for backward compatibility
        data["price_per_sms"] = data.get("cost_per_part", 50.0)
        data["currency"] = "UZS"
        return data

    async def get_operator_by_phone(self, phone: str) -> dict[str, Any]:
        """
        Get operator info by phone number

        Returns:
            {
                "phone": "+998901234567",
                "operator": "Beeline",
                "connector_id": "smpp-beeline-uz",
                "price": 50.00
            }
        """
        if not self._base_url:
            return None

        url = f"{self._base_url}/v1/operators/{phone}"

        resp = await self._client.get(url, timeout=5)
        if resp.status_code != 200:
            return None

        data = resp.json()
        # Transform to expected format
        return {
            "operator": data.get("operator"),
            "connector_id": data.get("connector_id"),
            "name": data.get("operator"),
            "price_per_sms": data.get("price", 50.0),
        }

    async def get_all_operators(self) -> list[dict[str, Any]]:
        """
        Get all active operators

        Returns list of operators from routing service
        """
        if not self._base_url:
            return []

        url = f"{self._base_url}/v1/operators"
        resp = await self._client.get(url, timeout=5)
        if resp.status_code != 200:
            raise UpstreamError(f"Routing service error: {resp.text}")

        data = resp.json()
        # Return operators list
        return data.get("operators", [])
