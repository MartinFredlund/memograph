const sv = {
  // App
  appName: "MemoGraph",

  // Auth
  login: "Logga in",
  loggingIn: "Loggar in...",
  logout: "Logga ut",
  username: "Användarnamn",
  password: "Lösenord",
  invalidCredentials: "Felaktigt användarnamn eller lösenord",

  // Nav
  gallery: "Galleri",
  upload: "Ladda upp",
  people: "Personer",
  events: "Händelser",
  places: "Platser",
  graph: "Graf",
  admin: "Admin",

  // Gallery
  photos: "foton",
  noImages: "Inga bilder ännu",
  noImagesHint: "Ladda upp bilder för att komma igång",
  filterByPerson: "Filtrera på person",
  filterByEvent: "Filtrera på händelse",
  filterByPlace: "Filtrera på plats",
  loadMore: "Ladda fler",

  // Upload
  dragAndDrop: "Dra och släpp bilder här",
  orClickToSelect: "eller klicka för att välja",
  uploading: "Laddar upp...",
  uploadComplete: "Uppladdning klar",
  reviewImages: "Granska bilder",
  skip: "Hoppa över",
  next: "Nästa",
  previous: "Föregående",
  done: "Klar",

  // Image detail
  caption: "Bildtext",
  takenDate: "Fotograferingsdatum",
  uploadedAt: "Uppladdad",
  fileInfo: "Filinformation",
  download: "Ladda ner",
  rotate: "Rotera",
  delete: "Radera",
  confirmDelete: "Är du säker på att du vill radera?",
  tagPerson: "Tagga person",
  searchPerson: "Sök person...",

  // People
  noPeople: "Inga personer ännu",
  noPeopleHint: "Skapa en person eller tagga någon i en bild",
  createPerson: "Skapa person",
  name: "Namn",
  birthDate: "Födelsedatum",
  deathDate: "Dödsdatum",
  gender: "Kön",
  nickname: "Smeknamn",
  description: "Beskrivning",
  photosTab: "Bilder",
  relationshipsTab: "Relationer",
  eventsTab: "Händelser",
  placesTab: "Platser",
  bornAt: "Födelseort",

  // Relationships
  addRelationship: "Lägg till relation",
  parentOf: "Förälder till",
  partnerOf: "Partner med",
  social: "Social",
  since: "Sedan",
  context: "Kontext",
  relationshipType: "Relationstyp",
  removeRelationship: "Ta bort relation",

  // Events
  noEvents: "Inga händelser ännu",
  createEvent: "Skapa händelse",
  startDate: "Startdatum",
  endDate: "Slutdatum",
  heldAt: "Plats",

  // Places
  noPlaces: "Inga platser ännu",
  createPlace: "Skapa plats",
  address: "Adress",

  // Graph
  searchToCenter: "Sök för att centrera...",
  forceDirected: "Kraftstyrd",
  hierarchical: "Hierarkisk",

  // Admin
  users: "Användare",
  role: "Roll",
  active: "Aktiv",
  createUser: "Skapa användare",
  editUser: "Redigera användare",
  resetPassword: "Återställ lösenord",

  // Roles
  roleAdmin: "Administratör",
  roleEditor: "Redaktör",
  roleViewer: "Läsare",

  // Common
  save: "Spara",
  cancel: "Avbryt",
  edit: "Redigera",
  remove: "Ta bort",
  confirm: "Bekräfta",
  search: "Sök...",
  loading: "Laddar...",
  error: "Något gick fel",
  retry: "Försök igen",
  noResults: "Inga resultat",

  // Theme
  lightMode: "Ljust läge",
  darkMode: "Mörkt läge",

  // Language
  language: "Språk",
  swedish: "Svenska",
  english: "English",
} as const;

export type TranslationKey = keyof typeof sv;
export default sv;
