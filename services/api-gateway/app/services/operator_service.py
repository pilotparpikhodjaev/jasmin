"""
Operator service - manages SMPP operator connections
"""

from datetime import datetime
from typing import Optional, List
from decimal import Decimal

from ..models.operator import (
    OperatorCreate,
    OperatorUpdate,
    OperatorResponse,
    OperatorHealthMetrics,
    OperatorStatsResponse,
)


class OperatorService:
    """
    Operator management service
    Handles dynamic SMPP operator connection management
    """
    
    def __init__(self, jasmin_client, billing_client, routing_client, redis):
        self.jasmin_client = jasmin_client
        self.billing_client = billing_client
        self.routing_client = routing_client
        self.redis = redis
    
    async def create_operator(self, request: OperatorCreate) -> OperatorResponse:
        """
        Create new operator and configure SMPP connection in Jasmin
        
        Steps:
        1. Store operator config in PostgreSQL (via billing-service)
        2. Create SMPP connector in Jasmin (via jCli or HTTP API)
        3. Configure routing rules
        4. Start health monitoring
        """
        # 1. Store in database
        operator_data = {
            "name": request.name,
            "code": request.code,
            "country": request.country,
            "mcc": request.mcc,
            "mnc": request.mnc,
            "price_per_sms": float(request.price_per_sms),
            "currency": request.currency,
            "priority": request.priority,
            "weight": request.weight,
            "status": request.status,
            "health_check_enabled": request.health_check_enabled,
            "health_check_interval": request.health_check_interval,
            "smpp_config": request.smpp_config.model_dump(),
            "metadata": request.metadata,
        }
        
        operator = await self.billing_client.create_operator(operator_data)
        operator_id = operator["id"]
        
        # 2. Create SMPP connector in Jasmin
        try:
            connector_id = await self._create_jasmin_connector(
                operator_id=operator_id,
                code=request.code,
                smpp_config=request.smpp_config,
            )
            
            # Update operator with connector_id
            await self.billing_client.update_operator(
                operator_id,
                {"jasmin_connector_id": connector_id}
            )
        except Exception as e:
            # Rollback: delete operator from database
            await self.billing_client.delete_operator(operator_id)
            raise ValueError(f"Failed to create Jasmin connector: {e}")
        
        # 3. Configure routing rules
        await self._configure_routing(operator_id, request)
        
        # 4. Start health monitoring if enabled
        if request.health_check_enabled:
            await self._start_health_monitoring(operator_id)
        
        # Return operator response
        return await self.get_operator(operator_id)
    
    async def _create_jasmin_connector(
        self,
        operator_id: str,
        code: str,
        smpp_config,
    ) -> str:
        """
        Create SMPP connector in Jasmin via jCli commands
        
        This uses Jasmin's telnet CLI (jCli) to create SMPP client connector
        
        Commands:
        smppccm -a
        cid <code>
        host <host>
        port <port>
        username <system_id>
        password <password>
        submit_throughput <throughput>
        ...
        ok
        """
        # Build jCli commands
        commands = [
            "smppccm -a",  # Add SMPP client connector
            f"cid {code}",
            f"host {smpp_config.host}",
            f"port {smpp_config.port}",
            f"username {smpp_config.system_id}",
            f"password {smpp_config.password}",
            f"submit_throughput {smpp_config.submit_sm_throughput}",
            f"bind {smpp_config.bind_mode}",
            "ok",
        ]
        
        # Execute via Jasmin client
        result = await self.jasmin_client.execute_jcli_commands(commands)
        
        if not result.get("success"):
            raise Exception(f"Failed to create connector: {result.get('error')}")
        
        return code  # Connector ID is the code
    
    async def _configure_routing(self, operator_id: str, request: OperatorCreate):
        """
        Configure routing rules for operator
        
        This creates:
        1. Filter for MCC/MNC matching
        2. Route to operator connector
        """
        # Store routing config in routing-service
        routing_config = {
            "operator_id": str(operator_id),
            "mcc": request.mcc,
            "mnc": request.mnc,
            "priority": request.priority,
            "weight": request.weight,
            "price_per_sms": float(request.price_per_sms),
        }
        
        await self.routing_client.add_operator_route(routing_config)
    
    async def _start_health_monitoring(self, operator_id: str):
        """
        Start health monitoring for operator
        
        This schedules periodic health checks
        """
        # Store in Redis for health check scheduler
        key = f"operator_health_check:{operator_id}"
        await self.redis.set(key, "enabled")
    
    async def list_operators(
        self,
        status: Optional[str] = None,
        country: Optional[str] = None,
    ) -> List[OperatorResponse]:
        """
        List all operators with filters
        """
        operators = await self.billing_client.list_operators(
            status=status,
            country=country,
        )
        
        # Enrich with health metrics
        result = []
        for op in operators:
            health = await self._get_cached_health(op["id"])
            config = op.get("smpp_config") or {}
            smpp_host = config.get("host", "")
            smpp_port = config.get("port", 0)
            smpp_system_id = config.get("system_id", "")
            smpp_bind_mode = config.get("bind_mode", "")
            submit_sm_throughput = config.get("submit_sm_throughput", 0)

            result.append(OperatorResponse(
                id=op["id"],
                name=op["name"],
                code=op["code"],
                country=op["country"],
                mcc=op["mcc"],
                mnc=op["mnc"],
                price_per_sms=op["price_per_sms"],
                currency=op["currency"],
                priority=op["priority"],
                weight=op["weight"],
                status=op["status"],
                health_check_enabled=op["health_check_enabled"],
                health_check_interval=op["health_check_interval"],
                created_at=op["created_at"],
                updated_at=op["updated_at"],
                smpp_host=smpp_host,
                smpp_port=smpp_port,
                smpp_system_id=smpp_system_id,
                smpp_bind_mode=smpp_bind_mode,
                submit_sm_throughput=submit_sm_throughput,
                health_metrics=health,
                metadata=op.get("metadata"),
            ))
        
        return result
    
    async def get_operator(self, operator_id: str) -> OperatorResponse:
        """
        Get operator by ID
        """
        op = await self.billing_client.get_operator(operator_id)
        
        if not op:
            return None
        
        health = await self._get_cached_health(operator_id)
        config = op.get("smpp_config") or {}
        smpp_host = config.get("host", "")
        smpp_port = config.get("port", 0)
        smpp_system_id = config.get("system_id", "")
        smpp_bind_mode = config.get("bind_mode", "")
        submit_sm_throughput = config.get("submit_sm_throughput", 0)
        
        return OperatorResponse(
            id=op["id"],
            name=op["name"],
            code=op["code"],
            country=op["country"],
            mcc=op["mcc"],
            mnc=op["mnc"],
            price_per_sms=op["price_per_sms"],
            currency=op["currency"],
            priority=op["priority"],
            weight=op["weight"],
            status=op["status"],
            health_check_enabled=op["health_check_enabled"],
            health_check_interval=op["health_check_interval"],
            created_at=op["created_at"],
            updated_at=op["updated_at"],
            smpp_host=smpp_host,
            smpp_port=smpp_port,
            smpp_system_id=smpp_system_id,
            smpp_bind_mode=smpp_bind_mode,
            submit_sm_throughput=submit_sm_throughput,
            health_metrics=health,
            metadata=op.get("metadata"),
        )
    
    async def update_operator(
        self,
        operator_id: str,
        request: OperatorUpdate,
    ) -> OperatorResponse:
        """
        Update operator configuration
        """
        # Update in database
        update_data = request.model_dump(exclude_unset=True)
        
        if "smpp_config" in update_data:
            update_data["smpp_config"] = update_data["smpp_config"].model_dump()
        
        await self.billing_client.update_operator(operator_id, update_data)
        
        # If SMPP config changed, update Jasmin connector
        if request.smpp_config:
            await self._update_jasmin_connector(operator_id, request.smpp_config)
        
        return await self.get_operator(operator_id)
    
    async def _update_jasmin_connector(self, operator_id: str, smpp_config):
        """
        Update SMPP connector in Jasmin
        """
        # Get operator to get connector ID
        op = await self.billing_client.get_operator(operator_id)
        connector_id = op.get("jasmin_connector_id") or op["code"]
        
        # Build update commands
        commands = [
            f"smppccm -u {connector_id}",
            f"host {smpp_config.host}",
            f"port {smpp_config.port}",
            f"username {smpp_config.system_id}",
            f"password {smpp_config.password}",
            f"submit_throughput {smpp_config.submit_sm_throughput}",
            "ok",
        ]
        
        await self.jasmin_client.execute_jcli_commands(commands)
    
    async def delete_operator(self, operator_id: str):
        """
        Delete operator (disconnect and remove)
        """
        # 1. Disconnect if connected
        await self.disconnect_operator(operator_id)
        
        # 2. Remove from Jasmin
        op = await self.billing_client.get_operator(operator_id)
        connector_id = op.get("jasmin_connector_id") or op["code"]
        
        commands = [f"smppccm -r {connector_id}"]
        await self.jasmin_client.execute_jcli_commands(commands)
        
        # 3. Remove from database
        await self.billing_client.delete_operator(operator_id)
    
    async def get_operator_health(self, operator_id: str) -> OperatorHealthMetrics:
        """
        Get real-time operator health metrics
        """
        # TODO: Implement actual health metrics collection from Jasmin
        # This should query Jasmin's metrics endpoint or Redis cache
        
        return OperatorHealthMetrics(
            operator_id=operator_id,
            operator_code="PLACEHOLDER",
            is_connected=True,
            last_connected_at=datetime.utcnow(),
            connection_uptime_seconds=3600,
            submit_sm_count=1000,
            submit_sm_resp_count=995,
            delivery_count=980,
            failure_count=15,
            submit_success_rate=99.5,
            delivery_rate=98.5,
            avg_submit_latency_ms=50.0,
            p95_submit_latency_ms=100.0,
            p99_submit_latency_ms=200.0,
            health_score=98.0,
            health_status="healthy",
            recent_errors=[],
            measured_at=datetime.utcnow(),
        )
    
    async def _get_cached_health(self, operator_id: str) -> Optional[OperatorHealthMetrics]:
        """
        Get cached health metrics from Redis
        """
        # TODO: Implement Redis cache lookup
        return None
    
    async def connect_operator(self, operator_id: str) -> dict:
        """
        Connect operator (start SMPP connection)
        """
        op = await self.billing_client.get_operator(operator_id)
        connector_id = op.get("jasmin_connector_id") or op["code"]
        
        commands = [f"smppccm -1 {connector_id}"]  # Start connector
        result = await self.jasmin_client.execute_jcli_commands(commands)
        
        return result
    
    async def disconnect_operator(self, operator_id: str) -> dict:
        """
        Disconnect operator (stop SMPP connection)
        """
        op = await self.billing_client.get_operator(operator_id)
        connector_id = op.get("jasmin_connector_id") or op["code"]
        
        commands = [f"smppccm -0 {connector_id}"]  # Stop connector
        result = await self.jasmin_client.execute_jcli_commands(commands)
        
        return result
    
    async def get_operator_stats(
        self,
        operator_id: str,
        start_date: str,
        end_date: str,
    ) -> OperatorStatsResponse:
        """
        Get operator statistics for a period
        """
        # Query CDR from billing service
        stats = await self.billing_client.get_operator_stats(
            operator_id=operator_id,
            start_date=start_date,
            end_date=end_date,
        )
        
        return OperatorStatsResponse(**stats)
