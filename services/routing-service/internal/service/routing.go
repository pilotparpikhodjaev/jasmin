package service

import (
	"database/sql"
	"fmt"
	"routing-service/internal/database"
	"routing-service/internal/models"
	"strings"
)

// GetRoutingDecision implements LCR (Least Cost Routing) logic
func GetRoutingDecision(req models.RoutingRequest) (*models.RoutingResponse, error) {
	// Step 1: Extract country code and prefix from MSISDN
	operator, err := getOperatorByPhone(req.DestinationMSISDN)
	if err != nil {
		return nil, fmt.Errorf("failed to identify operator: %w", err)
	}

	// Step 2: Calculate cost
	costPerPart := operator.PricePerSMS

	// Step 3: Get backup connectors (other operators with higher cost)
	backups, err := getBackupConnectors(operator.ID)
	if err != nil {
		return nil, fmt.Errorf("failed to get backup connectors: %w", err)
	}

	return &models.RoutingResponse{
		PrimaryConnectorID: operator.SMPPConnectorID,
		BackupConnectorIDs: backups,
		CostPerPart:        costPerPart,
		OperatorName:       operator.Name,
	}, nil
}

// getOperatorByPhone identifies operator from phone number using MCC/MNC prefix matching
func getOperatorByPhone(phone string) (*models.Operator, error) {
	// Normalize phone number (remove +, spaces, etc.)
	normalized := strings.TrimPrefix(phone, "+")
	normalized = strings.ReplaceAll(normalized, " ", "")
	normalized = strings.ReplaceAll(normalized, "-", "")

	// Try to match by MCC/MNC prefix (longest match first)
	// Normalized phone has no '+', so strip '+' from country_code for matching
	var operatorID int
	query := `
		SELECT operator_id
		FROM mcc_mnc_prefixes
		WHERE $1 LIKE REPLACE(country_code, '+', '') || prefix || '%'
		ORDER BY LENGTH(prefix) DESC
		LIMIT 1
	`
	err := database.DB.Get(&operatorID, query, normalized)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("no operator found for phone number: %s", phone)
		}
		return nil, err
	}

	// Fetch operator details
	var operator models.Operator
	err = database.DB.Get(&operator, "SELECT * FROM operators WHERE id = $1 AND status = 'active'", operatorID)
	if err != nil {
		return nil, fmt.Errorf("operator not found or inactive: %w", err)
	}

	return &operator, nil
}

// getBackupConnectors returns alternative connectors sorted by price
func getBackupConnectors(primaryOperatorID int) ([]string, error) {
	var backupConnectors []string
	query := `
		SELECT smpp_connector_id
		FROM operators
		WHERE id != $1 AND status = 'active'
		ORDER BY price_per_sms ASC, health_score DESC
		LIMIT 3
	`
	err := database.DB.Select(&backupConnectors, query, primaryOperatorID)
	if err != nil {
		return nil, err
	}
	return backupConnectors, nil
}

// GetAllOperators returns all active operators
func GetAllOperators() ([]models.Operator, error) {
	var operators []models.Operator
	query := `
		SELECT * FROM operators
		WHERE status = 'active'
		ORDER BY priority ASC, price_per_sms ASC
	`
	err := database.DB.Select(&operators, query)
	return operators, err
}
