# Project facts (source of truth for config + submission)

## Sanity
- Project name: aws-source-of-truth
- Project ID: 0q5ohtvv        # HARD submission requirement (goes in the Dev.to post)
- Organization ID: op7a9oe06
- Plan: Growth Trial (Context + Knowledge Bases available)
- Dataset: production (to be created/confirmed)
- Owner: Sarvar Nadaf

## Stack (decided 2026-09-28)
- Model: amazon.nova-pro-v1:0 on Amazon Bedrock (VERIFIED working in us-east-1 via Converse)
- Agent framework: Strands Agents (Python)
- Structured content: Sanity Context MCP + awsFact schema/Knowledge Base
- Live cross-check: AWS Pricing MCP + read-only Service Quotas (the unique differentiator)
- Region: us-east-1

## Challenge
- Path One (Sanity Challenge, dev.to)
- Submissions due: 2026-10-04 23:59 PDT
- Required tag: #sanitychallenge

## Decisions locked (2026-09-28, from research + real checks)
- GitHub target: simplynadaf (confirmed via gh auth; public repo)
- Web viewer: YES, minimal static viewer, timeboxed (Usability is scored)
- Agent session: Nova/Strands tool-trail (primary) + official Claude Code session over the
  same Context MCP (supplementary; claude is installed and DEV-supported)

## Still needed from user
- Org-level API token with Context Viewer permission (for the KB / Context MCP endpoint)
