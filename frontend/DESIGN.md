# MemoGraph — Frontend Design Guide

## Design Principles

1. **Photos first** — images are the primary content. UI chrome should be minimal and stay out of the way.
2. **Clean and breathable** — generous whitespace, no visual clutter.
3. **Consistent** — all pages share the same theme tokens. No one-off colors or font sizes.
4. **Accessible** — sufficient contrast ratios in both light and dark modes. Interactive elements clearly distinguishable.
5. **Swedish first** — UI language defaults to Swedish. User toggle to switch to English, persisted in localStorage. All user-facing text (labels, buttons, placeholders, empty states, error messages) must go through a translation system — no hardcoded strings in components. Use a simple key-based approach (e.g., `i18n` object or React context) with Swedish and English translation files.
6. **Connected navigation** — minimize full-page transitions. Where it makes sense, use overlays, drawers, or modals to keep the user anchored to their current context (e.g., image detail as an overlay on the gallery, person detail as a slide-out from a people list). Not every view needs its own page — some are better as layers on top of a base view. The route structure supports both approaches; the design branch decides which views are pages and which are overlays.

---

## Theme

### Mode

Light and dark mode with a user toggle. Preference persisted in localStorage. Respect `prefers-color-scheme` as the initial default.

### Color Palette

Ant Design's theme customization system (`ConfigProvider` with `theme` prop) is the mechanism. Define tokens, not raw CSS.

| Token | Purpose |
|-------|---------|
| `colorPrimary` | Primary actions, active nav items, links |
| `colorBgContainer` | Page/card backgrounds |
| `colorBgLayout` | App shell background (slightly offset from container) |
| `colorText` | Primary text |
| `colorTextSecondary` | Captions, metadata, timestamps |
| `colorBorder` | Subtle dividers and card borders |
| `colorError` | Destructive actions, validation errors |
| `colorSuccess` | Confirmation states |

Choose a neutral primary (slate blue, muted teal, or similar) that doesn't compete with photo content. Avoid saturated primaries — the photos should be the most colorful thing on screen.

### Typography

- Use Ant Design's default font stack (system fonts). No custom web fonts.
- Hierarchy through size and weight, not color. Three levels max:
  - **Page title** — `fontSizeHeading3` or similar
  - **Section/card title** — `fontSizeLG`
  - **Body/metadata** — `fontSize` (default)
- Monospace only for technical values (UIDs, coordinates) if displayed at all.

### Spacing

Use Ant Design's spacing tokens (`marginXS`, `marginSM`, `margin`, `marginLG`, etc.). Do not hardcode pixel values. Consistent spacing creates visual rhythm without explicit rules.

### Radius & Shadows

- Cards and containers: subtle border-radius via `borderRadius` token.
- Shadows: minimal. Use Ant Design's default elevation, don't add custom box-shadows.
- Photos in grids: no border-radius (photos should not be cropped at corners).

### Transitions

Use Ant Design's built-in motion tokens. No custom CSS transitions unless Ant Design components don't cover the interaction.

---

## Page Features

**Priority:** Gallery and Graph are the primary pages — they represent the two core ways to explore the app (photos and connections). Image detail and upload are closely tied to the gallery flow. People, events, places, and admin are supporting pages.

Design effort should reflect this priority: get the gallery and graph feeling right first, then build outward.

### Login Page

- Username and password fields
- Submit button with loading state
- Error message display for invalid credentials
- App name/branding
- No access to any other page without authentication

### Gallery Page (main page, `/`)

- Masonry or responsive grid of image thumbnails
- Sorted by upload date, newest first
- Filter controls: by person, event, place (autocomplete search to select)
- Image count display
- Infinite scroll or load-more pagination (cursor-based)
- Clicking a thumbnail navigates to image detail
- Empty state when no images exist

### Upload Page (`/upload`)

- Drag-and-drop zone for bulk image upload
- Upload progress indication per file
- Post-upload review flow: step through each uploaded image to:
  - Tag people (face tagger)
  - Add caption and taken date
  - Link to event and/or place
  - Rotate or delete
  - Skip to next
- Summary/completion state when all images reviewed

### Image Detail Page (`/images/:uid`)

- Full-size image display
- Face tag overlay: existing tags visible, clickable (navigate to person)
- Face tagger: click image to place new tag, search/select person
- Metadata panel: caption, taken date, upload date, file info
- Edit caption and taken date inline
- Linked event and place (with ability to set/change/remove)
- Rotate and delete actions (role-gated: editor+ for rotate, admin for delete)
- Download button

### People Page (`/people`)

- Searchable list/grid of all people
- Each entry shows: name, thumbnail (from a tagged photo if available)
- Click navigates to person detail
- Create new person action (role-gated: editor+)

### Person Page (`/people/:uid`)

- Profile header: name, birth/death dates, gender, nickname, description
- Edit profile inline (role-gated: editor+)
- Photos tab: grid of all images this person appears in
- Relationships tab: list of family and social connections with type labels
  - Add/edit/remove relationships (role-gated: editor+)
- Events tab: events this person attended (explicit + photo-derived)
- Places tab: places derived from photo locations
- Mini graph: neighborhood visualization showing immediate connections
- Born-at place (set/remove)

### Events Page (`/events`)

- List of all events
- Each entry shows: name, date range, description
- Click navigates to event detail (or inline expand)
- Create new event action (role-gated: editor+)
- Event detail shows: linked place (HELD_AT), photos from this event

### Places Page (`/places`)

- List of all places
- Each entry shows: name, address, description
- Click navigates to place detail (or inline expand)
- Create new place action (role-gated: editor+)
- Place detail shows: photos taken at this place, events held here

### Graph Page (`/graph`)

- Full-screen graph visualization (Cytoscape.js)
- Search to center on a person/event/place
- Node visual distinction by type (person, event, place — use shape or subtle color)
- Edge labels showing relationship type
- Click node to see summary details (sidebar or popover)
- Click-through to full detail page from summary
- Layout options: force-directed (default), hierarchical family tree
- Zoom and pan controls

### Admin Page (`/admin`)

- List of all user accounts
- Each entry shows: username, role, active status
- Edit user: change role, reset password
- Create new user: username, password, role
- Admin-only access (enforced by ProtectedRoute)

---

## Role-Based Visibility

Components should use the `useAuth` hook to conditionally render actions:

| Action | Admin | Editor | Viewer |
|--------|-------|--------|--------|
| View photos/graph/pages | Yes | Yes | Yes |
| Upload photos | Yes | Yes | No |
| Tag people, edit metadata | Yes | Yes | No |
| Create/edit people/events/places | Yes | Yes | No |
| Create/edit relationships | Yes | Yes | No |
| Delete anything | Yes | No | No |
| Access admin page | Yes | No | No |

---

## Shared UI Patterns

### Autocomplete Search

Used in: gallery filters, face tagger, relationship forms, event/place linking. Backed by the `/api/search` endpoint. Debounced input, minimum 2 characters.

### Empty States

Every list/grid should have a meaningful empty state — not just blank space. Indicate what the page is for and how to populate it.

### Loading States

Use Ant Design's `Spin` or skeleton components. Never show a blank page while data loads.

### Error States

Display user-friendly error messages. Network errors should suggest retrying. 401 errors are handled globally by the axios interceptor.

### Confirmation Dialogs

All destructive actions (delete image, remove relationship, remove tag) require confirmation before executing.

### Responsive Behavior

The app should be usable on tablet-width screens at minimum. Phone optimization is not required but layouts should not break below 768px.

### Relationship to Foundation Code

The design branch builds on top of existing foundation code (API client, hooks, types, auth context, i18n, route definitions). It may adjust this code where needed — for example, restructuring routes to support overlay navigation, or adding fields to types. But changes to the foundation should be minimal and purposeful. Don't rewrite the plumbing; extend it.
