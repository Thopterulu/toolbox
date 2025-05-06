package api

import (
	"context"
	"encoding/json"
	"fmt"
	"gkeep_api/internal/models"
	"net/http"
)

// FetchNotes retrieves notes from the Google Keep API.
func (c *Client) FetchNotes(ctx context.Context) ([]models.Note, error) {
    // Use the API endpoint from config instead of hard-coding it
    req, err := http.NewRequestWithContext(ctx, "GET", c.config.APIEndpoint, nil)
    if err != nil {
        return nil, err
    }

    // No need to append an API key since we're using OAuth
    resp, err := c.httpClient.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    if resp.StatusCode != http.StatusOK {
        return nil, fmt.Errorf("failed to fetch notes: %s", resp.Status)
    }

    var response models.NotesListResponse
    if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
        return nil, err
    }

    return response.Notes, nil
}