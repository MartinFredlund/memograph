import type { TranslationKey } from "./sv";

const en: Record<TranslationKey, string> = {
  // App
  appName: "MemoGraph",

  // Auth
  login: "Log in",
  loggingIn: "Logging in...",
  logout: "Log out",
  username: "Username",
  password: "Password",
  invalidCredentials: "Invalid username or password",

  // Nav
  gallery: "Gallery",
  upload: "Upload",
  people: "People",
  events: "Events",
  places: "Places",
  graph: "Graph",
  admin: "Admin",

  // Gallery
  photos: "photos",
  noImages: "No images yet",
  noImagesHint: "Upload images to get started",
  filterByPerson: "Filter by person",
  filterByEvent: "Filter by event",
  filterByPlace: "Filter by place",
  loadMore: "Load more",

  // Upload
  dragAndDrop: "Drag and drop images here",
  orClickToSelect: "or click to select",
  uploading: "Uploading...",
  uploadComplete: "Upload complete",
  reviewImages: "Review images",
  skip: "Skip",
  next: "Next",
  previous: "Previous",
  done: "Done",

  // Image detail
  caption: "Caption",
  takenDate: "Date taken",
  uploadedAt: "Uploaded",
  fileInfo: "File info",
  download: "Download",
  rotate: "Rotate",
  delete: "Delete",
  confirmDelete: "Are you sure you want to delete?",
  tagPerson: "Tag person",
  searchPerson: "Search person...",

  // People
  noPeople: "No people yet",
  noPeopleHint: "Create a person or tag someone in a photo",
  createPerson: "Create person",
  name: "Name",
  birthDate: "Birth date",
  deathDate: "Death date",
  gender: "Gender",
  nickname: "Nickname",
  description: "Description",
  photosTab: "Photos",
  relationshipsTab: "Relationships",
  eventsTab: "Events",
  placesTab: "Places",
  bornAt: "Born at",

  // Relationships
  addRelationship: "Add relationship",
  parentOf: "Parent of",
  partnerOf: "Partner of",
  social: "Social",
  since: "Since",
  context: "Context",
  relationshipType: "Relationship type",
  removeRelationship: "Remove relationship",

  // Events
  noEvents: "No events yet",
  createEvent: "Create event",
  startDate: "Start date",
  endDate: "End date",
  heldAt: "Location",

  // Places
  noPlaces: "No places yet",
  createPlace: "Create place",
  address: "Address",

  // Graph
  searchToCenter: "Search to center...",
  forceDirected: "Force-directed",
  hierarchical: "Hierarchical",

  // Admin
  users: "Users",
  role: "Role",
  active: "Active",
  createUser: "Create user",
  editUser: "Edit user",
  resetPassword: "Reset password",

  // Roles
  roleAdmin: "Administrator",
  roleEditor: "Editor",
  roleViewer: "Viewer",

  // Common
  save: "Save",
  cancel: "Cancel",
  edit: "Edit",
  remove: "Remove",
  confirm: "Confirm",
  search: "Search...",
  loading: "Loading...",
  error: "Something went wrong",
  retry: "Try again",
  noResults: "No results",

  // Theme
  lightMode: "Light mode",
  darkMode: "Dark mode",

  // Language
  language: "Language",
  swedish: "Svenska",
  english: "English",
};

export default en;
