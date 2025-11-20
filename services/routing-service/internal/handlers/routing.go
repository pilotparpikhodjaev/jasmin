package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"routing-service/internal/service"
	"routing-service/internal/models"
)

// HealthCheck returns service health status
func HealthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"service": "routing",
		"status":  "ok",
	})
}

// GetRoutingDecision handles POST /v1/routing/decision
func GetRoutingDecision(c *gin.Context) {
	var req models.RoutingRequest

	// Bind and validate JSON request
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "invalid_request",
			"message": err.Error(),
		})
		return
	}

	// Get routing decision
	response, err := service.GetRoutingDecision(req)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"error":   "routing_failed",
			"message": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, response)
}

// GetOperators handles GET /v1/operators
func GetOperators(c *gin.Context) {
	operators, err := service.GetAllOperators()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "database_error",
			"message": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"operators": operators,
		"count":     len(operators),
	})
}

// GetOperatorByPhone handles GET /v1/operators/:phone
func GetOperatorByPhone(c *gin.Context) {
	phone := c.Param("phone")

	// Create a routing request to identify operator
	req := models.RoutingRequest{
		DestinationMSISDN: phone,
		AccountID:         "system",
		MessageParts:      1,
	}

	response, err := service.GetRoutingDecision(req)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"error":   "operator_not_found",
			"message": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"phone":        phone,
		"operator":     response.OperatorName,
		"connector_id": response.PrimaryConnectorID,
		"price":        response.CostPerPart,
	})
}
