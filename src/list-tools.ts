/**
 * Lists the tools the Sanity Context MCP exposes. This is the fastest way to
 * confirm the endpoint + token work AND which retrieval mode you are in:
 *   - Knowledge Base mode -> you should see `initial_context` + `knowledge_base_read`
 *   - GROQ mode           -> you should see `initial_context` + `groq_query` (+ schema_explorer, array_field_reader)
 *
 * Troubleshooting:
 *   401                    -> token missing/malformed
 *   403 contextGrantRequired -> token is not an ORG token with Context Viewer
 *   empty tool list        -> a `tools=` allowlist named only out-of-mode tools
 */
import { createSanityContextClient } from './mcp.js';

function explain(err: unknown): string {
  const msg = (err as Error)?.message ?? String(err);
  const status = (err as { statusCode?: number })?.statusCode;
  if (status === 401 || /HTTP 401/.test(msg)) {
    return (
      'HTTP 401 from Sanity. The token is missing, malformed, or not a member of the org.\n' +
      '  - Confirm SANITY_ORGANIZATION_TOKEN is an ORG-level token (Manage > org > API > Tokens).\n' +
      '  - Confirm the org id in the URL matches that org.'
    );
  }
  if (status === 403 || /contextGrantRequired/.test(msg)) {
    return (
      'HTTP 403 contextGrantRequired. The token is not an org token with Context Viewer.\n' +
      '  - Recreate the token at the ORG level with Context Viewer (or Editor) permission.'
    );
  }
  return msg;
}

const client = await createSanityContextClient().catch((err) => {
  console.error('\u2717 Could not connect to the Sanity Context MCP.\n\n' + explain(err));
  process.exit(1);
});

try {
  const { tools } = await client.listTools();
  if (!tools.length) {
    console.log('No tools returned. Check the `tools=` allowlist and the mode (see comments).');
  } else {
    console.log(`Context MCP exposed ${tools.length} tool(s):\n`);
    for (const t of tools) {
      console.log(`  \u2022 ${t.name}\n      ${t.description ?? ''}`);
    }
    const names = tools.map((t) => t.name);
    const mode = names.includes('knowledge_base_read')
      ? 'Knowledge Base mode'
      : names.includes('groq_query')
        ? 'GROQ mode'
        : 'unknown';
    console.log(`\nDetected: ${mode}`);
  }
} catch (err) {
  console.error('\u2717 Could not list tools.\n\n' + explain(err));
  process.exitCode = 1;
} finally {
  await client.close();
}
