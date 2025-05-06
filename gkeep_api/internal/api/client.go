package api

import (
	"context"
	"net/http"

	"gkeep_api/configs"
)

// Client represents a Google Keep API client
type Client struct {
    config     *configs.Config
    httpClient *http.Client
}

// NewClient creates a new Google Keep API client
func NewClient(ctx context.Context, config *configs.Config) (*Client, error) {
    httpClient, err := config.GetClient(ctx)
    if err != nil {
        return nil, err
    }
    
    return &Client{
        config:     config,
        httpClient: httpClient,
    }, nil
}