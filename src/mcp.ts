import { createMCPClient } from '@ai-sdk/mcp';
import { config } from './config.js';

/**
 * Creates a Sanity Context MCP client over Streamable HTTP with the org token
 * as a bearer header. Read-only in both GROQ and Knowledge Base mode.
 *
 * The caller is responsible for `await client.close()`.
 */
export async function createSanityContextClient() {
  return createMCPClient({
    transport: {
      type: 'http',
      url: config.mcpUrl,
      headers: {
        Authorization: `Bearer ${config.sanityToken}`,
        // Sanity Context speaks JSON-RPC over SSE-capable HTTP.
        Accept: 'application/json, text/event-stream',
      },
    },
  });
}
