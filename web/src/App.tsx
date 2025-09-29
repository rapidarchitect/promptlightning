import { useState } from 'react';
import { Menu, X } from 'lucide-react';
import { TemplateList } from './components/TemplateList';
import { TemplateEditor } from './components/TemplateEditor';
import { StatusBar } from './components/StatusBar';
import { Button } from '@/components/ui/button';

function App() {
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="h-screen bg-background flex flex-col">
      {/* Mobile Header */}
      <div className="md:hidden border-b border-border bg-card px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="md:hidden"
            >
              {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </Button>
            <h1 className="text-lg font-semibold">Dakora</h1>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Mobile Sidebar Overlay */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/50 z-40 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar */}
        <div
          className={`
            fixed md:relative inset-y-0 left-0 z-50 md:z-0
            transform ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
            md:translate-x-0 transition-transform duration-200 ease-in-out
          `}
        >
          <TemplateList
            selectedTemplate={selectedTemplate}
            onSelectTemplate={(template) => {
              setSelectedTemplate(template);
              setSidebarOpen(false); // Close sidebar on mobile after selection
            }}
          />
        </div>

        {/* Main Editor */}
        <div className="flex-1 md:flex">
          <TemplateEditor templateId={selectedTemplate} />
        </div>
      </div>

      {/* Status Bar */}
      <StatusBar />
    </div>
  );
}

export default App;