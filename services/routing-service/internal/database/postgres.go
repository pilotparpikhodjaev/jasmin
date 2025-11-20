package database

import (
	"fmt"
	"log"
	"os"

	"github.com/jmoiron/sqlx"
	_ "github.com/lib/pq" // PostgreSQL driver
)

// DB is the global database connection
var DB *sqlx.DB

// InitDB initializes the PostgreSQL connection
func InitDB() error {
	dbURL := os.Getenv("ROUTING_DB_URL")
	if dbURL == "" {
		dbURL = "postgres://otp:otp-secret@postgres:5432/otp?sslmode=disable"
	}

	var err error
	DB, err = sqlx.Connect("postgres", dbURL)
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}

	// Set connection pool settings
	DB.SetMaxOpenConns(25)
	DB.SetMaxIdleConns(5)

	log.Println("Database connection established")
	return nil
}

// CloseDB closes the database connection
func CloseDB() error {
	if DB != nil {
		return DB.Close()
	}
	return nil
}
