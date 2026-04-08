import { useState, useRef, useEffect, useCallback } from 'react';
import { ChatMessage } from './components/ChatMessage';
import { ChatInput } from './components/ChatInput';
import { streamChat } from './api';
import type { Message } from './types';

function generateId() {
  return Math.random().toString(36).slice(2);
}

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = useCallback(async (text: string) => {
    setError(null);

    const userMessage: Message = { id: generateId(), role: 'user', text };
    const assistantId = generateId();
    const assistantMessage: Message = {
      id: assistantId,
      role: 'assistant',
      text: '',
      streaming: true,
    };

    setMessages(prev => [...prev, userMessage, assistantMessage]);
    setIsStreaming(true);

    abortRef.current = new AbortController();

    try {
      await streamChat(
        text,
        (chunk) => {
          setMessages(prev =>
            prev.map(m =>
              m.id === assistantId ? { ...m, text: m.text + chunk } : m
            )
          );
        },
        abortRef.current.signal,
      );
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        setError('Something went wrong. Please try again.');
        setMessages(prev => prev.filter(m => m.id !== assistantId));
      }
    } finally {
      setMessages(prev =>
        prev.map(m =>
          m.id === assistantId ? { ...m, streaming: false } : m
        )
      );
      setIsStreaming(false);
      abortRef.current = null;
    }
  }, []);

  return (
    <div className="flex flex-col h-screen bg-white dark:bg-gray-900">
      {/* Header */}
      <header className="flex-shrink-0 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="max-w-3xl mx-auto flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center">
            <span className="text-white text-sm font-bold">L</span>
          </div>
          <div>
            <h1 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              Lorcana Assistant
            </h1>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Ask about rules, cards, and gameplay
            </p>
          </div>
        </div>
      </header>

      {/* Messages */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-4 py-6 flex flex-col gap-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center min-h-[40vh] text-center gap-3">
              <div className="w-14 h-14 rounded-2xl bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center">
                <span className="text-indigo-600 dark:text-indigo-400 text-2xl font-bold">L</span>
              </div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Lorcana Assistant
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400 max-w-sm">
                Ask me anything about Disney Lorcana — card abilities, game rules, interactions, and more.
              </p>
            </div>
          )}

          {messages.map(message => (
            <ChatMessage key={message.id} message={message} />
          ))}

          {error && (
            <p className="text-center text-sm text-red-500 dark:text-red-400">{error}</p>
          )}

          <div ref={bottomRef} />
        </div>
      </main>

      {/* Input */}
      <footer className="flex-shrink-0 border-t border-gray-200 dark:border-gray-700 px-4 py-4">
        <div className="max-w-3xl mx-auto">
          <p className="text-center text-xs text-amber-500/60 dark:text-amber-400/50 font-bold mb-2">
            AI responses may include mistakes. Always verify rules with the official Disney Lorcana comprehensive rules.
          </p>
          <ChatInput onSend={handleSend} disabled={isStreaming} />
          <p className="text-center text-xs text-gray-400 dark:text-gray-500 mt-2">
            Shift+Enter for a new line · Enter to send
          </p>
        </div>
      </footer>
    </div>
  );
}
