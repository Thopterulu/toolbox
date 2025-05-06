package main

import (
	"context"
	"gkeep_api/configs"
	"gkeep_api/internal/api"
	"log"
)

func main() {
    // Load configuration
    config, err := configs.LoadConfig()
    if err != nil {
        log.Fatalf("Error loading config: %v", err)
    }

    // Initialize Google Keep API client
    client, err := api.NewClient(context.Background(), config)
    if err != nil {
        log.Fatalf("Error creating API client: %v", err)
    }

    // Fetch notes
    notes, err := client.FetchNotes(context.Background())
    if err != nil {
        log.Fatalf("Error fetching notes: %v", err)
    }

    // Print notes
    for _, note := range notes {
        log.Printf("Note ID: %s, Title: %s, Content: %s", note.ID, note.Title, note.Content)
    }
}