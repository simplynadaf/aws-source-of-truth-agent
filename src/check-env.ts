/**
 * Quick sanity check that the environment is wired before you try the agent.
 * Does NOT hit the network - just verifies the vars are present and shaped right.
 */
import { config } from './config.js';

function ok(label: string, value: string) {
  console.log(`  \u2713 ${label}: ${value}`);
}

try {
  const url = config.mcpUrl;
  const mode = /mode=knowledge_base/.test(url)
    ? 'knowledge_base (forced via URL)'
    : /mode=groq/.test(url)
      ? 'groq (forced via URL)'
      : 'auto (decided by the MCP sources)';
  console.log('Environment looks good:\n');
  ok('MCP URL host', new URL(url).host);
  ok('Retrieval mode', mode);
  ok('Org token', `set (${config.sanityToken.slice(0, 4)}\u2026, ${config.sanityToken.length} chars)`);
  ok('OpenAI key', `set (${config.openaiKey.length} chars)`);
  ok('Model', config.model);
  ok('Project id (for submission)', config.projectId);
  if (!/knowledgeBases=kb/.test(url) && !/mode=groq/.test(url)) {
    console.log(
      '\n  note: no knowledgeBases=kb... param found. That is fine if the KB is\n' +
        '        attached as a source on the MCP endpoint itself. Otherwise add\n' +
        '        ?mode=knowledge_base&knowledgeBases=kbXXXX to the URL.',
    );
  }
  console.log('\nNext: npm run list-tools');
} catch (err) {
  console.error('\u2717 ' + (err as Error).message);
  process.exit(1);
}
