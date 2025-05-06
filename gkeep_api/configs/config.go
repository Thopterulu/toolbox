package configs

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"

	"github.com/joho/godotenv"
	"golang.org/x/oauth2"
	"golang.org/x/oauth2/google"
)

type Config struct {
    OAuth2Config *oauth2.Config
    TokenFile    string
    APIEndpoint  string
}

func LoadConfig() (*Config, error) {
    err := godotenv.Load()
    if err != nil {
        log.Printf("Warning: Error loading .env file: %v", err)
        // Continue anyway, env vars might be set another way
    }
    
    clientID := os.Getenv("GOOGLE_CLIENT_ID")
    clientSecret := os.Getenv("GOOGLE_CLIENT_SECRET")
    redirectURL := os.Getenv("GOOGLE_REDIRECT_URL")
    tokenFile := os.Getenv("GOOGLE_TOKEN_FILE")
    
    if tokenFile == "" {
        homeDir, err := os.UserHomeDir()
        if err != nil {
            return nil, fmt.Errorf("could not get user home directory: %v", err)
        }
        tokenFile = filepath.Join(homeDir, ".gkeep_token.json")
    }
    
    if clientID == "" || clientSecret == "" {
        return nil, fmt.Errorf("client ID and client secret must be set")
    }
    
    if redirectURL == "" {
        redirectURL = "http://localhost:8080/callback"
    }

    // Configure the OAuth2 client
    config := &oauth2.Config{
        ClientID:     clientID,
        ClientSecret: clientSecret,
        RedirectURL:  redirectURL,
        Scopes: []string{
            // Google Keep n'a pas d'API officielle, utiliser des scopes généraux
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile", 
            "openid",
        },
        Endpoint: google.Endpoint,
    }

    return &Config{
        OAuth2Config: config,
        TokenFile:    tokenFile,
        APIEndpoint:  "https://keep.googleapis.com/v1/notes",
    }, nil
}

// GetToken retrieves a valid OAuth token, either from the cached file or by initiating a new auth flow
func (c *Config) GetToken() (*oauth2.Token, error) {
    token, err := c.tokenFromFile()
    if err == nil && token.Valid() {
        return token, nil
    }
    
    // Token doesn't exist or is invalid, get a new one
    authURL := c.OAuth2Config.AuthCodeURL("state-token", oauth2.AccessTypeOffline)
    fmt.Printf("Go to the following link in your browser: \n%v\n", authURL)
    fmt.Printf("Enter the authorization code: ")

    var authCode string
    if _, err := fmt.Scan(&authCode); err != nil {
        return nil, fmt.Errorf("unable to read authorization code: %v", err)
    }

    token, err = c.OAuth2Config.Exchange(context.Background(), authCode)
    if err != nil {
        return nil, fmt.Errorf("unable to retrieve token: %v", err)
    }
    
    // Save the token for future use
    err = c.saveToken(token)
    if err != nil {
        log.Printf("Warning: Failed to save token: %v", err)
    }
    
    return token, nil
}

// tokenFromFile retrieves a token from a local file
func (c *Config) tokenFromFile() (*oauth2.Token, error) {
    f, err := os.Open(c.TokenFile)
    if err != nil {
        return nil, err
    }
    defer f.Close()
    
    token := &oauth2.Token{}
    err = json.NewDecoder(f).Decode(token)
    return token, err
}

// saveToken saves a token to a file
func (c *Config) saveToken(token *oauth2.Token) error {
    f, err := os.OpenFile(c.TokenFile, os.O_RDWR|os.O_CREATE|os.O_TRUNC, 0600)
    if err != nil {
        return fmt.Errorf("unable to cache oauth token: %v", err)
    }
    defer f.Close()
    
    return json.NewEncoder(f).Encode(token)
}

// GetClient returns an HTTP client with OAuth credentials
func (c *Config) GetClient(ctx context.Context) (*http.Client, error) {
    token, err := c.GetToken()
    if err != nil {
        return nil, err
    }
    return c.OAuth2Config.Client(ctx, token), nil
}