import path from "node:path";
import { fileURLToPath } from "node:url";

const dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Pin the tracing root to this app (a stray lockfile elsewhere on disk would
  // otherwise be inferred as the workspace root).
  outputFileTracingRoot: dirname,
};

export default nextConfig;
