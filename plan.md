# GraphWeb — Image-Driven Memory Bank & Family/Social Graph

## Context

A self-hosted personal memory bank centered around **photos**. The primary workflow is: upload images → tag who's in them (click on faces) → optionally link to an event or place → build up a family tree and social graph over time. The graph database captures how people are related (family and social relationships), and every image serves as a memory anchoring those connections.

**Scale:** Small (< 1,000 nodes). This is a personal/family tool, not enterprise.

## Tech Stack

| Layer | Choice |
|-------|--------|
| Backend | Python / FastAPI |
| Graph DB | Neo4j 5 Community Edition |
| Image Storage | MinIO (S3-compatible) |
| Frontend | React + TypeScript + Ant Design + Cytoscape.js |
| Data Fetching | @tanstack/react-query |
| Reverse Proxy | Traefik v3 |
| CI/CD | GitHub Actions |
| Build Tool | Vite (frontend), uv (backend) |

## Core Workflow (Image-Driven)

1. **Upload** — User uploads one or more photos via drag-and-drop
2. **Tag people** — On each photo, user clicks on faces to place a tag marker, then searches/selects a person (or creates a new one inline). Tag coordinates (x%, y%) are stored on the `APPEARS_IN` relationship.
3. **Add context** (optional) — Link photo to an event ("Christmas 2024") and/or a place ("Grandma's house"). Create these inline if they don't exist.
4. **Add date/description** (optional) — Date the photo was taken, add a caption.
5. **Browse** — Gallery view (main page), person detail pages showing all their photos, graph explorer showing the relationship web.

## Project Structure

```
graphweb/
├── .github/workflows/        # CI + CD pipelines
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app + lifespan
│   │   ├── config.py          # Pydantic Settings
│   │   ├── dependencies.py    # get_db_session, get_current_user
│   │   ├── auth/              # login, register, JWT, RBAC
│   │   ├── people/            # Person CRUD
│   │   ├── events/            # Event CRUD
│   │   ├── places/            # Place CRUD
│   │   ├── relationships/     # Relationship CRUD (family/social types)
│   │   ├── images/            # Upload, face-tag coordinates, presigned URLs
│   │   ├── graph/             # Graph exploration + search endpoints
│   │   └── db/                # Neo4j driver, session, seed script
│   ├── tests/
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── api/               # Axios client + typed API functions
│   │   ├── auth/              # AuthContext, ProtectedRoute, LoginPage
│   │   ├── pages/
│   │   │   ├── GalleryPage.tsx      # Main page — image grid/timeline
│   │   │   ├── ImageDetailPage.tsx  # Single image with face tags + metadata
│   │   │   ├── UploadPage.tsx       # Upload + tagging workflow
│   │   │   ├── PersonPage.tsx       # Person profile: photos, relationships, bio
│   │   │   ├── PeoplePage.tsx       # List/search all people
│   │   │   ├── GraphPage.tsx        # Full family/social graph explorer
│   │   │   ├── EventsPage.tsx       # Events list
│   │   │   ├── PlacesPage.tsx       # Places list
│   │   │   └── AdminPage.tsx        # User management
│   │   ├── components/
│   │   │   ├── AppLayout.tsx        # Ant Design Layout with sidebar
│   │   │   ├── ImageCard.tsx        # Gallery thumbnail with hover tags
│   │   │   ├── FaceTagger.tsx       # Click-to-tag overlay on image
│   │   │   ├── PersonSearch.tsx     # Autocomplete search for people
│   │   │   ├── RelationshipForm.tsx # Add/edit family/social relationship
│   │   │   ├── GraphViewer.tsx      # Cytoscape.js wrapper
│   │   │   └── ImageUploader.tsx    # Drag-and-drop upload component
│   │   ├── hooks/
│   │   └── utils/
│   │       └── cytoscape-config.ts
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
├── docker/
│   ├── docker-compose.yml
│   ├── docker-compose.dev.yml
│   ├── cloudflared/config.yml   # Tunnel config (hostname → service mapping)
│   └── traefik/traefik.yml
├── Makefile
└── .env.example
```

## Neo4j Data Model

### Nodes

**`:Person`** — `uid`, `name`, `birth_date?`, `death_date?`, `gender?`, `nickname?`, `description?`, `created_at`, `updated_at`
**`:Event`** — `uid`, `name`, `start_date?`, `end_date?`, `description?`, `created_at`, `updated_at`
**`:Place`** — `uid`, `name`, `address?`, `latitude?`, `longitude?`, `description?`, `created_at`, `updated_at`
**`:Image`** — `uid`, `filename`, `object_key`, `content_type`, `size_bytes`, `width?`, `height?`, `taken_date?`, `caption?`, `uploaded_at`
**`:User`** — `uid`, `username`, `hashed_password`, `role`, `is_active`, `created_at`, `updated_at`
- Each User is linked to a Person node via `(:User)-[:IS_PERSON]->(:Person)`
- Most users represent themselves in the graph; their Person node is the anchor for their viewpoint
- A Person can exist without a User account (most people in the graph won't have logins)
- When a new User registers, they can link to an existing Person or create one

### Relationships (Fixed Family + Flexible Social)

Family relationships are fixed types — graph traversal depends on them. Social relationships use a single `SOCIAL` type with a user-defined `type` property, allowing custom relationship kinds.

**Family types** (Person → Person, fixed):
| Type | Meaning | Properties |
|------|---------|------------|
| `PARENT_OF` | Direct parent→child. Derives grandparent (2 hops), sibling (shared parent), cousin, uncle/aunt, etc. | `since?` |
| `PARTNER_OF` | Marriage/partnership. Derives in-laws via traversal. | `since?` |

**Social type** (Person → Person, flexible):
| Type | Meaning | Properties |
|------|---------|------------|
| `SOCIAL` | Any social connection. Defaults: "friend", "colleague", "neighbor". Users can add custom types (e.g., "godparent", "mentor", "roommate"). | `type`, `since?`, `context?` |

**Derived relationship examples** (computed by Cypher queries, not stored):
- Grandparent: `(gp)-[:PARENT_OF]->(p)-[:PARENT_OF]->(person)`
- Sibling: `(person)<-[:PARENT_OF]-(parent)-[:PARENT_OF]->(sibling)`
- Cousin: `(person)<-[:PARENT_OF]-(p1)<-[:PARENT_OF]-(gp)-[:PARENT_OF]->(p2)-[:PARENT_OF]->(cousin)`
- In-law: traverse through `PARTNER_OF` + `PARENT_OF` combinations

**User-Person link:**
- `IS_PERSON` (User → Person) — links a login account to their representation in the graph

**Image associations:**
- `UPLOADED_BY` (Image → User) — tracks who uploaded the image
- `APPEARS_IN` (Person → Image) — **with `tag_x` and `tag_y` (float, 0-100%)** for click-to-tag position
- `TAKEN_AT` (Image → Place)
- `FROM_EVENT` (Image → Event)

**Entity cross-references:**
- `BORN_AT` (Person → Place) — optional birth location
- `ATTENDED` (Person → Event)
- `HELD_AT` (Event → Place)
- `LIVES_AT` (Person → Place) — properties: `since?`

### Constraints
```cypher
CREATE CONSTRAINT person_uid FOR (p:Person) REQUIRE p.uid IS UNIQUE;
CREATE CONSTRAINT event_uid FOR (e:Event) REQUIRE e.uid IS UNIQUE;
CREATE CONSTRAINT place_uid FOR (p:Place) REQUIRE p.uid IS UNIQUE;
CREATE CONSTRAINT image_uid FOR (i:Image) REQUIRE i.uid IS UNIQUE;
CREATE CONSTRAINT user_uid FOR (u:User) REQUIRE u.uid IS UNIQUE;
CREATE CONSTRAINT user_username FOR (u:User) REQUIRE u.username IS UNIQUE;
```

## Network Architecture

```
Internet → Cloudflare (SSL, DDoS, caching)
         → cloudflared tunnel (outbound-only, no open ports)
         → Traefik (internal routing)
         → backend (/api/*) | frontend (/*) | neo4j | minio
```

- **Cloudflare** handles public DNS, SSL termination, and edge protection
- **cloudflared** runs as a Docker container, creates an outbound tunnel to Cloudflare — no firewall ports to open
- **Traefik** handles internal service routing (`/api/*` → backend, `/*` → frontend)
- Other web apps on the same server are unaffected — each gets its own public hostname in the Cloudflare Tunnel config (e.g., `photos.yourdomain.com` → this app's Traefik)

## Docker Compose Services

6 services: `cloudflared`, `traefik`, `neo4j`, `minio`, `backend`, `frontend`

| Service | Image | Purpose |
|---------|-------|---------|
| `cloudflared` | `cloudflare/cloudflared` | Tunnel to Cloudflare edge, routes `photos.yourdomain.com` to Traefik |
| `traefik` | `traefik:v3` | Internal reverse proxy, routes `/api/*` → backend, `/*` → frontend |
| `neo4j` | `neo4j:5-community` | Graph database, volume for `/data` |
| `minio` | `minio/minio` | Image object storage, volume for `/data` |
| `backend` | Build from `backend/Dockerfile` | FastAPI API server |
| `frontend` | Build from `frontend/Dockerfile` | React app served by nginx |

- Dev override (`docker-compose.dev.yml`) skips cloudflared, mounts source code, enables hot reload
- Neo4j and MinIO get named volumes for persistence
- No ports exposed to host in production — all traffic flows through the tunnel

## Authentication & RBAC

- JWT-based (HS256), stored in localStorage
- Default admin user seeded on first startup from env vars
- Admins create other users via API

| Action | Admin | Editor | Viewer |
|--------|-------|--------|--------|
| View photos/graph | Yes | Yes | Yes |
| Upload photos / tag people | Yes | Yes | No |
| Create/edit people/events/places | Yes | Yes | No |
| Delete anything | Yes | No | No |
| Manage users | Yes | No | No |

## Key UI Components

### FaceTagger (click-to-tag on images)
- Renders the image at full size in a container
- On click: places a circular marker at the click position, opens a `PersonSearch` popover
- User searches for an existing person or creates a new one inline
- Saves `APPEARS_IN` relationship with `tag_x`, `tag_y` as percentage coordinates
- On hover over existing tags: shows person name tooltip
- On the image detail page: all tags are visible and clickable (navigate to person)

### Gallery Page (main page)
- Grid of image thumbnails, sorted by date (newest first)
- Filter/search by: person name, event, place, date range
- Clicking a thumbnail opens the image detail page

### Person Page
- Profile header: name, birth date, description
- **Photos tab**: grid of all images they appear in
- **Relationships tab**: family tree view + social connections, with ability to add/edit
- **Mini graph**: Cytoscape.js showing this person's immediate connections

### Graph Explorer
- Full-screen Cytoscape.js visualization
- Search to center on a person
- Node colors: Person=blue, Event=orange, Place=green
- Edge labels show relationship type
- Click node → sidebar with details + link to full page
- Family tree layout option (hierarchical) + force-directed option

## Implementation Order

### Phase 1: Foundation
1. [x] Init monorepo, `.gitignore`, `Makefile`
2. [x] `docker-compose.yml` — neo4j + minio + traefik
3. [x] FastAPI skeleton: health endpoint, config, Neo4j driver lifespan, MinIO client
4. [x] DB seed script (constraints, indexes, default admin user)
5. [x] Auth module (register, login, JWT, RBAC)

### Phase 2: People & Relationships
1. [x] Person CRUD (schemas, service with Cypher, router)
2. [x] Relationship CRUD with predefined family/social types
3. [x] Events and Places CRUD (simpler, same pattern)
4. [x] Backend tests

### Phase 3: Image Upload & Tagging
1. [x] MinIO storage wrapper (upload, presigned URL, delete — thumbnail generation deferred to Phase 6)
2. [x] Bulk image upload endpoint (multipart → MinIO + Image nodes in Neo4j, returns list of created image UIDs)
3. [x] Image rotate/delete endpoints (basic image management during review)
4. [x] Face-tag endpoint: `POST /api/images/{uid}/tags` — saves `APPEARS_IN` with coordinates
5. [x] Remove face-tag endpoint: `DELETE /api/images/{uid}/tags/{person_uid}`
6. Image association endpoints: link to event/place
7. Image download endpoint (presigned URL with `Content-Disposition: attachment`)
8. Image list/search endpoint with filters

### Phase 4: Graph API
1. Graph exploration query (Cytoscape-formatted JSON)
2. Person neighborhood query (for mini-graphs on person pages)
3. Search endpoint (full-text across all entity types)

### Phase 5: Frontend
1. Vite + React + TS + Ant Design scaffold
2. API client with JWT interceptor
3. Auth context + login page
4. AppLayout with sidebar navigation + routing
5. **GalleryPage** — image grid with filters (this is the main page)
6. **UploadPage** — bulk drag-and-drop upload → post-upload review flow (step through each image: tag people, rotate, add metadata, delete unwanted, skip)
7. **ImageDetailPage** — full image view with FaceTagger overlay + metadata (also used as the review step UI)
8. **FaceTagger component** — click-to-tag with person search popover
9. **PersonPage** — profile with photos tab, relationships tab, mini graph
10. **PeoplePage** — searchable list of all people
11. **GraphPage** — full Cytoscape.js explorer
12. Events/Places pages (simple list views)
13. AdminPage for user management

### Phase 6: CI/CD, Backup & Polish
1. GitHub Actions CI (lint + test backend, lint + build frontend)
2. GitHub Actions CD (build + push Docker images to GHCR)
3. Frontend Dockerfile (multi-stage with nginx)
4. Image thumbnails for gallery performance
5. Backup script — Neo4j dump (`neo4j-admin database dump`) + MinIO data tar, scheduled via cron, with rolling retention (e.g., 30 daily). Off-site destination TBD (external drive, Backblaze B2, rsync to another machine).

## Post-MVP Ideas
- Duplicate image detection (perceptual hashing to catch near-duplicates, not just exact matches)
- Face detection / auto-tag suggestions (e.g., with face_recognition library)
- Batch upload with EXIF date/location extraction
- Timeline view (photos on a chronological timeline)
- Map view for places (Leaflet)
- Family tree layout (hierarchical Cytoscape.js or d3-dag)
- Data export (JSON, CSV)
- Refresh tokens
- `PROFILE_IMAGE` relationship (Person → Image) — dedicated profile picture per person
- `COVER_IMAGE` relationship (Event → Image) — dedicated cover image per event
- Safe delete for Person/Event/Place nodes (relationship checks, soft-delete, confirmation)
- Video support (chunked upload, `:Video` or `:Media` node, ffmpeg thumbnails, `APPEARS_IN` without coordinates — people linked to videos but no spatial face tagging)
- MinIO/Neo4j orphan reconciliation: if Cypher fails after a successful MinIO upload, the object is left dangling. Add a background job or two-phase cleanup to detect and remove orphans.

## Verification
1. `make up` → all 5 containers healthy
2. Login as admin → create a person → verify in Neo4j browser
3. Upload an image → verify in MinIO console → verify presigned URL loads
4. Click-to-tag a person in the image → verify `APPEARS_IN` relationship with coordinates
5. Create family relationships → verify graph explorer shows connections
6. Gallery page shows uploaded images, filter by person works
7. Person page shows all their tagged photos
8. RBAC: viewer can browse but not upload, editor can upload and tag, admin can delete
9. `git push` → GitHub Actions CI passes
