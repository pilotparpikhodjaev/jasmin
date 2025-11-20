package models

// RoutingRequest represents an incoming routing decision request
type RoutingRequest struct {
	DestinationMSISDN string `json:"destination_msisdn" binding:"required"`
	AccountID         string `json:"account_id" binding:"required"`
	MessageParts      int    `json:"message_parts" binding:"required,min=1"`
}

// RoutingResponse represents a routing decision
type RoutingResponse struct {
	PrimaryConnectorID string            `json:"primary_connector_id"`
	BackupConnectorIDs []string          `json:"backup_connector_ids"`
	CostPerPart        float64           `json:"cost_per_part"`
	Currency           string            `json:"currency"`
	OperatorName       string            `json:"operator_name"`
	EstimatedCost      float64           `json:"estimated_cost"`
	RoutingDecision    string            `json:"routing_decision"` // "success", "no_route", "error"
	Message            string            `json:"message,omitempty"`
}

// OperatorListResponse represents a list of operators
type OperatorListResponse struct {
	Operators []Operator `json:"operators"`
	Total     int        `json:"total"`
}

// HealthCheckResponse represents service health status
type HealthCheckResponse struct {
	Status    string `json:"status"`
	Service   string `json:"service"`
	Version   string `json:"version"`
	Timestamp string `json:"timestamp"`
}
