package main

import (
	"log"
	"os"

	"github.com/gin-gonic/gin"
	"routing-service/internal/database"
	"routing-service/internal/handlers"
)

func main() {
	// Initialize database
	if err := database.InitDB(); err != nil {
		log.Fatalf("Failed to initialize database: %v", err)
	}
	defer database.CloseDB()

	// Set Gin mode from environment
	if mode := os.Getenv("GIN_MODE"); mode != "" {
		gin.SetMode(mode)
	} else {
		gin.SetMode(gin.ReleaseMode)
	}

	// Create router
	router := gin.Default()

	// Health check endpoint
	router.GET("/health", handlers.HealthCheck)

	// Routing endpoints
	v1 := router.Group("/v1")
	{
		v1.POST("/routing/decision", handlers.GetRoutingDecision)
		v1.GET("/operators", handlers.GetOperators)
		v1.GET("/operators/:phone", handlers.GetOperatorByPhone)
	}

	// Start server
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("Starting Routing Service on port %s", port)
	if err := router.Run(":" + port); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
