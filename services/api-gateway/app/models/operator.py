"""
Operator management models - for admin panel
"""

from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal

from pydantic import BaseModel, Field, IPvAnyAddress


class SMPPConnectionConfig(BaseModel):
    """SMPP connection configuration"""
    host: str
    port: int = Field(ge=1, le=65535)
    system_id: str
    password: str
    system_type: str = ""
    bind_mode: str = Field(default="transceiver", pattern="^(transmitter|receiver|transceiver)$")
    
    # Connection settings
    bind_timeout: int = Field(default=30, ge=5, le=300)
    enquire_link_interval: int = Field(default=30, ge=10, le=300)
    reconnect_delay: int = Field(default=10, ge=1, le=300)
    max_reconnect_attempts: int = Field(default=0, ge=0, description="0 = unlimited")
    
    # Throughput settings
    submit_sm_throughput: int = Field(default=100, ge=1, le=10000, description="Messages per second")
    
    # TLS settings
    use_tls: bool = False
    tls_verify: bool = True
    
    # Additional parameters
    source_addr_ton: int = Field(default=0, ge=0, le=255)
    source_addr_npi: int = Field(default=0, ge=0, le=255)
    dest_addr_ton: int = Field(default=1, ge=0, le=255)
    dest_addr_npi: int = Field(default=1, ge=0, le=255)
    registered_delivery: int = Field(default=1, ge=0, le=255)


class OperatorCreate(BaseModel):
    """Create new operator"""
    name: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=2, max_length=20, description="Operator code (e.g., UZ_UCELL)")
    country: str = Field(pattern=r"^[A-Z]{2}$", description="ISO 3166-1 alpha-2")
    mcc: str = Field(pattern=r"^\d{3}$", description="Mobile Country Code")
    mnc: str = Field(pattern=r"^\d{2,3}$", description="Mobile Network Code")
    
    # Pricing
    price_per_sms: Decimal = Field(ge=0)
    currency: str = Field(default="UZS")
    
    # SMPP configuration
    smpp_config: SMPPConnectionConfig
    
    # Routing settings
    priority: int = Field(default=100, ge=0, le=1000, description="Higher = preferred in LCR")
    weight: int = Field(default=100, ge=0, le=100, description="Load balancing weight")
    
    # Health check settings
    health_check_enabled: bool = True
    health_check_interval: int = Field(default=60, ge=10, le=3600, description="Seconds")
    
    # Status
    status: str = Field(default="active", pattern="^(active|suspended|maintenance)$")
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = None


class OperatorUpdate(BaseModel):
    """Update operator"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    price_per_sms: Optional[Decimal] = Field(default=None, ge=0)
    smpp_config: Optional[SMPPConnectionConfig] = None
    priority: Optional[int] = Field(default=None, ge=0, le=1000)
    weight: Optional[int] = Field(default=None, ge=0, le=100)
    health_check_enabled: Optional[bool] = None
    health_check_interval: Optional[int] = Field(default=None, ge=10, le=3600)
    status: Optional[str] = Field(default=None, pattern="^(active|suspended|maintenance)$")
    metadata: Optional[Dict[str, Any]] = None


class OperatorHealthMetrics(BaseModel):
    """Operator health metrics"""
    operator_id: str | int
    operator_code: str
    
    # Connection status
    is_connected: bool
    last_connected_at: Optional[datetime]
    last_disconnected_at: Optional[datetime]
    connection_uptime_seconds: int
    
    # Performance metrics (last 5 minutes)
    submit_sm_count: int
    submit_sm_resp_count: int
    delivery_count: int
    failure_count: int
    
    # Success rates
    submit_success_rate: float = Field(ge=0, le=100, description="Percentage")
    delivery_rate: float = Field(ge=0, le=100, description="Percentage")
    
    # Latency (milliseconds)
    avg_submit_latency_ms: float
    p95_submit_latency_ms: float
    p99_submit_latency_ms: float
    
    # Health score (0-100)
    health_score: float = Field(ge=0, le=100)
    health_status: str = Field(pattern="^(healthy|degraded|unhealthy|unknown)$")
    
    # Errors
    recent_errors: list[str] = Field(default_factory=list, max_length=10)
    
    # Timestamp
    measured_at: datetime


class OperatorResponse(BaseModel):
    """Operator response"""
    id: str | int
    name: str
    code: str
    country: str
    mcc: str
    mnc: str
    price_per_sms: Decimal
    currency: str
    priority: int
    weight: int
    status: str
    health_check_enabled: bool
    health_check_interval: int
    created_at: datetime
    updated_at: datetime
    
    # SMPP config (masked password)
    smpp_host: str
    smpp_port: int
    smpp_system_id: str
    smpp_bind_mode: str
    submit_sm_throughput: int
    
    # Current health
    health_metrics: Optional[OperatorHealthMetrics] = None
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = None


class OperatorListResponse(BaseModel):
    """List of operators"""
    total: int
    operators: list[OperatorResponse]


class OperatorStatsResponse(BaseModel):
    """Operator statistics"""
    operator_id: str | int
    operator_code: str
    period_start: datetime
    period_end: datetime
    
    # Volume
    total_messages: int
    total_parts: int
    
    # Revenue
    total_revenue: Decimal
    currency: str
    
    # Performance
    avg_delivery_rate: float
    avg_latency_ms: float
    
    # Status breakdown
    by_status: Dict[str, int]
