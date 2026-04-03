import json
import os
from typing import Any
from uuid import UUID

from langchain_core.language_models.chat_models import BaseChatModel
from sqlalchemy import select

from openclerk.db import get_async_session
from openclerk.db.config import get_config
from openclerk.db.models import LlmProviderConfig

# Default models per provider
DEFAULT_MODELS = {
    "openai": "gpt-5-mini",
    "anthropic": "claude-3-5-sonnet-latest",
    "mistral": "mistral-large-latest",
    "gemini": "gemini-1.5-pro",
    "vertex": "gemini-1.5-pro",
    "openrouter": "openai/gpt-5-mini",
}


async def get_active_provider_config(user_id: UUID | None) -> dict[str, Any] | None:
    """Get the active LLM provider configuration for a user."""
    if not user_id:
        return None

    config = get_config()
    if not config.is_database_configured:
        return None

    try:
        async with get_async_session() as session:
            stmt = select(LlmProviderConfig).where(
                LlmProviderConfig.user_id == user_id,
                LlmProviderConfig.is_active,
            )
            result = await session.execute(stmt)
            provider_config = result.scalar_one_or_none()

            if provider_config:
                return {
                    "provider": provider_config.provider_name,
                    "env_vars": provider_config.env_vars,
                    "model": provider_config.selected_model
                    or DEFAULT_MODELS.get(provider_config.provider_name, "gpt-4o-mini"),
                }
    except Exception as e:
        print(f"Error fetching active provider config: {e}")
        pass

    return None


async def get_llm(
    user_id: str | None = None, model: str | None = None, temperature: float = 0.0
) -> BaseChatModel:
    """
    Factory function to get a configured LLM instance.

    Order of precedence:
    1. Active provider config from DB for the user.
    2. Global environment variables (e.g., OPENAI_API_KEY).
    """
    # Check DB for user override
    active_config = None
    if user_id:
        try:
            active_config = await get_active_provider_config(UUID(user_id))
        except ValueError:
            pass

    if active_config:
        provider = active_config["provider"]
        env_vars = active_config["env_vars"]
        # Use provided model parameter if it exists (e.g., evaluation model overrides),
        # otherwise use the user's selected model from DB
        target_model = model or active_config["model"]

        if provider == "openai":
            from langchain_openai import ChatOpenAI

            api_key = env_vars.get("OPENAI_API_KEY")
            return ChatOpenAI(
                model=target_model, temperature=temperature, api_key=api_key
            )

        elif provider == "anthropic":
            from langchain_anthropic import ChatAnthropic

            api_key = env_vars.get("ANTHROPIC_API_KEY")
            return ChatAnthropic(  # type: ignore[call-arg]
                model=target_model, temperature=temperature, api_key=api_key
            )

        elif provider == "mistral":
            from langchain_mistralai import ChatMistralAI

            api_key = env_vars.get("MISTRAL_API_KEY")
            return ChatMistralAI(  # type: ignore[call-arg]
                model=target_model, temperature=temperature, api_key=api_key
            )

        elif provider == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI

            api_key = env_vars.get("GOOGLE_API_KEY")
            return ChatGoogleGenerativeAI(
                model=target_model, temperature=temperature, google_api_key=api_key
            )

        elif provider == "openrouter":
            from langchain_openai import ChatOpenAI

            api_key = env_vars.get("OPENROUTER_API_KEY")
            return ChatOpenAI(
                model=target_model,
                temperature=temperature,
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
            )

        elif provider == "vertex":
            from langchain_google_vertexai import ChatVertexAI

            # Vertex supports both JSON credentials string or default gcloud auth
            # The UI should allow pasting the JSON credentials into a specific env var
            credentials_json = env_vars.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
            if credentials_json:
                from google.oauth2 import service_account

                try:
                    cred_dict = json.loads(credentials_json)
                    credentials = service_account.Credentials.from_service_account_info(
                        cred_dict
                    )
                    # We might need project from JSON too
                    project = cred_dict.get("project_id")
                    return ChatVertexAI(
                        model=target_model,
                        temperature=temperature,
                        credentials=credentials,
                        project=project,
                    )
                except Exception as e:
                    print(f"Error parsing Vertex AI credentials: {e}")

            # Fallback to default auth if no json or error
            project = env_vars.get("GOOGLE_CLOUD_PROJECT")
            return ChatVertexAI(
                model=target_model, temperature=temperature, project=project
            )

    # Global Fallbacks (using OS env vars)
    target_model = model or DEFAULT_MODELS["openai"]

    # Infer provider from model name
    inferred_provider = "openai"
    if target_model.startswith("claude-"):
        inferred_provider = "anthropic"
    elif (
        target_model.startswith("mistral-")
        or target_model.startswith("pixtral-")
        or target_model.startswith("open-mistral")
    ):
        inferred_provider = "mistral"
    elif target_model.startswith("gemini-"):
        inferred_provider = "gemini"
    elif "/" in target_model:
        inferred_provider = "openrouter"

    if inferred_provider == "openai" and os.environ.get("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=target_model, temperature=temperature)

    elif inferred_provider == "anthropic" and os.environ.get("ANTHROPIC_API_KEY"):
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=target_model, temperature=temperature)  # type: ignore[call-arg]

    elif inferred_provider == "mistral" and os.environ.get("MISTRAL_API_KEY"):
        from langchain_mistralai import ChatMistralAI

        return ChatMistralAI(model=target_model, temperature=temperature)  # type: ignore[call-arg]

    elif inferred_provider == "gemini":
        if os.environ.get("GOOGLE_API_KEY"):
            from langchain_google_genai import ChatGoogleGenerativeAI

            return ChatGoogleGenerativeAI(model=target_model, temperature=temperature)
        elif os.environ.get("GOOGLE_CLOUD_PROJECT"):
            from langchain_google_vertexai import ChatVertexAI

            project = os.environ.get("GOOGLE_CLOUD_PROJECT")
            return ChatVertexAI(
                model=target_model, temperature=temperature, project=project
            )

    elif inferred_provider == "openrouter" and os.environ.get("OPENROUTER_API_KEY"):
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=target_model,
            temperature=temperature,
            base_url="https://openrouter.ai/api/v1",
        )

    # Fallback if the inferred provider key is missing but another is present
    if os.environ.get("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=target_model, temperature=temperature)

    # Absolute default
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=target_model, temperature=temperature)
