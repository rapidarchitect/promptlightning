import { useState } from 'react';
import { FileText, Search, Sparkles, Loader2 } from 'lucide-react';
import { useTemplates, useExamples } from '../hooks/useApi';
import { NewTemplateDialog } from './NewTemplateDialog';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface TemplateListProps {
  selectedTemplate: string | null;
  onSelectTemplate: (templateId: string | null) => void;
}

export function TemplateList({ selectedTemplate, onSelectTemplate }: TemplateListProps) {
  const { templates, loading: templatesLoading, error: templatesError, refetch } = useTemplates();
  const { examples, loading: examplesLoading, error: examplesError } = useExamples();
  const [searchTerm, setSearchTerm] = useState('');

  const handleTemplateCreated = (templateId: string) => {
    refetch();
    onSelectTemplate(templateId);
  };

  const filteredTemplates = templates.filter(template =>
    template.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredExamples = examples.filter(example =>
    example.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    example.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="w-full md:w-80 bg-card border-r border-border flex flex-col h-full">
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Templates</h2>
        </div>

        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
          <Input
            type="text"
            placeholder="Search templates..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>

        <Tabs defaultValue="templates" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="templates" className="flex items-center gap-2">
              <FileText className="w-4 h-4" />
              <span className="hidden sm:inline">Project</span>
            </TabsTrigger>
            <TabsTrigger value="examples" className="flex items-center gap-2">
              <Sparkles className="w-4 h-4" />
              <span className="hidden sm:inline">Examples</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="templates" className="mt-4">
            <ScrollArea className="h-[calc(100vh-280px)]">
              <div className="space-y-2">
                {templatesLoading && (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
                  </div>
                )}

                {templatesError && (
                  <Card className="p-3 bg-destructive/10 border-destructive/20">
                    <p className="text-sm text-destructive">{templatesError}</p>
                  </Card>
                )}

                {!templatesLoading && !templatesError && filteredTemplates.length === 0 && (
                  <div className="text-center py-8">
                    <FileText className="w-12 h-12 mx-auto mb-3 text-muted-foreground/50" />
                    <p className="text-sm text-muted-foreground">No templates found</p>
                    {searchTerm && (
                      <p className="text-xs text-muted-foreground mt-1">Try adjusting your search</p>
                    )}
                  </div>
                )}

                {filteredTemplates.map((templateId) => (
                  <Button
                    key={templateId}
                    onClick={() => onSelectTemplate(templateId)}
                    variant={selectedTemplate === templateId ? "secondary" : "ghost"}
                    className={cn(
                      "w-full justify-start h-auto p-3 font-normal",
                      selectedTemplate === templateId && "ring-2 ring-primary/20"
                    )}
                  >
                    <div className="flex items-center w-full">
                      <FileText className="w-4 h-4 mr-3 flex-shrink-0" />
                      <span className="text-sm truncate">{templateId}</span>
                    </div>
                  </Button>
                ))}
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="examples" className="mt-4">
            <ScrollArea className="h-[calc(100vh-280px)]">
              <div className="space-y-2">
                {examplesLoading && (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
                  </div>
                )}

                {examplesError && (
                  <Card className="p-3 bg-destructive/10 border-destructive/20">
                    <p className="text-sm text-destructive">{examplesError}</p>
                  </Card>
                )}

                {!examplesLoading && !examplesError && filteredExamples.length === 0 && (
                  <div className="text-center py-8">
                    <Sparkles className="w-12 h-12 mx-auto mb-3 text-muted-foreground/50" />
                    <p className="text-sm text-muted-foreground">No examples found</p>
                  </div>
                )}

                {filteredExamples.map((example) => (
                  <Button
                    key={example.id}
                    onClick={() => onSelectTemplate(example.id)}
                    variant={selectedTemplate === example.id ? "secondary" : "ghost"}
                    className={cn(
                      "w-full justify-start h-auto p-3 font-normal",
                      selectedTemplate === example.id && "ring-2 ring-primary/20"
                    )}
                  >
                    <div className="flex flex-col items-start w-full">
                      <div className="flex items-center w-full mb-1">
                        <Sparkles className="w-4 h-4 mr-3 flex-shrink-0 text-amber-500" />
                        <span className="text-sm font-medium truncate">{example.id}</span>
                      </div>
                      {example.description && (
                        <p className="text-xs text-muted-foreground ml-7 text-left truncate w-full">
                          {example.description}
                        </p>
                      )}
                      {example.metadata?.tags && Array.isArray(example.metadata.tags) ? (
                        <div className="flex flex-wrap gap-1 ml-7 mt-1">
                          {(example.metadata.tags as string[]).slice(0, 2).map((tag: string) => (
                            <Badge key={`${example.id}-${tag}`} variant="secondary" className="text-xs px-1.5 py-0.5">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  </Button>
                ))}
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </div>

      <div className="p-4 border-t border-border">
        <NewTemplateDialog onTemplateCreated={handleTemplateCreated} />
      </div>
    </div>
  );
}