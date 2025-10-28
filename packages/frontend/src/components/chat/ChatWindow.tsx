import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { AudioRecorder } from './AudioRecorder';
import io, { Socket } from 'socket.io-client';
import TypingIndicator from '../ui/TypingIndicator';

const socket: Socket = io(import.meta.env.VITE_NODE_API_URL || 'http://localhost:8081', {});

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'eva';
  timestamp: string;
}

export const ChatWindow = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: "Hi, I'm EVA! How can I assist you today?",
      sender: 'eva',
      timestamp: new Date().toLocaleTimeString(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [typingUsers, setTypingUsers] = useState<string[]>([]);

  const messageEndRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const scrollToBottom = () => {
    messageEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    socket.on('connect', () => {
      console.log('Connected to WebSocket server');
      socket.emit('join_room', { room: 'general', user: 'user' });
    });

    socket.on('disconnect', () => {
      console.log('Disconnected from WebSocket server');
    });

    socket.on('chat_message', (data: { message: string; user: string }) => {
      const newMessage: Message = {
        id: String(Date.now()),
        text: data.message,
        sender: 'eva',
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prevMessages) => [...prevMessages, newMessage]);
    });

    socket.on('user_typing', (data: { user: string }) => {
      setTypingUsers((prev) => (prev.includes(data.user) ? prev : [...prev, data.user]));
    });

    socket.on('user_stopped_typing', (data: { user: string }) => {
      setTypingUsers((prev) => prev.filter((u) => u !== data.user));
    });

    return () => {
      socket.off('connect');
      socket.off('disconnect');
      socket.off('chat_message');
      socket.off('user_typing');
      socket.off('user_stopped_typing');
    };
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
    socket.emit('typing', { room: 'general', user: 'user' });
    typingTimeoutRef.current = setTimeout(() => {
      socket.emit('stop_typing', { room: 'general', user: 'user' });
    }, 2000);
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !isProcessing) {
      const newMessage: Message = {
        id: String(Date.now()),
        text: inputValue,
        sender: 'user',
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prevMessages) => [...prevMessages, newMessage]);
      socket.emit('chat_message', { room: 'general', message: inputValue, user: 'user' });
      setInputValue('');
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
      socket.emit('stop_typing', { room: 'general', user: 'user' });
    }
  };

  const handleSendAudioMessage = (audioData: string, format: string) => {
    console.log(`Sending audio message of format ${format}`);
    // Placeholder for sending audio to backend
    const newMessage: Message = {
      id: String(Date.now()),
      text: 'Audio message sent.',
      sender: 'user',
      timestamp: new Date().toLocaleTimeString(),
    };
    setMessages((prevMessages) => [...prevMessages, newMessage]);
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-eva-bg-secondary">
      <header className="flex items-center justify-between p-4 border-b border-eva-border">
        <h2 className="text-xl font-bold">EVA Assistant</h2>
        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 bg-green-500 rounded-full"></span>
          <span>Online</span>
        </div>
      </header>
      <div className="flex-1 p-6 overflow-y-auto space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex items-start max-w-[80%] ${message.sender === 'user' ? 'self-end flex-row-reverse' : 'self-start'}`}>
            <Avatar className="w-8 h-8">
              <AvatarImage src={message.sender === 'eva' ? '/eva-avatar.png' : '/user-avatar.png'} />
              <AvatarFallback>{message.sender === 'eva' ? 'E' : 'U'}</AvatarFallback>
            </Avatar>
            <div className={`rounded-2xl p-4 mx-3 ${message.sender === 'user' ? 'bg-eva-primary text-white rounded-br-none' : 'bg-eva-message-bubble text-eva-text-primary rounded-bl-none'}`}>
              <p>{message.text}</p>
              <span className="text-xs opacity-60 mt-1 block text-right">{message.timestamp}</span>
            </div>
          </div>
        ))}
        <div ref={messageEndRef} />
      </div>
      <div className="p-4 border-t border-eva-border">
        <TypingIndicator typingUsers={typingUsers} />
        <form onSubmit={handleSendMessage} className="flex items-center space-x-4">
          <Input
            type="text"
            placeholder="Type your message..."
            value={inputValue}
            onChange={handleInputChange}
            className="flex-1 bg-black text-white border-gray-600 rounded-lg focus:ring-eva-primary placeholder:text-gray-400"
            disabled={isProcessing}
          />
          <Button
            type="submit"
            className="bg-eva-primary hover:bg-eva-primary-dark text-white font-bold py-2 px-4 rounded-lg"
            disabled={isProcessing || !inputValue.trim()}>
            Send
          </Button>
          <AudioRecorder onAudioMessage={handleSendAudioMessage} isProcessing={isProcessing} />
        </form>
      </div>
      <audio ref={audioRef} className="hidden" />
    </div>
  );
};
