package models

type Note struct {
    ID        string `json:"id"`
    Title     string `json:"title"`
    Content   string `json:"content"`
    CreatedAt string `json:"created_at"`
    UpdatedAt string `json:"updated_at"`
}

type NotesListRequestParams struct {
    PageSize  int    `json:"pageSize"`
    PageToken string `json:"pageToken"`
    Filter    string `json:"filter"`
}

type NotesListResponse struct {
    Notes      []Note `json:"notes"`
    NextPage  string `json:"nextPageToken"`
}