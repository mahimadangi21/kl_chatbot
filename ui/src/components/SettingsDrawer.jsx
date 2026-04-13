import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Moon, Sun, Cpu, Languages, RefreshCw, Smartphone } from 'lucide-react';
import LanguageSelector from './LanguageSelector';
import SyncButton from './SyncButton';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) {
  return twMerge(clsx(inputs));
}

const SettingsDrawer = ({ isOpen, onClose, settings, setSettings, isSynced, setIsSynced }) => {
  const isDark = settings.theme === 'dark';

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100]"
          />

          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className={cn(
               "fixed right-0 top-0 h-full w-full max-w-[400px] border-l z-[110] shadow-2xl flex flex-col transition-colors duration-300",
               isDark ? "bg-brand-sidebar border-white/10" : "bg-white border-gray-200"
            )}
          >
            {/* Header */}
            <div className={cn(
               "p-6 border-b flex items-center justify-between backdrop-blur-md",
               isDark ? "border-white/5 bg-brand-bg/50" : "border-gray-100 bg-gray-50/50"
            )}>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-brand-accent/10 flex items-center justify-center border border-brand-accent/20">
                  <Cpu className="w-5 h-5 text-brand-accent" />
                </div>
                <div>
                  <h2 className={cn("text-lg font-bold", isDark ? "text-white" : "text-slate-900")}>Settings</h2>
                  <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">Configuration Panel</p>
                </div>
              </div>
              <button 
                onClick={onClose}
                className="p-2 hover:bg-gray-200 dark:hover:bg-white/5 rounded-full text-gray-400 transition-all"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-8 custom-scrollbar">
              
              <section className="space-y-4">
                <label className="text-[11px] font-black text-gray-500 uppercase tracking-[0.2em] px-1">Appearance</label>
                <div className="grid grid-cols-2 gap-3">
                  <button 
                    onClick={() => setSettings(prev => ({ ...prev, theme: 'dark' }))}
                    className={cn(
                       "flex items-center justify-center gap-3 p-4 rounded-2xl border transition-all",
                       settings.theme === 'dark' 
                        ? 'bg-brand-accent/10 border-brand-accent text-white' 
                        : 'bg-gray-50 dark:bg-white/5 border-transparent text-gray-400'
                    )}
                  >
                    <Moon className="w-4 h-4" />
                    <span className="text-sm font-medium">Dark</span>
                  </button>
                  <button 
                    onClick={() => setSettings(prev => ({ ...prev, theme: 'light' }))}
                    className={cn(
                       "flex items-center justify-center gap-3 p-4 rounded-2xl border transition-all",
                       settings.theme === 'light' 
                        ? 'bg-brand-accent/10 border-brand-accent text-brand-bg' 
                        : 'bg-gray-50 dark:bg-white/5 border-transparent text-gray-400'
                    )}
                  >
                    <Sun className="w-4 h-4" />
                    <span className="text-sm font-medium">Light</span>
                  </button>
                </div>
              </section>

              <section className="space-y-4">
                <div className="flex items-center justify-between px-1">
                  <label className="text-[11px] font-black text-gray-500 uppercase tracking-[0.2em]">Language</label>
                  <Languages className="w-3.5 h-3.5 text-brand-accent" />
                </div>
                <LanguageSelector 
                  selected={settings.language} 
                  onChange={(val) => setSettings(prev => ({ ...prev, language: val }))} 
                  isDark={isDark}
                />
              </section>

              <section className="space-y-4">
                <div className="flex items-center justify-between px-1">
                  <label className="text-[11px] font-black text-gray-500 uppercase tracking-[0.2em]">Knowledge Base</label>
                  <RefreshCw className={cn("w-3.5 h-3.5 text-brand-accent", !isSynced && "animate-spin")} />
                </div>
                <div className={cn(
                  "p-4 rounded-2xl border flex items-center justify-between transition-all",
                  isDark ? "bg-white/5 border-white/10" : "bg-gray-50 border-gray-100"
                )}>
                  <div className="flex items-center gap-3">
                    <div className={cn("w-2 h-2 rounded-full", isSynced ? "bg-green-500" : "bg-brand-accent animate-pulse")} />
                    <span className={cn("text-sm font-medium", isDark ? "text-gray-300" : "text-brand-bg")}>
                      {isSynced ? "Engine Ready" : "Sync Required"}
                    </span>
                  </div>
                  <SyncButton 
                    onComplete={() => setIsSynced(true)} 
                    variant={isSynced ? "minimal" : "full"}
                    isDark={isDark}
                  />
                </div>
              </section>

              <section className="space-y-4">
                <label className="text-[11px] font-black text-gray-500 uppercase tracking-[0.2em] px-1">Active Model</label>
                <div className="space-y-2">
                  {['Gemini (Google)', 'Grok (xAI)'].map((model) => (
                    <button
                      key={model}
                      onClick={() => setSettings(prev => ({ ...prev, model }))}
                      className={cn(
                         "w-full flex items-center justify-between p-4 rounded-2xl border transition-all",
                         settings.model === model 
                          ? 'bg-brand-accent/10 border-brand-accent dark:text-white text-brand-bg shadow-sm' 
                          : 'bg-gray-50 dark:bg-white/5 border-transparent text-gray-400 hover:bg-gray-100 dark:hover:bg-white/10'
                      )}
                    >
                      <span className="text-sm font-medium">{model}</span>
                      {settings.model === model && <div className="w-2 h-2 rounded-full bg-brand-accent shadow-[0_0_8px_#3b82f6]" />}
                    </button>
                  ))}
                </div>
              </section>
            </div>

            <div className={cn(
               "p-6 border-t",
               isDark ? "border-white/5 bg-brand-bg/30" : "border-gray-100 bg-gray-50"
            )}>
              <div className="flex items-center gap-3 text-gray-500 mb-4">
                <Smartphone className="w-4 h-4" />
                <span className="text-[10px] uppercase font-black tracking-widest">v3.2.1 Stable</span>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default SettingsDrawer;
