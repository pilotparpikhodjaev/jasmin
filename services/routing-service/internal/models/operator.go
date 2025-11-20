package models

import "time"

// Operator represents a mobile network operator (carrier)
type Operator struct {
	ID               int       `db:"id" json:"id"`
	Name             string    `db:"name" json:"name"`
	Country          string    `db:"country" json:"country"`
	MCC              string    `db:"mcc" json:"mcc"`      // Mobile Country Code
	MNC              string    `db:"mnc" json:"mnc"`      // Mobile Network Code
	SMPPConnectorID  string    `db:"smpp_connector_id" json:"smpp_connector_id"`
	Status           string    `db:"status" json:"status"` // active, suspended, testing
	PricePerSMS      float64   `db:"price_per_sms" json:"price_per_sms"`
	Currency         string    `db:"currency" json:"currency"`
	HealthScore      int       `db:"health_score" json:"health_score"` // 0-100
	Priority         int       `db:"priority" json:"priority"`         // Lower number = higher priority
	CreatedAt        time.Time `db:"created_at" json:"created_at"`
	UpdatedAt        time.Time `db:"updated_at" json:"updated_at"`
}

// MCCMNCPrefix represents a phone number prefix mapping to operator
type MCCMNCPrefix struct {
	ID         int       `db:"id" json:"id"`
	CountryCode string   `db:"country_code" json:"country_code"` // e.g., "+998"
	Prefix      string    `db:"prefix" json:"prefix"`              // e.g., "90", "91", "93"
	MCC         string    `db:"mcc" json:"mcc"`
	MNC         string    `db:"mnc" json:"mnc"`
	OperatorID  int       `db:"operator_id" json:"operator_id"`
	CreatedAt   time.Time `db:"created_at" json:"created_at"`
}

// OperatorHealth represents real-time operator health metrics
type OperatorHealth struct {
	OperatorID      int       `db:"operator_id" json:"operator_id"`
	DLRRate         float64   `db:"dlr_rate" json:"dlr_rate"`             // Delivery success rate (0-100%)
	AvgLatencyMS    int       `db:"avg_latency_ms" json:"avg_latency_ms"` // Average DLR latency in milliseconds
	CurrentTPS      int       `db:"current_tps" json:"current_tps"`       // Current throughput (TPS)
	ErrorRate       float64   `db:"error_rate" json:"error_rate"`         // Error rate (0-100%)
	HealthScore     int       `db:"health_score" json:"health_score"`     // Calculated 0-100
	LastUpdated     time.Time `db:"last_updated" json:"last_updated"`
}
