export interface SearchResult {
  command_id: string;
  command: string;
  name: string;
  description: string;
  technology: string;
  category: string;
  intent: string;
  confidence: number;
  risk: 'safe' | 'warning' | 'dangerous';
  tags: string[];
  documentation_url: string;
  related_commands: string[];
  explanation: {
    technology_detected: string;
    intent_detected: string;
    matched_tags: string[];
    semantic_score: number;
    keyword_score: number;
  };
}

export interface AskResponse {
  query: string;
  results: SearchResult[];
  clarification?: {
    message: string;
    options: string[];
  };
}

export interface CommandDetail {
  command_id: string;
  command: string;
  name: string;
  description: string;
  technology: string;
  category: string;
  intent: string;
  risk: 'safe' | 'warning' | 'dangerous';
  tags: string[];
  documentation_url: string;
  related_commands: string[];
  examples: string[];
}

export interface Category {
  name: string;
  technology: string;
  count: number;
  description: string;
}

export interface HealthResponse {
  status: string;
  version: string;
}

export type RiskLevel = 'safe' | 'warning' | 'dangerous';
