# Frontend HTML Templates

## base.html
**Purpose**: Base template providing common layout, navigation, styling.

**Key Elements**:
- Doctype: HTML5
- Meta tags: UTF-8, viewport, X-UA-Compatible
- Stylesheets:
  - Tailwind CSS (via CDN)
  - Custom app.css
  - Any block-level child stylesheets
- Navigation bar: Home, Chat links
- Session display: Shows logged-in username if authenticated
- Logout button: Available when authenticated
- Body content: Jinja2 block for child templates
- Footer scripts: main.js for global utilities
- Theme: Dark mode compatible (via Tailwind)

**Template Blocks**:
- `{% block title %}`: Page title in browser tab
- `{% block content %}`: Main page content (overridden by child templates)
- `{% block extra_css %}`: Additional stylesheet for specific pages
- `{% block extra_scripts %}`: Additional scripts for specific pages

**Navigation Items**:
- Logo/Home link
- Chat link (if authenticated)
- User display (name + role)
- Logout button

---

## chat.html
**Purpose**: Main chat interface - query input, response display, document management.

**Key Sections**:

**Header**:
- Page title: "Chat Interface"
- Instructions: "Ask questions about your documents"

**Document Management Panel**:
- Refresh button: Reload document list
- Upload button: Trigger file input
- Document list: Cards showing each document
  - Document name
  - Indexing status (indexed/pending/failed)
  - File size
  - Delete button

**Chat Area**:
- Chat box: Scrollable message display
  - User messages: Aligned right, blue background
  - Assistant messages: Aligned left, gray background
  - Citations: Special "Citations" message format
- Status line: Shows current operation status
- Keyboard shortcuts: Ctrl+Enter to send, Escape to clear

**Query Input**:
- Text input field: Large, full-width
- Submit button: Styled, disabled while processing
- Form validation: Empty queries rejected

**Hidden Elements**:
- File input: #chatFileInput (triggered by upload button)

**CSS Classes** (from app.css):
- chat-bubble: Message container styling
- chat-bubble-content: Message content styling
- doc-card: Document list item styling
- doc-card-delete: Delete button styling

**JavaScript Events**:
- Load documents on page load
- Handle query submission
- Handle file uploads
- Handle document deletion
- Keyboard shortcuts for efficiency

---

## landing.html
**Purpose**: Welcome/landing page - project overview and call-to-action.

**Key Sections**:

**Hero Section**:
- Large heading: Project name/title
- Subheading: Brief description
- Call-to-action button: Link to /chat

**Features Section**:
- List of key features
- Benefits of using the system
- Icons/visual elements (CSS-based)

**How It Works Section**:
- Step-by-step explanation
- Upload documents → Ask questions → Get answers
- Citation highlighting

**Access Request Section** (if needed):
- Form for users to request access
- Fields: Name, email, organization, use case
- Submit button
- Response message area

**Footer**:
- Contact information
- Links to documentation
- Copyright notice

**Styling**:
- Responsive design (mobile-friendly)
- Tailwind CSS utilities
- Custom CSS from app.css
- Smooth scrolling, transitions
- Color scheme: Professional, accessible

---

# CSS Files

## app.css
**Purpose**: Custom styling beyond Tailwind CSS defaults.

**Key Components**:

**Chat Bubble Styling**:
- .chat-bubble: Message container with rounded corners
- .chat-bubble.user: Right-aligned user messages (blue)
- .chat-bubble.assistant: Left-aligned bot messages (gray)
- .chat-bubble-content: Inner content with padding
- .chat-bubble-label: Speaker name (small, muted)
- .chat-bubble-text: Message text (normal weight)

**Document Card Styling**:
- .doc-card: Card container with border, shadow
- .doc-card-title: Document filename (truncated)
- .doc-card-status: Status badge with color
  - .indexed: Green color
  - .rejected: Red color
  - .pending: Yellow color
- .doc-card-delete: Delete button styling

**Chat Interface**:
- Chat input area: Full-width, placeholder text
- Submit button: Primary color, disabled state
- Status line: Small text, color-coded (red for errors)
- Scroll container: Max height with overflow-y

**Color Scheme**:
- Primary: Blue (action buttons, user messages)
- Success: Green (indexed status)
- Error: Red (failed status, error messages)
- Neutral: Gray (assistant messages, text)
- Background: White or dark mode compatible

**Responsive Design**:
- Mobile-first approach
- Breakpoints: sm, md, lg (from Tailwind)
- Chat box: Height adjusts for viewport
- Input area: Sticks to bottom on scroll
- Document cards: Grid layout responsive

**Accessibility**:
- .sr-only: Screen reader only text (hidden visually)
- Good contrast: Text color vs. background
- Focus states: Visible outline on buttons
- Semantic HTML: Proper heading hierarchy

**Typography**:
- Body font: System font stack (via Tailwind)
- Sizes: Base 14px, small 12px, large 16px
- Weight: Normal for body, semibold for labels

**Spacing**:
- Padding: 12px standard (3 × 4px unit)
- Margins: 8px between sections
- Gap: 8px between grid items
