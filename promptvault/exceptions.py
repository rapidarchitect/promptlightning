class PromptVaultError(Exception): pass
class TemplateNotFound(PromptVaultError): pass
class ValidationError(PromptVaultError): pass
class RenderError(PromptVaultError): pass