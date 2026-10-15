"""One place that decides which model backs the app: Azure AI Foundry deployment or local Ollama."""
from . import config as c


def _azure_token_provider():
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    return get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")


def chat_model(temperature: float = 0.0):
    if c.PROVIDER == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=c.OLLAMA_CHAT, base_url=c.OLLAMA_URL, temperature=temperature)
    from langchain_openai import AzureChatOpenAI
    kwargs = dict(azure_endpoint=c.AZURE_ENDPOINT, azure_deployment=c.CHAT_DEPLOYMENT,
                  api_version=c.AZURE_API_VERSION, temperature=temperature)
    if c.AZURE_API_KEY:
        kwargs["api_key"] = c.AZURE_API_KEY
    else:
        kwargs["azure_ad_token_provider"] = _azure_token_provider()
    return AzureChatOpenAI(**kwargs)


def embeddings():
    if c.PROVIDER == "ollama":
        from langchain_ollama import OllamaEmbeddings
        return OllamaEmbeddings(model=c.OLLAMA_EMBED, base_url=c.OLLAMA_URL)
    from langchain_openai import AzureOpenAIEmbeddings
    kwargs = dict(azure_endpoint=c.AZURE_ENDPOINT, azure_deployment=c.EMBED_DEPLOYMENT,
                  api_version=c.AZURE_API_VERSION)
    if c.AZURE_API_KEY:
        kwargs["api_key"] = c.AZURE_API_KEY
    else:
        kwargs["azure_ad_token_provider"] = _azure_token_provider()
    return AzureOpenAIEmbeddings(**kwargs)
