/**
 * The AWS "Source of Truth" agent (Sanity Challenge, Path One).
 *
 * It answers questions like "which value is current?" over a Sanity Context
 * Knowledge Base built from AWS docs + a structured quota/pricing dataset.
 * The whole point (the challenge's bar): the answer only works BECAUSE the
 * content is structured. When the docs, the pricing page, and the console
 * disagree, the KB has already reconciled them into an entry with citations,
 * so the agent surfaces the resolved value AND the losing claim, each with its
 * source - something a plain keyword search cannot do.
 *
 * Usage:
 *   npm run ask -- "What is the current default vCPU quota for on-demand Standard instances?"
 */
import { generateText, stepCountIs } from 'ai';
import { openai } from '@ai-sdk/openai';
import { createSanityContextClient } from './mcp.js';
import { config } from './config.js';

const SYSTEM_PROMPT = `You are the AWS Source of Truth agent.

You answer AWS configuration questions (service quotas, limits, version
compatibility, regional availability, pricing figures) by reading a Sanity
Context Knowledge Base through the provided MCP tools. The Knowledge Base was
built ahead of time from primary AWS sources and has already reconciled
conflicting sources into cited entries.

Rules (non-negotiable):
1. Ground every claim in retrieved content. First call the tool that returns the
   Knowledge Base outline (initial_context), then read the specific entries whose
   paths match the question (knowledge_base_read). In GROQ mode, inspect the
   schema then query it. NEVER answer from your own training knowledge of AWS.
2. Cite the source. For every value you state, name the entry/source it came from
   exactly as it appears in the retrieved content. If you cannot find it, say so.
3. When sources disagree, show BOTH claims. State the reconciled/current value
   first, then note the conflicting value and where it came from, and why the
   current one wins (recency, official precedence) if the entry says so. Do not
   silently pick one.
4. You are read-only. You only read content; you never suggest changing the
   dataset or running a write.
5. Be concise and direct. No em dashes.`;

async function main() {
  const question = process.argv.slice(2).join(' ').trim();
  if (!question) {
    console.error('Ask something, e.g.:\n  npm run ask -- "What is the current default vCPU quota for Standard on-demand instances in us-east-1?"');
    process.exit(1);
  }

  const client = await createSanityContextClient().catch((err) => {
    const msg = (err as Error)?.message ?? String(err);
    if (/HTTP 401/.test(msg)) {
      console.error('Could not connect: HTTP 401. Use an ORG-level token with Context Viewer, and check the org id in the URL.');
    } else if (/contextGrantRequired|HTTP 403/.test(msg)) {
      console.error('Could not connect: HTTP 403 contextGrantRequired. The token needs Context Viewer at the org level.');
    } else {
      console.error('Could not connect to the Sanity Context MCP:', msg);
    }
    process.exit(1);
  });
  try {
    const tools = await client.tools();

    const result = await generateText({
      model: openai(config.model),
      system: SYSTEM_PROMPT,
      prompt: question,
      tools,
      // Allow the agent to orient (outline) then read entries then answer.
      stopWhen: stepCountIs(8),
    });

    console.log('\n=== Answer ===\n');
    console.log(result.text.trim());

    // Show the tool trail so the writeup can prove the agent used structured
    // content (a named judging criterion), not a keyword guess.
    const calls = result.steps.flatMap((s) => s.toolCalls ?? []);
    if (calls.length) {
      console.log('\n=== Tool trail (proof it read the structured KB) ===');
      for (const c of calls) {
        console.log(`  - ${c.toolName}(${JSON.stringify(c.input)})`);
      }
    }
    console.log(`\nSanity project id for submission: ${config.projectId}`);
  } finally {
    await client.close();
  }
}

main().catch((err) => {
  console.error('\nAgent error:', (err as Error).message);
  process.exit(1);
});
