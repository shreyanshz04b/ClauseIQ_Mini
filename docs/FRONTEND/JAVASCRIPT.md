# Frontend Files Documentation

## JavaScript Files

### main.js
**Purpose**: Global utilities and authentication management.

**Key Variables**:
- `window.__authSession`: Cached session data
- Form element references: loginForm, logoutBtn, uploadForm, accessRequestForm

**Key Functions**:

`requestJSON(url, method, body)`:
- HTTP request wrapper for JSON APIs
- Parameters:
  - url: API endpoint
  - method: "GET", "POST", etc. (default: "GET")
  - body: Object to send as JSON (default: null)
- Returns: Parsed JSON response
- Throws: Error if HTTP response is not ok

`getAuthMode()`:
- Gets auth mode from body data attribute
- Returns: "any", "protected", "public-only", "password-change-only"

`fetchSessionState()`:
- Checks if user is authenticated
- Calls: GET /api/auth/session
- Returns: {authenticated: boolean, username, role, force_password_change}
- Fallback: Returns {authenticated: false} on error

`enforceAuthMode()`:
- Main auth flow enforcement
- Called on: Page load, page show event
- Logic:
  - "any" mode: Allow unrestricted access
  - "protected" mode: Redirect to /login if not authenticated
  - "public-only" mode: Redirect if authenticated
  - "password-change-only" mode: Force password change or redirect

**Event Handlers**:

`window.addEventListener("pageshow", ...)`:
- Rechecks auth on browser back button
- Calls: enforceAuthMode()

`document.addEventListener("DOMContentLoaded", ...)`:
- Runs on page load
- Calls: enforceAuthMode()

`document.addEventListener("auth-session-ready", ...)`:
- Updates session display with username/role
- Updates: #sessionUserDisplay element

**Form Handlers**:

Login form (`#loginForm`):
- Submits username/password via POST /api/auth/login
- On success: Redirects to /chat
- On error: Shows error message in #loginMsg

Logout button (`#logoutBtn`):
- Calls: POST /api/auth/logout
- Redirects to home page

Upload form (`#uploadForm`):
- Submits file via multipart POST /api/upload
- Shows: Index button on success
- Shows: Error message on failure
- Stores: indexPath for manual indexing

Index button (`#indexBtn`):
- Manual document indexing
- Calls: POST to stored indexPath
- Updates: Status messages

Metrics button (`#refreshMetrics`):
- Admin feature: Loads stats
- Calls: GET /api/admin/metrics
- Displays: JSON in #metricsBox

**Dependencies**: Fetch API, DOM

---

### chat.js
**Purpose**: Chat interface logic - messages, documents, file uploads.

**Key Variables**:
- `chatForm`: Form for submitting queries
- `chatBox`: Chat message display area
- `docsList`: Document list container
- `chatInput`: Input field for queries
- `chatSubmitBtn`: Submit button

**Key Functions**:

`escapeHTML(str)`:
- Escapes HTML special characters
- Prevents XSS attacks
- Converts: &, <, >, ", ' to entities

`addLine(who, text, isCitation)`:
- Adds message bubble to chat
- Parameters:
  - who: "You" or "Assistant" or "Citations"
  - text: Message content
  - isCitation: Boolean (affects screen reader announcement)
- Creates DOM element with styled message
- Auto-scrolls chat to bottom
- Announces to screen readers

`announceToScreenReader(message)`:
- Accessibility: Announces changes to screen readers
- Creates hidden div with role="status"
- Auto-removes after 1 second

`setStatus(message, isError)`:
- Updates status line below chat
- Styling: Red if error, gray if normal
- Announces: Message to screen readers

`formatBytes(bytes)`:
- Formats file size as human-readable string
- Returns: "1024 B", "5.2 KB", "1.5 MB"

`loadDocuments()`:
- Fetches document list via GET /api/documents
- Renders document cards in #docsList
- Shows: Document name, status, size
- Each document has delete button
- Shows: "No documents" message if empty

`deleteDocument(documentId)`:
- Deletes specific document
- Calls: DELETE /api/documents/<id>
- Updates: Document list
- Shows: Confirmation message

`uploadAndIndex(file)`:
- Uploads and automatically indexes file
- Steps:
  1. Shows "Uploading..." status
  2. POSTs file to /api/upload
  3. Waits for response
  4. Updates status message
  5. Refreshes document list

**Event Listeners**:

Upload trigger (`#uploadTrigger`):
- Click: Opens file input dialog
- Allows: Multiple file selections via file input

File input change (`#chatFileInput`):
- On file selected: Calls uploadAndIndex()
- Clears: File input after upload

Refresh button (`#refreshDocs`):
- Click: Reloads document list

Document list click:
- Displays: Delete button for each document
- On delete click: Calls deleteDocument()

Chat input keyboard shortcuts:
- Ctrl/Cmd+Enter: Submit form
- Escape: Clear input text

Chat form submission (`#chatForm`):
- Gets query from input
- Shows: "Thinking..." status
- Adds: "You" message to chat
- Disables: Submit button while processing
- POSTs: {query} to /api/chat
- Response handling:
  - Error: Shows error in red
  - Success: Shows response in chat
  - Has citations: Renders citation section
- Handles: Network errors gracefully
- Finally: Re-enables button, focuses input

**Page Load**:
- Calls: loadDocuments() on DOM ready
- Adds: screen reader styles to head

**Dependencies**: Fetch API, DOM manipulation
