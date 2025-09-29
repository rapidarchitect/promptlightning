class DakoraError(Exception): pass
class TemplateNotFound(DakoraError): pass
class ValidationError(DakoraError): pass
class RenderError(DakoraError): pass