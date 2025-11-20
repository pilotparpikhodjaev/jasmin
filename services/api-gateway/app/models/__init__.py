"""
Data models for API Gateway
"""

from .auth import *
from .sms import *
from .user import *
from .operator import *
from .template import *

__all__ = [
    # Auth models
    "TokenData",
    "TokenResponse",
    "LoginRequest",
    "RefreshTokenRequest",
    "UserResponse",
    
    # SMS models
    "SMSSendRequest",
    "SMSBatchRequest",
    "SMSGlobalRequest",
    "SMSResponse",
    "SMSStatusResponse",
    "MessageHistoryRequest",
    "DispatchStatusResponse",
    "SMSNormalizerRequest",
    "SMSCheckRequest",
    "SMSCheckResponse",
    
    # User models
    "UserProfile",
    "BalanceResponse",
    "NicknameResponse",
    "TotalsRequest",
    "TotalsResponse",
    
    # Operator models
    "OperatorCreate",
    "OperatorUpdate",
    "OperatorResponse",
    "OperatorHealthMetrics",
    "SMPPConnectionConfig",
    
    # Template models
    "TemplateCreate",
    "TemplateUpdate",
    "TemplateResponse",
    "TemplateStatus",
]

