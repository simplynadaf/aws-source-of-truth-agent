import 'dotenv/config';

/**
 * Central env access with friendly errors, so every entrypoint fails the same
 * clear way instead of throwing a raw undefined deep inside the SDK.
 */
export function required(name: string): string {
  const v = process.env[name];
  if (!v || v.trim() === '') {
    throw new Error(
      `Missing ${name}. Copy .env.example to .env and fill it in. ` +
        `See README.md ("Configure") for where each value comes from.`,
    );
  }
  return v.trim();
}

export function optional(name: string, fallback: string): string {
  const v = process.env[name];
  return v && v.trim() !== '' ? v.trim() : fallback;
}

export const config = {
  get mcpUrl() {
    return required('SANITY_CONTEXT_MCP_URL');
  },
  get sanityToken() {
    return required('SANITY_ORGANIZATION_TOKEN');
  },
  get openaiKey() {
    return required('OPENAI_API_KEY');
  },
  get model() {
    return optional('OPENAI_MODEL', 'gpt-4o');
  },
  get projectId() {
    return optional('SANITY_PROJECT_ID', '(not set)');
  },
};
