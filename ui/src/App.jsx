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
  Zap,
  Edit2,
  Check as CheckIcon,
  X as XIcon
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

const Sidebar = ({ history, activeId, onNew, onSelect, onClear, onDelete, onRename, isSidebarOpen }) => {
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState("");

  const handleEditStart = (e, chat) => {
    e.stopPropagation();
    setEditingId(chat.id);
    setEditTitle(chat.title);
  };

  const handleEditSave = (e, id) => {
    e.stopPropagation();
    if (editTitle.trim()) {
      onRename(id, editTitle.trim());
    }
    setEditingId(null);
  };

  const handleEditCancel = (e) => {
    e.stopPropagation();
    setEditingId(null);
  };

  return (
    <aside className={cn(
      "dark:bg-brand-sidebar bg-[#f8fafc] border-r dark:border-white/5 border-gray-200 flex flex-col overflow-hidden transition-all duration-300 shrink-0",
      isSidebarOpen ? "w-[280px]" : "w-0 opacity-0"
    )}>
      <div className="p-4 flex flex-col h-full min-w-[280px]">
        <button 
          onClick={onNew}
          className="flex items-center gap-3 px-4 py-3 dark:bg-white/5 bg-white border dark:border-white/10 border-gray-200 rounded-xl hover:bg-brand-accent/5 transition-all mb-6 dark:text-white text-[#1e293b] font-semibold group active:scale-95 shadow-sm"
        >
          <Plus className="w-5 h-5 group-hover:rotate-90 transition-transform duration-300 text-brand-accent" />
          New Chat
        </button>

        <div className="flex-1 overflow-y-auto custom-scrollbar space-y-1 mb-4 pr-1">
          <label className="text-[10px] font-black dark:text-gray-500 text-gray-500 uppercase tracking-[0.2em] px-3 mb-3 block">Conversations</label>
          {history.map((chat) => (
            <div
              key={chat.id}
              onClick={() => onSelect(chat.id)}
              className={cn(
                "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group relative break-all text-left cursor-pointer",
                activeId === chat.id 
                  ? "bg-brand-accent/10 dark:text-white text-brand-accent ring-1 ring-brand-accent/20" 
                  : "dark:text-gray-500 text-gray-600 hover:bg-gray-200 dark:hover:bg-white/5 hover:text-black"
              )}
            >
              <MessageSquare className="w-4 h-4 flex-shrink-0" />
              
              {editingId === chat.id ? (
                <div className="flex-1 flex items-center gap-2">
                  <input
                    autoFocus
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleEditSave(e, chat.id);
                      if (e.key === 'Escape') handleEditCancel(e);
                    }}
                    onClick={(e) => e.stopPropagation()}
                    className="flex-1 bg-white dark:bg-gray-800 border dark:border-white/10 border-gray-300 rounded px-2 py-0.5 text-sm focus:outline-none focus:ring-1 focus:ring-brand-accent"
                  />
                  <div className="flex gap-1">
                     <button onClick={(e) => handleEditSave(e, chat.id)} className="p-1 hover:text-green-500 transition-colors">
                        <CheckIcon className="w-3.5 h-3.5" />
                     </button>
                     <button onClick={handleEditCancel} className="p-1 hover:text-red-500 transition-colors">
                        <XIcon className="w-3.5 h-3.5" />
                     </button>
                  </div>
                </div>
              ) : (
                <>
                  <span className="truncate flex-1 text-sm font-medium">{chat.title}</span>
                  <div className="flex gap-1 opacity-50 group-hover:opacity-100 transition-opacity">
                    <button 
                      onClick={(e) => handleEditStart(e, chat)}
                      className="p-1.5 hover:bg-brand-accent/10 rounded-lg dark:text-gray-400 text-gray-700 hover:text-brand-accent transition-all"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                    <button 
                      onClick={(e) => { e.stopPropagation(); onDelete(chat.id); }}
                      className="p-1.5 hover:bg-red-500/10 rounded-lg dark:text-gray-400 text-gray-700 hover:text-red-500 transition-all"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </>
              )}
            </div>
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
};

// ── MESSAGE COMPONENT ──────────────────────────────────────────────

const MessageBubble = ({ role, content, model, language }) => {
  const { settings } = useApp();
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
             <div className="flex items-center gap-2 px-1 text-[10px] font-bold uppercase tracking-widest dark:text-gray-500 text-gray-500">
               <span className={cn("font-black", settings.theme === 'dark' ? "text-white" : "text-black")}>
                  {model?.split(' ')[0] || 'Intelligence Engine'}
               </span>
               <span>•</span>
               <span className="opacity-60">{language || 'English'}</span>
             </div>
          )}
          
          <div className={cn(
            "p-4 px-5 rounded-2xl relative shadow-sm transition-all",
            isUser 
              ? "bg-brand-user text-white rounded-tr-none shadow-brand-accent/20" 
              : "bg-brand-bot dark:bg-brand-bot bg-[#ffffff] dark:text-gray-200 text-black border border-gray-200 dark:border-white/5 rounded-tl-none shadow-sm hover:shadow-md"
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
  const [activeChatId, setActiveChatId] = useState(() => {
    const saved = localStorage.getItem('kl_active_chat');
    return saved ? saved : null;
  });
  const [isSynced, setIsSynced] = useState(true); // Default to true to hide by default

  const scrollRef = useRef(null);
  const textareaRef = useRef(null);
  const { isListening, transcript, startListening, stopListening, setTranscript } = useSpeechToText();

  useEffect(() => {
    // Check sync status on load
    const checkSync = async () => {
      try {
        const res = await fetch('/sync/status');
        const data = await res.json();
        setIsSynced(data.synced);
      } catch (e) {
        console.error("Failed to check sync status:", e);
      }
    };
    checkSync();
  }, []);

  useEffect(() => {
    localStorage.setItem('kl_history', JSON.stringify(history));
  }, [history]);

  useEffect(() => {
    if (activeChatId) {
      localStorage.setItem('kl_active_chat', activeChatId);
    } else {
      localStorage.removeItem('kl_active_chat');
    }
  }, [activeChatId]);

  useEffect(() => {
    if (transcript) {
      setInput(prev => prev + ' ' + transcript);
      setTranscript('');
    }
  }, [transcript, setTranscript]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  useEffect(() => {
    // Sync dark class with settings
    if (settings.theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [settings.theme]);

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

  useEffect(() => {
    if (activeChatId && messages.length === 0) {
      const chat = history.find(c => String(c.id) === String(activeChatId));
      if (chat) setMessages(chat.messages);
    }
  }, [activeChatId, history]);

  const onDeleteChat = (id) => {
    if (confirm("Delete this conversation?")) {
      setHistory(prev => prev.filter(c => c.id !== id));
      if (activeChatId === id) onNew();
    }
  };

  const onRenameChat = (id, newTitle) => {
    setHistory(prev => prev.map(c => c.id === id ? { ...c, title: newTitle } : c));
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
              let errorMsg = data.error;
              if (errorMsg.includes('429') || errorMsg.includes('rate_limit')) {
                errorMsg = "🕒 The AI engine is currently busy (Rate Limit). Please try again in 18 minutes or use a different model.";
              }
              streamContent = `⚠️ **Assistant Note:** ${errorMsg}`;
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
              const chunk = data.delta;
              
              // ABSOLUTE SAFEGUARD: If raw error strings leak into the delta stream
              const lowerChunk = chunk.toLowerCase();
              if (lowerChunk.includes('error code: 429') || 
                  lowerChunk.includes('rate_limit_exceeded') || 
                  lowerChunk.includes('quota exceeded') ||
                  lowerChunk.includes('rate limit reached')) {
                
                streamContent = "🕒 **Assistant Note:** The AI engine is currently busy due to high traffic (Rate Limit reached). Please try again in a few minutes or switch to another model in Settings.";
                setMessages(prev => {
                  const updated = [...prev];
                  updated[updated.length - 1].content = streamContent;
                  return updated;
                });
                break; // Stop processing this chunk
              }

              if (streamContent === '') {
                streamContent = chunk;
              } else {
                streamContent += chunk;
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
        isSynced={isSynced}
        setIsSynced={setIsSynced}
      />

      <Sidebar 
        history={history} 
        activeId={activeChatId}
        onNew={onNew}
        onSelect={onSelect}
        onClear={onClear}
        onDelete={onDeleteChat}
        onRename={onRenameChat}
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
              <MenuIcon className="w-5 h-5 dark:text-gray-500 text-gray-600 hover:text-black transition-colors" />
            </button>
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-brand-accent animate-pulse" />
              <h1 className={cn("font-black text-sm tracking-tight", settings.theme === 'dark' ? "text-white" : "text-black")}>Kadel Labs Assistant</h1>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
             <ModelSelector 
               selected={settings.model} 
               onChange={(m) => setSettings(p => ({ ...p, model: m }))} 
               theme={settings.theme}
             />
             <ThemeToggle 
               theme={settings.theme} 
               setTheme={(t) => setSettings(p => ({ ...p, theme: t }))} 
             />
             <button 
              onClick={() => setIsSettingsOpen(true)}
              className="p-2.5 hover:bg-gray-200 dark:hover:bg-white/5 rounded-xl text-gray-500 hover:text-brand-accent transition-all active:scale-90"
             >
               <Settings className="w-5 h-5 dark:text-gray-500 text-gray-600 hover:text-brand-accent" />
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
                  <h2 className="text-3xl font-black mb-4 dark:text-white text-black">Ready to Help</h2>
                  <p className="dark:text-gray-400 text-slate-600 max-w-sm mx-auto mb-10 font-medium">
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
              className="bg-white dark:bg-[#1a2333] border border-gray-200 dark:border-white/10 rounded-3xl shadow-xl flex items-end gap-2 p-1.5 focus-within:ring-4 focus-within:ring-brand-accent/10 transition-all"
            >
              <textarea 
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit();
                  }
                }}
                rows={1}
                style={{ resize: 'none' }}
                placeholder={`Ask ${settings.model.split(' ')[0]} in ${settings.language}...`}
                className="flex-1 bg-transparent border-none dark:text-white text-slate-900 dark:placeholder-gray-500 placeholder-gray-500 focus:ring-0 p-4 max-h-[220px] transition-all overflow-y-auto"
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
