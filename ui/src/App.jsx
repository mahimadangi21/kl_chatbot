import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Toaster } from 'react-hot-toast';
import { 
  Plus, 
  MessageSquare, 
  Trash2, 
  Settings, 
  User, 
  Bot, 
  Send, 
  Mic, 
  MicOff, 
  Copy, 
  Check, 
  Sparkles,
  Menu as MenuIcon,
  X,
  Brain,
  Zap
} from 'lucide-react';
import { useSpeechToText } from './hooks/useSpeechToText';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { useApp } from './context/AppContext';

// Imported functional components
import SettingsDrawer from './components/SettingsDrawer';
import ModelSelector from './components/ModelSelector';
import ThemeToggle from './components/ThemeToggle';

function cn(...inputs) {
  return twMerge(clsx(inputs));
}

// ── SIDEBAR COMPONENT ──────────────────────────────────────────────

const Sidebar = ({ history, activeId, onNew, onSelect, onClear, isSidebarOpen }) => (
  <aside className={cn(
    "bg-brand-sidebar dark:bg-brand-sidebar bg-light-sidebar border-r border-white/5 dark:border-white/5 border-gray-200 flex flex-col overflow-hidden transition-all duration-300 shrink-0",
    isSidebarOpen ? "w-[280px]" : "w-0 opacity-0"
  )}>
    <div className="p-4 flex flex-col h-full min-w-[280px]">
      <button 
        onClick={onNew}
        className="flex items-center gap-3 px-4 py-3 bg-white/5 dark:bg-white/5 bg-gray-100 border border-white/10 dark:border-white/10 border-gray-300 rounded-xl hover:bg-brand-accent/5 transition-all mb-6 dark:text-white text-brand-bg font-medium group active:scale-95 shadow-sm"
      >
        <Plus className="w-5 h-5 group-hover:rotate-90 transition-transform duration-300 text-brand-accent" />
        New Chat
      </button>

      <div className="flex-1 overflow-y-auto custom-scrollbar space-y-1 mb-4 pr-1">
        <label className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] px-3 mb-3 block">Conversations</label>
        {history.map((chat) => (
          <button
            key={chat.id}
            onClick={() => onSelect(chat.id)}
            className={cn(
              "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group relative break-all text-left",
              activeId === chat.id 
                ? "bg-brand-accent/10 dark:text-white text-brand-accent ring-1 ring-brand-accent/20" 
                : "text-gray-500 hover:bg-gray-200 dark:hover:bg-white/5"
            )}
          >
            <MessageSquare className="w-4 h-4 flex-shrink-0" />
            <span className="truncate flex-1 text-sm font-medium">{chat.title}</span>
          </button>
        ))}
      </div>

      <div className="pt-4 border-t border-gray-200 dark:border-white/10">
        <button 
          onClick={onClear}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-gray-400 hover:text-red-500 transition-all text-sm group"
        >
          <Trash2 className="w-4 h-4" />
          Clear All History
        </button>
      </div>
    </div>
  </aside>
);

// ── MESSAGE COMPONENT ──────────────────────────────────────────────

const MessageBubble = ({ role, content, model, language }) => {
  const isUser = role === 'user';
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "group flex w-full flex-col mb-10",
        isUser ? "items-end" : "items-start"
      )}
    >
      <div className={cn(
        "flex max-w-[90%] md:max-w-[80%] gap-4",
        isUser ? "flex-row-reverse" : "flex-row"
      )}>
        <div className={cn(
          "w-9 h-9 rounded-xl flex-shrink-0 flex items-center justify-center mt-1.5 shadow-lg",
          isUser 
            ? "bg-brand-user text-white" 
            : "bg-brand-bot dark:bg-brand-bot bg-light-bot border border-gray-200 dark:border-white/10 text-brand-accent shadow-black/10"
        )}>
          {isUser ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
        </div>
        
        <div className="flex flex-col gap-2 flex-1">
          {!isUser && (
             <div className="flex items-center gap-2 px-1 text-[10px] font-bold uppercase tracking-widest text-gray-500">
               <span className="text-brand-accent">{model?.split(' ')[0] || 'Ollama'}</span>
               <span>•</span>
               <span className="opacity-60">{language || 'English'}</span>
             </div>
          )}
          
          <div className={cn(
            "p-4 px-5 rounded-2xl relative shadow-sm transition-all",
            isUser 
              ? "bg-brand-user text-white rounded-tr-none shadow-brand-accent/20" 
              : "bg-brand-bot dark:bg-brand-bot bg-light-chat dark:text-gray-200 text-brand-bg border border-gray-100 dark:border-white/5 rounded-tl-none shadow-xl"
          )}>
            <div className="markdown-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {content}
              </ReactMarkdown>
            </div>
          </div>
          
          <div className={cn(
            "flex items-center gap-4 opacity-0 group-hover:opacity-100 transition-all",
            isUser ? "justify-end" : "justify-start"
          )}>
            <button 
              onClick={handleCopy}
              className="text-gray-400 hover:text-brand-accent transition-colors p-1"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

// ── MAIN APP ───────────────────────────────────────────────────────

function App() {
  const { settings, setSettings } = useApp();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  
  const [history, setHistory] = useState(() => JSON.parse(localStorage.getItem('kl_history') || '[]'));
  const [activeChatId, setActiveChatId] = useState(null);

  const scrollRef = useRef(null);
  const { isListening, transcript, startListening, stopListening, setTranscript } = useSpeechToText();

  useEffect(() => {
    localStorage.setItem('kl_history', JSON.stringify(history));
  }, [history]);

  useEffect(() => {
    if (transcript) {
      setInput(prev => prev + ' ' + transcript);
      setTranscript('');
    }
  }, [transcript, setTranscript]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  const onNew = () => {
    setMessages([]);
    setActiveChatId(null);
  };

  const onSelect = (id) => {
    const chat = history.find(c => c.id === id);
    if (chat) {
      setMessages(chat.messages);
      setActiveChatId(id);
    }
  };

  const onClear = () => {
    if (confirm("Clear all?")) {
      setHistory([]);
      onNew();
    }
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userQuery = input.trim();
    const currentModel = settings.model;
    const currentLang = settings.language;
    
    // Optimistic User Message
    const updatedMessages = [...messages, { 
      role: 'user', 
      content: userQuery 
    }];
    
    setInput('');
    setMessages([...updatedMessages, { 
      role: 'assistant', 
      content: '', 
      model: currentModel, 
      language: currentLang 
    }]);
    setIsLoading(true);

    try {
      const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: userQuery, 
          history: messages,
          manual_lang: currentLang,
          model: currentModel
        })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let streamContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const data = JSON.parse(line);
            
            if (data.error) {
              streamContent = `⚠️ **Error:** ${data.error}`;
              setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1].content = streamContent;
                return updated;
              });
              break;
            }

            if (data.status) {
              setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1].content = `*${data.status}*`;
                return updated;
              });
              continue;
            }

            if (data.delta) {
              // If we were showing a status, clear it for the first real chunk
              if (streamContent === '') {
                streamContent = data.delta;
              } else {
                streamContent += data.delta;
              }
              
              setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1].content = streamContent;
                return updated;
              });
            }
          } catch (e) { 
            console.error("Error parsing stream line:", e, line);
          }
        }
      }

      // Save History
      const finalMsg = { role: 'assistant', content: streamContent, model: currentModel, language: currentLang };
      const finalSet = [...updatedMessages, finalMsg];
      if (activeChatId) {
        setHistory(p => p.map(c => c.id === activeChatId ? { ...c, messages: finalSet } : c));
      } else {
        const newChat = { id: Date.now(), title: userQuery.slice(0, 30), messages: finalSet };
        setHistory(p => [newChat, ...p]);
        setActiveChatId(newChat.id);
      }
    } catch (err) {
      setMessages(prev => {
        const up = [...prev];
        up[up.length - 1].content = "⚠️ Error connecting to server.";
        return up;
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={cn(
      "flex h-screen w-full transition-colors duration-300 font-sans overflow-hidden",
      settings.theme === 'dark' ? "bg-brand-bg text-brand-text" : "bg-light-bg text-brand-bg"
    )}>
      <Toaster position="top-right" />
      
      <SettingsDrawer 
        isOpen={isSettingsOpen} 
        onClose={() => setIsSettingsOpen(false)} 
        settings={settings}
        setSettings={setSettings}
      />

      <Sidebar 
        history={history} 
        activeId={activeChatId}
        onNew={onNew}
        onSelect={onSelect}
        onClear={onClear}
        isSidebarOpen={isSidebarOpen}
      />

      <main className="flex-1 flex flex-col relative h-full overflow-hidden">
        {/* Modern Header */}
        <header className="h-14 border-b border-gray-200 dark:border-white/10 flex items-center justify-between px-6 bg-transparent backdrop-blur-md z-50">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="p-2 hover:bg-gray-200 dark:hover:bg-white/5 rounded-lg transition-all"
            >
              <MenuIcon className="w-5 h-5 text-gray-500" />
            </button>
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-brand-accent animate-pulse" />
              <h1 className="font-bold text-sm tracking-tight dark:text-white text-brand-bg">Kadel Lab Assistant</h1>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
             <ModelSelector 
               selected={settings.model} 
               onChange={(m) => setSettings(p => ({ ...p, model: m }))} 
             />
             <ThemeToggle 
               theme={settings.theme} 
               setTheme={(t) => setSettings(p => ({ ...p, theme: t }))} 
             />
             <button 
              onClick={() => setIsSettingsOpen(true)}
              className="p-2.5 hover:bg-gray-200 dark:hover:bg-white/5 rounded-xl text-gray-500 hover:text-brand-accent transition-all active:scale-90"
             >
               <Settings className="w-5 h-5" />
             </button>
          </div>
        </header>

        {/* Chat Canvas */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto custom-scrollbar pt-12 pb-44 px-4 overflow-x-hidden">
          <div className="max-w-[760px] mx-auto w-full">
            <AnimatePresence initial={false}>
              {messages.length === 0 ? (
                <motion.div 
                  initial={{ opacity: 0, scale: 0.98 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="flex flex-col items-center justify-center min-h-[60vh] text-center"
                >
                  <div className="w-20 h-20 bg-brand-accent/10 rounded-3xl flex items-center justify-center mb-8 border border-brand-accent/20 animate-float shadow-2xl">
                    <Brain className="w-10 h-10 text-brand-accent" />
                  </div>
                  <h2 className="text-3xl font-black mb-4 dark:text-white text-brand-bg">Ready to Help</h2>
                  <p className="text-gray-500 max-w-sm mx-auto mb-10 font-medium">
                    Select a model above and start exploring your training materials in multiple languages.
                  </p>
                </motion.div>
              ) : (
                messages.map((m, i) => <MessageBubble key={i} {...m} />)
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Input Bar */}
        <div className="absolute bottom-0 left-0 w-full p-6 bg-gradient-to-t from-transparent via-transparent to-transparent">
          <div className="max-w-[780px] mx-auto">
            <form 
              onSubmit={handleSubmit}
              className="bg-light-chat dark:bg-[#1a2333] border border-gray-200 dark:border-white/10 rounded-3xl shadow-2xl flex items-end gap-2 p-1.5 focus-within:ring-4 focus-within:ring-brand-accent/10 transition-all"
            >
              <textarea 
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit();
                  }
                }}
                rows={1}
                placeholder={`Ask ${settings.model.split(' ')[0]} in ${settings.language}...`}
                className="flex-1 bg-transparent border-none dark:text-white text-brand-bg focus:ring-0 p-4 max-h-[220px] transition-all"
              />
              <div className="flex items-center gap-2 pr-2 pb-2">
                <button 
                  type="button"
                  onClick={isListening ? stopListening : startListening}
                  className={cn(
                    "p-3 rounded-full",
                    isListening ? "bg-red-500 text-white animate-pulse" : "text-gray-500 hover:text-brand-accent hover:bg-white/5"
                  )}
                >
                  {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                </button>
                <button 
                  type="submit"
                  disabled={!input.trim() || isLoading}
                  className="p-3 bg-brand-accent text-white rounded-2xl shadow-xl hover:scale-105 active:scale-95 disabled:opacity-20 transition-all"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
