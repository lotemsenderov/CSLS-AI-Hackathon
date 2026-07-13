// Skill 4: API Client. Owner: feature/frontend-ui branch.
// Wraps /fields and /search per API_CONTRACT.md.

const BASE_URL = "http://localhost:8000";

export async function fetchFields() {
  // TODO: GET `${BASE_URL}/fields`, return the `fields` array, handle errors
  throw new Error("not implemented");
}

export async function searchConferences(field, query) {
  // TODO: GET `${BASE_URL}/search?field=...&query=...`, return `results`, handle errors
  throw new Error("not implemented");
}
