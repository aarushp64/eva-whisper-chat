import { useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Settings, Zap, Lock, Globe } from 'lucide-react';

// ─── Provider & model definitions ───────────────────────────────────

interface ProviderOption {
  id: string;
  name: string;
  icon: React.ReactNode;
  badge: string;
  badgeVariant: 'default' | 'secondary' | 'outline';
  models: { id: string; name: string }[];
  requiresKey: boolean;
}

const PROVIDERS: ProviderOption[] = [
  {
    id: 'groq',
    name: 'Groq',
    icon: <Zap className="w-4 h-4" />,
    badge: 'Cloud — Fast',
    badgeVariant: 'default',
    models: [
      { id: 'qwen/qwen3-32b', name: 'Qwen 3 32B' },
    ],
    requiresKey: true,
  },
  {
    id: 'ollama',
    name: 'Ollama',
    icon: <Lock className="w-4 h-4" />,
    badge: 'Local — Private',
    badgeVariant: 'secondary',
    models: [
      { id: 'mistral:7b', name: 'Mistral 7B' },
      { id: 'qwen3:8b', name: 'Qwen 3 8B' },
      { id: 'llama3.2', name: 'Llama 3.2' },
    ],
    requiresKey: false,
  },
];

// ─── Runtime config shape ───────────────────────────────────────────

export interface LLMConfig {
  provider: string;
  model: string;
  apiKey?: string; // passed per-request only, never persisted
}

// ─── Hook for consuming LLM config from sessionStorage ──────────────

const LLM_CONFIG_KEY = 'eva_llm_config';

/**
 * Read the current LLM config from sessionStorage.
 * Returns the parsed object or null if not set.
 */
export function getLLMConfig(): LLMConfig | null {
  try {
    const raw = sessionStorage.getItem(LLM_CONFIG_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as LLMConfig;
  } catch {
    return null;
  }
}

/**
 * Save LLM config to sessionStorage.
 * NOTE: API keys are intentionally NOT stored here.
 * They are kept in React state and passed per-request.
 */
export function setLLMConfig(config: LLMConfig): void {
  sessionStorage.setItem(
    LLM_CONFIG_KEY,
    JSON.stringify({ provider: config.provider, model: config.model })
  );
}

/** Clear the persisted provider/model selection */
export function clearLLMConfig(): void {
  sessionStorage.removeItem(LLM_CONFIG_KEY);
}

// ─── Component ──────────────────────────────────────────────────────

interface LLMSettingsModalProps {
  /** Called when config changes. Receives the full config including apiKey. */
  onConfigChange: (config: LLMConfig | null) => void;
}

export function LLMSettingsModal({ onConfigChange }: LLMSettingsModalProps) {
  const [open, setOpen] = useState(false);

  // Read persisted selection (provider + model only, no API key)
  const persisted = getLLMConfig();

  const [provider, setProvider] = useState(
    persisted?.provider || 'groq'
  );
  const [model, setModel] = useState(
    persisted?.model || PROVIDERS[0].models[0].id
  );
  // API key is NEVER persisted — only held in component state
  const [apiKey, setApiKey] = useState('');
  const [keyVisible, setKeyVisible] = useState(false);

  const selectedProvider = PROVIDERS.find((p) => p.id === provider)!;

  // If the selected model isn't available for this provider, reset to the first
  const availableModels = selectedProvider.models;
  const currentModel = availableModels.some((m) => m.id === model)
    ? model
    : availableModels[0].id;

  const handleSave = useCallback(() => {
    const config: LLMConfig = {
      provider,
      model: currentModel,
    };

    // Only include apiKey if the provider requires one AND the user entered a value
    if (selectedProvider.requiresKey && apiKey.trim()) {
      config.apiKey = apiKey.trim();
    }

    // Persist provider + model only (no key)
    setLLMConfig(config);

    // Pass the full config (with key) to the parent
    onConfigChange(config);
    setOpen(false);
  }, [provider, currentModel, apiKey, selectedProvider.requiresKey, onConfigChange]);

  const handleProviderChange = (newProvider: string) => {
    setProvider(newProvider);
    const prov = PROVIDERS.find((p) => p.id === newProvider)!;
    setModel(prov.models[0].id);
    setApiKey(''); // clear key when switching providers
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="flex items-center gap-2 text-sm hover:bg-eva-primary/20"
          title="LLM / API Settings"
        >
          <Settings className="w-4 h-4" />
          <span className="hidden sm:inline">⚙️ LLM / API</span>
        </Button>
      </DialogTrigger>

      <DialogContent className="sm:max-w-md bg-eva-bg-secondary border-eva-border text-eva-text-primary">
        <DialogHeader>
          <DialogTitle className="text-lg">LLM / API Settings</DialogTitle>
          <DialogDescription className="text-sm text-eva-text-secondary">
            Choose your AI provider and model. API keys are sent per-request only and never stored.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-5 py-2">
          {/* ── Provider Selection ── */}
          <div className="space-y-2">
            <Label>Provider</Label>
            <Select value={provider} onValueChange={handleProviderChange}>
              <SelectTrigger className="bg-black/40 border-eva-border text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-eva-bg-secondary border-eva-border">
                {PROVIDERS.map((p) => (
                  <SelectItem key={p.id} value={p.id} className="flex items-center gap-2">
                    <span className="flex items-center gap-2">
                      {p.icon}
                      {p.name}
                      <Badge variant={p.badgeVariant} className="text-xs">
                        {p.badge}
                      </Badge>
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* ── Model Selection ── */}
          <div className="space-y-2">
            <Label>Model</Label>
            <Select value={currentModel} onValueChange={setModel}>
              <SelectTrigger className="bg-black/40 border-eva-border text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-eva-bg-secondary border-eva-border">
                {availableModels.map((m) => (
                  <SelectItem key={m.id} value={m.id}>
                    {m.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* ── API Key (conditional) ── */}
          {selectedProvider.requiresKey && (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Label>API Key</Label>
                <Globe className="w-3 h-3 text-eva-text-secondary" />
              </div>
              <div className="relative">
                <Input
                  type={keyVisible ? 'text' : 'password'}
                  placeholder={`Enter your ${selectedProvider.name} API key`}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="bg-black/40 border-eva-border text-white pr-20"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  className="absolute right-1 top-1/2 -translate-y-1/2 h-7 px-2 text-xs text-eva-text-secondary hover:text-white"
                  onClick={() => setKeyVisible((v) => !v)}
                >
                  {keyVisible ? 'Hide' : 'Show'}
                </Button>
              </div>
              <p className="text-xs text-eva-text-secondary">
                🔒 Key is sent per-request and never stored on disk or in localStorage.
              </p>
            </div>
          )}

          {!selectedProvider.requiresKey && (
            <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20">
              <p className="text-xs text-green-400">
                ✅ No API key needed — this provider runs locally on your machine.
              </p>
            </div>
          )}
        </div>

        {/* ── Actions ── */}
        <div className="flex justify-end gap-2 pt-2">
          <Button
            variant="outline"
            onClick={() => setOpen(false)}
            className="text-sm"
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            className="bg-eva-primary hover:bg-eva-primary-dark text-white text-sm"
          >
            Save & Apply
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
