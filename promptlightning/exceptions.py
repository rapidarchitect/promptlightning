class PromptLightningError(Exception): pass
class TemplateNotFound(PromptLightningError): pass
class ValidationError(PromptLightningError): pass
class RenderError(PromptLightningError): pass
class RegistryError(PromptLightningError): pass

class LLMError(PromptLightningError): pass
class APIKeyError(LLMError): pass
class RateLimitError(LLMError): pass
class ModelNotFoundError(LLMError): pass