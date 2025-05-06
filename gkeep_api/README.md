# Google Keep Notes

This project is a simple Go application that interacts with the Google Keep API to retrieve and display your notes.

## Project Structure

```
gkeep_api
├── cmd
│   └── main.go          # Entry point of the application
├── internal
│   ├── api
│   │   └── keep.go      # Functions to interact with the Google Keep API
│   └── models
│       └── note.go      # Structs representing notes
├── configs
│   └── config.go        # Configuration settings for the application
├── go.mod                # Module definition and dependencies
├── go.sum                # Dependency checksums
└── README.md             # Project documentation
```

## Setup Instructions

1. **Create a new directory for your project:**
   ```bash
   mkdir gkeep_api
   cd gkeep_api
   ```

2. **Initialize a new Go module:**
   ```bash
   go mod init gkeep_api
   ```

3. **Create the directory structure:**
   ```bash
   mkdir -p cmd internal/api internal/models configs
   ```

4. **Create the necessary Go files:**
   ```bash
   touch cmd/main.go internal/api/keep.go internal/models/note.go configs/config.go
   ```

5. **Open the project in your preferred code editor and implement the functionality in each file.**

6. **Install any required dependencies using:**
   ```bash
   go get <dependency>
   ```

7. **Build and run the application:**
   ```bash
   go run cmd/main.go
   ```

8. **Follow the instructions in README.md for further usage and configuration.**

## Usage

After setting up the project and implementing the necessary functionality, you can run the application to fetch and display your Google Keep notes. Make sure to configure your API keys and any other settings in `configs/config.go` before running the application.