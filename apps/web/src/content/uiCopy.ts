export const copy = {
  app: {
    name: "Technical Knowledge Platform"
  },
  action: {
    signOut: "Sign out",
    openSearch: "Search past solutions",
    close: "Close",
    retry: "Try again",
    search: "Search",
    clearFilters: "Clear filters",
    viewSolution: "View solution"
  },
  nav: {
    dashboard: "Dashboard",
    search: "Search solutions",
    submit: "Log a solved problem",
    reviews: "Reviews",
    profile: "My profile",
    settings: "Administration"
  },
  mobile: {
    menu: "Open navigation",
    closeMenu: "Close navigation"
  },
  dashboard: {
    title: "Find a past solution",
    searchHint: "Describe the problem, error message, technology, or environment.",
    logPrompt: "Solved something worth sharing?",
    logAction: "Log a solved problem",
    recent: "Recent verified solutions",
    empty: "No verified solutions are available to you yet."
  },
  search: {
    title: "Search past solutions",
    placeholder: "Paste an error message or describe the roadblock",
    emptyTitle: "Start with the problem you are trying to solve",
    emptyBody: "Search uses past solutions that you are allowed to access.",
    filters: "Filters",
    verifiedOnly: "Verified only",
    sort: "Sort results",
    sortRelevance: "Relevance",
    sortNewest: "Most recently updated",
    generateSummary: "Generate grounded summary",
    summaryUnavailable: "Grounded summary is temporarily unavailable.",
    sources: "Sources",
    summary: "Summary of matching solutions",
    appliedQuery: "Results for",
    verifiedResults: "Showing verified solutions",
    resultCount: "Matching solutions",
    preview: "Preview solution",
    noAnswerTitle: "No reliable match was found",
    noAnswerBody: "Add the exact error message, affected technology or environment to improve your search.",
    clear: "Clear search",
    previousPage: "Previous page",
    nextPage: "Next page"
  },
  foundation: {
    phaseLabel: "Authenticated foundation",
    localStack: "Local stack",
    statusEyebrow: "Project foundation",
    title: "Search past solutions",
    description:
      "The approved stack is starting here: React, FastAPI, PostgreSQL with pgvector, and explicit service health checks.",
    webLabel: "Web",
    webReady: "Frontend is running.",
    apiLabel: "API",
    checkingApi: "Checking API health.",
    apiReady: "API health check passed.",
    apiUnavailable: "API health check failed.",
    signedIn: "Signed in",
    dashboardNotice: "Authentication is active. Solution discovery begins in a later phase."
  },
  login: {
    title: "Sign in to the knowledge platform",
    email: "Work email",
    password: "Password",
    submit: "Sign in",
    submitting: "Signing in",
    invalid: "We could not sign you in with those details.",
    description: "Use your approved work account to access internal technical knowledge.",
    emailInvalid: "Enter a valid work email address.",
    passwordInvalid: "Enter a password between 8 and 128 characters."
  },
  shell: {
    collapseNavigation: "Collapse navigation",
    expandNavigation: "Expand navigation",
    toggleTheme: "Toggle theme",
    openUserMenu: "Open user menu",
    primaryNavigation: "Primary navigation",
    mobileNavigation: "Mobile navigation"
  },
  command: {
    title: "Search and commands",
    hint: "Type to search pages and actions",
    noResults: "No matching commands",
    shortcut: "Ctrl K"
  },
  page: {
    notFoundTitle: "This page is not available",
    notFoundBody: "Check the address or return to the dashboard.",
    adminTitle: "Administration",
    adminBody: "Administration tools are available to administrators only.",
    solutionTitle: "Solution details",
    solutionBody: "Open a solution from search or an approved link.",
    authoringBody: "Create and edit solution drafts in the authoring workflow.",
    reviewsBody: "Review submitted solutions that are available to you."
  },
  detail: {
    problem: "Problem",
    symptoms: "Symptoms",
    rootCause: "Root cause",
    resolution: "Resolution",
    code: "Code and commands",
    solvedBy: "Solved by"
  },
  state: {
    loading: "Loading",
    comingSoon: "This workflow is not available yet.",
    permissionTitle: "You do not have access to this content",
    permissionBody: "If you need access, contact the solution owner or an administrator.",
    notFoundTitle: "This solution is not available",
    notFoundBody: "It may have been removed or you may not have access to it.",
    networkTitle: "We could not complete that request",
    networkBody: "Check your connection and try again."
  }
} as const;
