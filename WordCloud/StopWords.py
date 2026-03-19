from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

"""
Centralized stop-word configuration for work-order text processing.
"""

KEEP_FROM_SKLEARN = {
    "still", "again", "same", "off", "out", "down"
}

CUSTOM_EXCLUDE = {
    # pleasantries / email filler
    "thank", "thanks", "hello", "hope",

    # request/admin words
    "contact", "questions", "question", "attached", "detail", "details",
    "info", "information", "request", "requesting", "requester",
    "order", "task", "service", "services", "support", "assist",
    "assistance", "provide", "provided", "generated", "assign",
    "assigned", "caller", "contacted", "regarding", "related",
    "billable", "vendor", "expenses", "charges", "charge", "cost",
    "requisitions", "department", "project", "team", "operations",

    # generic filler verbs / weak words
    "need", "needs", "needed", "like", "just", "make", "made",
    "come", "coming", "go", "going", "get", "gets", "getting",
    "having", "use", "used", "using", "possible", "currently",
    "additional", "following", "good", "let", "know", "look",
    "looks", "want", "really", "able", "appears", "believe",
    "think", "said", "note",

    # weak generic problem words
    "issue", "issues", "problem", "problems",

    # location / orientation words
    "center", "room", "rooms", "floor", "floors", "hall", "hallway",
    "hallways", "office", "offices", "area", "areas", "space",
    "outside", "inside", "near", "located", "location", "main",
    "right", "left", "north", "south", "east", "west", "corner",
    "level", "suite", "basement", "lobby", "entry", "entrance",
    "storage", "closet", "dock", "loading", "station", "courtyard",
    "patio", "garage", "quad", "section", "middle", "rear",
    "building", "buildings", "house", "college", "commons",
    "lab", "classroom", "auditorium", "conference", "lecture",
    "library", "lounge", "servery", "dining", "venue", "campus",
    "university", "shop", "place",

    # time / scheduling words
    "today", "tomorrow", "yesterday", "morning", "afternoon",
    "evening", "night", "day", "days", "week", "weeks",
    "monday", "tuesday", "wednesday", "thursday", "friday",
    "saturday", "sunday", "january", "february", "march", "april",
    "june", "july", "august", "september", "october", "november",
    "december", "jan", "feb", "oct",

    # event / population words
    "event", "meeting", "game", "concert", "football", "annual",
    "student", "students", "staff", "faculty", "people", "public",
    "president", "alumni",

    # contact / communication tokens
    "phone", "email", "ext", "number",

    # restroom location labels that are usually redundant once toilet/restroom/sink stay
    "men", "women", "mens", "womens", "ladies",

    # campus-specific / building-specific terms
    "rice", "edu", "brc", "grb", "dbh", "alm", "coa", "fsc", "rmc", "rupd",
    "duncan", "brown", "baker", "lovett", "fondren", "hanszen",
    "martel", "mcmurtry", "sewall", "wiess", "brockman", "anderson",
    "kraft", "moody", "mcnair", "rawls", "huff", "keck", "ryon",
    "tudor", "garrett", "jones",

    # person names showing up in the counts
    "rodriguez", "monica", "frydl", "juan", "david", "matt", "garcia",
    "munira", "vejlani", "olivia", "james", "dewayne", "sid", "allen",
    "mosquinski", "bradley", "calvin", "abbatessa", "gutierrez",
    "brad", "thang", "anh", "mike", "maria", "francisco", "rudy",
    "hannes", "jonathan", "sanchez", "minh", "harper", "urbano",
    "nguyen", "benny", "waldron", "thacker", "layton", "herring",
    "connor", "tegan", "tegang",

    # tokenization artifacts
    "doesn", "isn", "won", "don", "didn", "aren", "wasn", "weren",
    "hasn", "haven", "couldn", "wouldn", "shouldn", "attn", "xxxx"
}

STOP_WORDS = (set(ENGLISH_STOP_WORDS) - KEEP_FROM_SKLEARN) | CUSTOM_EXCLUDE
SHORT_KEEP = {"ac"}