export type Role = 'user' | 'assistant';

export interface Citation {
  number: number;
  rule_id: string;
  rule_text: string;
}

export interface CardReference {
  card_id: number;
  full_name: string;
  image_url: string;
}

export interface Message {
  id: string;
  role: Role;
  text: string;
  citations: Citation[];
  cards: Record<number, CardReference>;
  /** True while the assistant is still streaming this message. */
  streaming?: boolean;
}
