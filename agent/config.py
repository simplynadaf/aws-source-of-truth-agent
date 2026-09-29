"""
Central configuration + friendly env loading.

Every entrypoint imports `config` so a missing value fails the same clear way
instead of throwing a raw KeyError deep in the SDK. Values come from .env
(python-dotenv) or the real environment.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # dotenv is optional at runtime
    pass


class ConfigError(RuntimeError):
    """Raised when a required environment value is missing."""


def _required(name: str) -> str:
    v = os.environ.get(name, "").strip()
    if not v:
        raise ConfigError(
            f"Missing {name}. Copy .env.example to .env and fill it in. "
            f"See README.md ('Configure') for where each value comes from."
        )
    return v


def _optional(name: str, fallback: str) -> str:
    v = os.environ.get(name, "").strip()
    return v if v else fallback


@dataclass(frozen=True)
class Config:
    @property
    def mcp_url(self) -> str:
        return _required("SANITY_CONTEXT_MCP_URL")

    @property
    def sanity_token(self) -> str:
        return _required("SANITY_ORGANIZATION_TOKEN")

    @property
    def project_id(self) -> str:
        return _optional("SANITY_PROJECT_ID", "(not set)")

    @property
    def org_id(self) -> str:
        return _optional("SANITY_ORGANIZATION_ID", "(not set)")

    @property
    def dataset(self) -> str:
        return _optional("SANITY_DATASET", "production")

    @property
    def model_id(self) -> str:
        return _optional("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")

    @property
    def region(self) -> str:
        return _optional("AWS_REGION", "us-east-1")

    def retrieval_mode(self) -> str:
        url = os.environ.get("SANITY_CONTEXT_MCP_URL", "")
        if "mode=knowledge_base" in url:
            return "knowledge_base (forced via URL)"
        if "mode=groq" in url:
            return "groq (forced via URL)"
        return "auto (decided by the MCP sources)"


config = Config()
