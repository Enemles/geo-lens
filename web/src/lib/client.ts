import createClient from "openapi-fetch";

import type { paths } from "@/lib/api/schema";

export const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

// Fully typed against the backend's OpenAPI schema: paths, methods, query
// params, request bodies, and responses are all checked at compile time.
export const api = createClient<paths>({ baseUrl: apiBaseUrl });
