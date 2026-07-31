const ACCESS_TOKEN_STORAGE_KEY = "minfy-resolve.access-token";

function readStoredToken() {
  try {
    return window.sessionStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

function writeStoredToken(token: string | null) {
  try {
    if (token) {
      window.sessionStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, token);
      return;
    }
    window.sessionStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
  } catch {
    // Session persistence is a convenience for browser refreshes. Auth still
    // works for the active page session when storage is unavailable.
  }
}

let accessToken: string | null = readStoredToken();

export function getAccessToken() { return accessToken; }
export function hasAccessToken() { return accessToken !== null; }
export function setAccessToken(token: string | null) {
  accessToken = token;
  writeStoredToken(token);
}
