export type Role = 'user' | 'assistant';

export interface Message {
  id: string;
  role: Role;
  text: string;
  /** True while the assistant is still streaming this message. */
  streaming?: boolean;
}
