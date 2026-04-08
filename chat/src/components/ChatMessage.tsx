import ReactMarkdown from 'react-markdown';
import { useTypewriter } from '../hooks/useTypewriter';
import type { Message } from '../types';

interface Props {
  message: Message;
}

function ThinkingIndicator() {
  return (
    <div className="flex items-center gap-1 px-1 py-0.5">
      <span className="w-1.5 h-1.5 rounded-full bg-gray-400 dark:bg-gray-500 animate-bounce [animation-delay:-0.3s]" />
      <span className="w-1.5 h-1.5 rounded-full bg-gray-400 dark:bg-gray-500 animate-bounce [animation-delay:-0.15s]" />
      <span className="w-1.5 h-1.5 rounded-full bg-gray-400 dark:bg-gray-500 animate-bounce" />
    </div>
  );
}

export function ChatMessage({ message }: Props) {
  const isUser = message.role === 'user';

  const displayed = useTypewriter(message.text, message.streaming ?? false);
  const text = isUser ? message.text : displayed;

  const isWaiting = !isUser && message.streaming && message.text.length === 0;

  return (
    <div className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? 'bg-indigo-600 text-white rounded-br-sm'
            : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-bl-sm'
        }`}
      >
        {isWaiting ? (
          <ThinkingIndicator />
        ) : isUser ? (
          <p className="whitespace-pre-wrap">
            {text}
          </p>
        ) : (
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown>{text}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
