package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"time"

	"cloud.google.com/go/firestore"
	"github.com/modelcontextprotocol/go-sdk/mcp"
	"google.golang.org/api/option"
)

// HealthMetrics maps exactly to your Firestore document schema
type HealthMetrics struct {
	Steps         int64   `firestore:"steps,omitempty" json:"steps"`
	CaloriesBurnt int64   `firestore:"caloriesBurnt,omitempty" json:"calories_burnt"`
	Weight        float64 `firestore:"weight,omitempty" json:"weight"`
	BloodPressure struct {
		Systolic  int64 `firestore:"systolic" json:"systolic"`
		Diastolic int64 `firestore:"diastolic" json:"diastolic"`
	} `firestore:"bloodPressure,omitempty" json:"blood_pressure"`
	LastUpdated time.Time `firestore:"lastUpdated" json:"last_updated"`
}

// TodaySummaryInput defines parameters for the tool.
type TodaySummaryInput struct{}

// TodaySummaryOutput matches the standard output block type
type TodaySummaryOutput struct {
	Result string `json:"result"`
}

func main() {
	ctx := context.Background()
	projectID := "mcp-personel-health"

	// 1. Initialize Firestore Client using the local service account
	opt := option.WithCredentialsFile("service-account.json")
	firestoreClient, err := firestore.NewClient(ctx, projectID, opt)
	if err != nil {
		log.Fatalf("Failed to initialize Firestore client: %v", err)
	}
	defer firestoreClient.Close()

	// 2. Initialize the local MCP Server instance with proper metadata reference
	serverInfo := &mcp.Implementation{
		Name:    "personal-health-server",
		Version: "1.0.0",
	}
	mcpServer := mcp.NewServer(serverInfo, nil)

	// 3. Register the health tracking tool via type-safe generics
	mcp.AddTool(mcpServer, &mcp.Tool{
		Name:        "get_today_health_summary",
		Description: "Retrieves the user's real health metrics for today: weight, steps, calories burnt, and blood pressure.",
	}, func(ctx context.Context, req *mcp.CallToolRequest, input TodaySummaryInput) (*mcp.CallToolResult, TodaySummaryOutput, error) {

		// Enforce local Spanish timezone layout
		loc, err := time.LoadLocation("Europe/Madrid")
		if err != nil {
			loc = time.UTC
		}
		todayStr := time.Now().In(loc).Format("2006-01-02")

		// Query Firestore by Document ID
		doc, err := firestoreClient.Collection("health_metrics").Doc(todayStr).Get(ctx)
		if err != nil {
			msg := fmt.Sprintf("No metrics recorded yet for today (%s). Check back later.", todayStr)
			return &mcp.CallToolResult{
				Content: []mcp.Content{&mcp.TextContent{Text: msg}},
			}, TodaySummaryOutput{Result: msg}, nil
		}

		var metrics HealthMetrics
		if err := doc.DataTo(&metrics); err != nil {
			return nil, TodaySummaryOutput{}, fmt.Errorf("failed to map firestore document: %w", err)
		}

		// Serialize the struct to JSON for the LLM context window
		jsonBytes, err := json.MarshalIndent(metrics, "", "  ")
		if err != nil {
			return nil, TodaySummaryOutput{}, fmt.Errorf("failed to marshal metrics: %w", err)
		}

		responseText := string(jsonBytes)
		return &mcp.CallToolResult{
			Content: []mcp.Content{&mcp.TextContent{Text: responseText}},
		}, TodaySummaryOutput{Result: responseText}, nil
	})

	// 4. Run the server using Standard I/O (stdio) transport
	log.Println("Launching local Personal Health MCP Server on stdio...")
	if err := mcpServer.Run(ctx, &mcp.StdioTransport{}); err != nil {
		log.Fatalf("MCP Server standard I/O execution loop dropped: %v", err)
	}
}
