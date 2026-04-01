package main

import (
	"database/sql"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	_ "github.com/lib/pq"
)

type Device struct {
	ID       string    `json:"id"`
	Name     string    `json:"name"`
	Type     string    `json:"type"`
	State    string    `json:"state"`
	Location string    `json:"location"`
	UpdatedAt time.Time `json:"updated_at"`
}

var db *sql.DB

func main() {
	var err error
	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		dbURL = "postgres://postgres:postgres@localhost:5432/devices?sslmode=disable"
	}

	time.Sleep(5 * time.Second) // Wait for DB
	db, err = sql.Open("postgres", dbURL)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	router := gin.Default()
	router.GET("/health", func(c *gin.Context) { c.JSON(200, gin.H{"status": "ok"}) })
	
	api := router.Group("/api/v1/devices")
	{
		api.GET("", getDevices)
		api.POST("", createDevice)
		api.GET("/:id", getDevice)
		api.GET("/:id/state", getDeviceState)
		api.POST("/:id/actions", executeAction)
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = ":8083"
	}
	log.Printf("Device Service starting on %s", port)
	router.Run(port)
}

func getDevices(c *gin.Context) {
	rows, err := db.Query("SELECT id, name, type, state, location, updated_at FROM devices ORDER BY updated_at DESC")
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	devices := []Device{}
	for rows.Next() {
		var d Device
		rows.Scan(&d.ID, &d.Name, &d.Type, &d.State, &d.Location, &d.UpdatedAt)
		devices = append(devices, d)
	}
	c.JSON(200, devices)
}

func createDevice(c *gin.Context) {
	var input struct {
		Name     string `json:"name"`
		Type     string `json:"type"`
		Location string `json:"location"`
	}
	if err := c.BindJSON(&input); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}

	id := uuid.New().String()
	now := time.Now()
	_, err := db.Exec("INSERT INTO devices (id, name, type, state, location, created_at, updated_at) VALUES ($1, $2, $3, 'OFF', $4, $5, $5)",
		id, input.Name, input.Type, input.Location, now)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}

	c.JSON(201, Device{ID: id, Name: input.Name, Type: input.Type, State: "OFF", Location: input.Location, UpdatedAt: now})
}

func getDevice(c *gin.Context) {
	id := c.Param("id")
	var d Device
	err := db.QueryRow("SELECT id, name, type, state, location, updated_at FROM devices WHERE id = $1", id).
		Scan(&d.ID, &d.Name, &d.Type, &d.State, &d.Location, &d.UpdatedAt)
	if err != nil {
		c.JSON(404, gin.H{"error": "Device not found"})
		return
	}
	c.JSON(200, d)
}

func getDeviceState(c *gin.Context) {
	id := c.Param("id")
	var state string
	var updatedAt time.Time
	err := db.QueryRow("SELECT state, updated_at FROM devices WHERE id = $1", id).Scan(&state, &updatedAt)
	if err != nil {
		c.JSON(404, gin.H{"error": "Device not found"})
		return
	}
	c.JSON(200, gin.H{"deviceId": id, "state": state, "updatedAt": updatedAt})
}

func executeAction(c *gin.Context) {
	id := c.Param("id")
	var input struct {
		Action string `json:"action"`
	}
	if err := c.BindJSON(&input); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}

	var currentState string
	db.QueryRow("SELECT state FROM devices WHERE id = $1", id).Scan(&currentState)

	newState := "OFF"
	switch input.Action {
	case "TURN_ON":
		newState = "ON"
	case "TURN_OFF":
		newState = "OFF"
	case "TOGGLE":
		if currentState == "ON" {
			newState = "OFF"
		} else {
			newState = "ON"
		}
	default:
		c.JSON(400, gin.H{"error": "Invalid action"})
		return
	}

	_, err := db.Exec("UPDATE devices SET state = $1, updated_at = $2 WHERE id = $3", newState, time.Now(), id)
	if err != nil {
		c.JSON(500, gin.H{"error": err.Error()})
		return
	}

	// Log to stdout (можно потом отправлять в RabbitMQ)
	event, _ := json.Marshal(map[string]string{"device_id": id, "previous_state": currentState, "new_state": newState})
	log.Printf("Device state changed: %s", event)

	c.JSON(200, gin.H{"deviceId": id, "state": newState})
}
