export type Role = 'user' | 'assistant';

export interface Citation {
  number: number;
  rule_id: string;
  rule_text: string;
}

export interface Message {
  id: string;
  role: Role;
  text: string;
  citations: Citation[];
  /** True while the assistant is still streaming this message. */
  streaming?: boolean;
}
