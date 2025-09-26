import { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import { Play, AlertCircle, CheckCircle, FileText, Loader2, Info, Code2 } from 'lucide-react';
import { useTemplate, useRender } from '../hooks/useApi';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';

interface TemplateEditorProps {
  templateId: string | null;
}

export function TemplateEditor({ templateId }: TemplateEditorProps) {
  const { template, loading, error } = useTemplate(templateId);
  const { render, loading: renderLoading, error: renderError, clearError } = useRender();

  const [templateContent, setTemplateContent] = useState('');
  const [inputs, setInputs] = useState<Record<string, unknown>>({});
  const [renderResult, setRenderResult] = useState<string>('');
  const [showPreview, setShowPreview] = useState(false);

  useEffect(() => {
    if (template) {
      setTemplateContent(template.template);
      // Initialize inputs with defaults
      const defaultInputs: Record<string, unknown> = {};
      Object.entries(template.inputs).forEach(([key, spec]) => {
        if (spec.default !== undefined) {
          defaultInputs[key] = spec.default;
        } else if (spec.required) {
          // Set empty values for required inputs
          switch (spec.type) {
            case 'string':
              defaultInputs[key] = '';
              break;
            case 'number':
              defaultInputs[key] = 0;
              break;
            case 'boolean':
              defaultInputs[key] = false;
              break;
            case 'array<string>':
              defaultInputs[key] = [];
              break;
            case 'object':
              defaultInputs[key] = {};
              break;
          }
        }
      });
      setInputs(defaultInputs);
      setRenderResult('');
      setShowPreview(false);
    }
  }, [template]);

  useEffect(() => {
    clearError();
  }, [templateContent, inputs, clearError]);

  const handleRender = async () => {
    if (!template) return;

    try {
      const response = await render(template.id, inputs);
      setRenderResult(response.rendered);
      setShowPreview(true);
    } catch (error) {
      console.error('Render error:', error);
    }
  };

  const handleInputChange = (key: string, value: unknown) => {
    setInputs(prev => ({ ...prev, [key]: value }));
  };

  const renderInputField = (key: string, spec: any) => {
    const value = inputs[key];

    switch (spec.type) {
      case 'string':
        return (
          <Textarea
            value={(value as string) || ''}
            onChange={(e) => handleInputChange(key, e.target.value)}
            placeholder={`Enter ${key}...`}
            rows={3}
          />
        );

      case 'number':
        return (
          <Input
            type="number"
            value={(value as number) || ''}
            onChange={(e) => handleInputChange(key, parseFloat(e.target.value) || 0)}
            placeholder={`Enter ${key}...`}
          />
        );

      case 'boolean':
        return (
          <div className="flex items-center space-x-4">
            <label className="flex items-center space-x-2">
              <input
                type="radio"
                name={`${key}-bool`}
                checked={(value as boolean) === true}
                onChange={() => handleInputChange(key, true)}
                className="text-primary"
              />
              <span className="text-sm">True</span>
            </label>
            <label className="flex items-center space-x-2">
              <input
                type="radio"
                name={`${key}-bool`}
                checked={(value as boolean) === false}
                onChange={() => handleInputChange(key, false)}
                className="text-primary"
              />
              <span className="text-sm">False</span>
            </label>
          </div>
        );

      case 'array<string>':
        return (
          <Textarea
            value={Array.isArray(value) ? (value as string[]).join('\n') : ''}
            onChange={(e) => handleInputChange(key, e.target.value.split('\n').filter(Boolean))}
            placeholder={`Enter ${key} (one per line)...`}
            rows={3}
          />
        );

      case 'object':
        return (
          <Textarea
            value={typeof value === 'object' ? JSON.stringify(value, null, 2) : ''}
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value);
                handleInputChange(key, parsed);
              } catch {
                // Invalid JSON, ignore
              }
            }}
            className="font-mono"
            placeholder={`Enter ${key} as JSON...`}
            rows={4}
          />
        );

      default:
        return null;
    }
  };

  if (!templateId) {
    return (
      <div className="flex-1 flex items-center justify-center bg-muted/10">
        <Card className="w-96 text-center">
          <CardContent className="pt-6">
            <FileText className="w-16 h-16 text-muted-foreground/50 mx-auto mb-4" />
            <CardTitle className="mb-2">No Template Selected</CardTitle>
            <CardDescription>
              Select a template from the sidebar to start editing and testing
            </CardDescription>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-muted/10">
        <Card className="w-96 text-center">
          <CardContent className="pt-6">
            <Loader2 className="w-12 h-12 text-primary mx-auto mb-4 animate-spin" />
            <CardTitle className="mb-2">Loading Template</CardTitle>
            <CardDescription>Please wait while we load the template...</CardDescription>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center bg-muted/10">
        <Card className="w-96 text-center">
          <CardContent className="pt-6">
            <AlertCircle className="w-16 h-16 text-destructive mx-auto mb-4" />
            <CardTitle className="mb-2">Error Loading Template</CardTitle>
            <CardDescription className="text-destructive">{error}</CardDescription>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!template) return null;

  return (
    <div className="flex-1 flex flex-col h-full bg-background">
      {/* Header */}
      <div className="border-b border-border px-6 py-4 bg-card">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h1 className="text-xl font-semibold truncate">{template.id}</h1>
              <Badge variant="secondary">{template.version}</Badge>
            </div>
            {template.description && (
              <p className="text-sm text-muted-foreground">{template.description}</p>
            )}
          </div>
          <Button
            onClick={handleRender}
            disabled={renderLoading}
            className="shrink-0"
          >
            {renderLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Rendering...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Render
              </>
            )}
          </Button>
        </div>
      </div>

      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        {/* Left Panel - Template & Inputs */}
        <div className="flex-1 flex flex-col border-b lg:border-r lg:border-b-0 border-border">
          {/* Template Editor */}
          <div className="flex-1 bg-card">
            <div className="px-4 py-3 border-b border-border bg-muted/30">
              <div className="flex items-center gap-2">
                <Code2 className="w-4 h-4" />
                <h3 className="text-sm font-medium">Template</h3>
                <Badge variant="outline" className="text-xs">Read-only</Badge>
              </div>
            </div>
            <div className="h-64 lg:h-80">
              <Editor
                height="100%"
                language="handlebars"
                value={templateContent}
                onChange={(value) => setTemplateContent(value || '')}
                options={{
                  minimap: { enabled: false },
                  scrollBeyondLastLine: false,
                  wordWrap: 'on',
                  lineNumbers: 'on',
                  fontSize: 14,
                  readOnly: true,
                  theme: 'vs',
                }}
              />
            </div>
          </div>

          {/* Inputs Panel */}
          <div className="flex-1 min-h-0 border-t border-border bg-muted/30 flex flex-col">
            <div className="px-4 py-3 border-b border-border bg-muted/30 flex-shrink-0">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium">Template Inputs</h3>
                {Object.keys(template.inputs).length > 0 && (
                  <Badge variant="secondary" className="text-xs">
                    {Object.keys(template.inputs).length} input{Object.keys(template.inputs).length !== 1 ? 's' : ''}
                  </Badge>
                )}
              </div>
            </div>
            <ScrollArea className="flex-1 min-h-0">
              <div className="p-4">
                {Object.keys(template.inputs).length === 0 ? (
                  <div className="text-center py-8">
                    <Info className="w-8 h-8 mx-auto mb-3 text-muted-foreground/50" />
                    <p className="text-sm text-muted-foreground">No inputs defined for this template</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {Object.entries(template.inputs).map(([key, spec]) => (
                      <div key={key} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <label className="text-sm font-medium">
                            {key}
                            {spec.required && <span className="text-destructive ml-1">*</span>}
                          </label>
                          <div className="flex items-center gap-1">
                            <Badge variant="outline" className="text-xs">
                              {spec.type}
                            </Badge>
                            {!spec.required && (
                              <Badge variant="secondary" className="text-xs">
                                optional
                              </Badge>
                            )}
                          </div>
                        </div>
                        {renderInputField(key, spec)}
                        {spec.default !== undefined && (
                          <p className="text-xs text-muted-foreground">
                            Default: {String(spec.default)}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </ScrollArea>
          </div>
        </div>

        {/* Right Panel - Preview */}
        <div className="flex-1 bg-card flex flex-col">
          <div className="px-4 py-3 border-b border-border bg-muted/30">
            <h3 className="text-sm font-medium">Preview</h3>
          </div>

          <ScrollArea className="flex-1">
            <div className="p-4">
              {renderError && (
                <Card className="mb-4 bg-destructive/10 border-destructive/20">
                  <CardContent className="pt-4">
                    <div className="flex items-start gap-2">
                      <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
                      <div>
                        <h4 className="text-sm font-medium text-destructive mb-1">Render Error</h4>
                        <p className="text-sm text-destructive/80">{renderError}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {!showPreview && !renderError && (
                <div className="text-center py-12">
                  <Play className="w-16 h-16 mx-auto mb-4 text-muted-foreground/30" />
                  <h3 className="text-lg font-medium mb-2">Ready to Render</h3>
                  <p className="text-sm text-muted-foreground">
                    Fill in the template inputs and click "Render" to preview the output
                  </p>
                </div>
              )}

              {showPreview && renderResult && (
                <Card>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-5 h-5 text-green-500" />
                      <CardTitle className="text-green-700">Rendered Successfully</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="bg-muted rounded-md p-4 border">
                      <pre className="text-sm whitespace-pre-wrap font-mono text-foreground leading-relaxed">
                        {renderResult}
                      </pre>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </ScrollArea>
        </div>
      </div>
    </div>
  );
}