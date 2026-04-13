import React, { useState } from 'react';
import { RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';

const SyncButton = ({ onComplete, variant = "full", isDark = true }) => {
  const [isSyncing, setIsSyncing] = useState(false);

  const handleSync = async () => {
    setIsSyncing(true);
    const toastId = toast.loading('Synchronizing Knowledge Base...');
    
    try {
      const response = await fetch('/sync', { method: 'POST' });
      const data = await response.json();
      
      if (response.ok) {
        toast.success(data.message || 'Sync Complete!', { id: toastId });
      } else {
        throw new Error(data.detail || 'Sync failed');
      }
    } catch (error) {
      toast.error(error.message || 'Connection error', { id: toastId });
    } finally {
      setIsSyncing(false);
      if (onComplete) onComplete();
    }
  };

  if (variant === "minimal") {
    return (
      <button
        onClick={handleSync}
        disabled={isSyncing}
        className="p-2 hover:bg-brand-accent/10 rounded-lg group transition-all"
        title="Force Refresh Data"
      >
        <RefreshCw className={`w-4 h-4 text-brand-accent ${isSyncing ? 'animate-spin' : 'group-hover:rotate-180 transition-transform duration-500'}`} />
      </button>
    );
  }

  return (
    <button
      onClick={handleSync}
      disabled={isSyncing}
      className={`w-full flex items-center justify-center gap-3 px-4 py-3 rounded-xl border transition-all ${
        isSyncing 
          ? 'bg-brand-accent/5 border-brand-accent/20 cursor-not-allowed opacity-50' 
          : 'bg-brand-accent/5 border-brand-accent/20 hover:bg-brand-accent/10 hover:border-brand-accent active:scale-95 shadow-sm'
      }`}
    >
      <RefreshCw className={`w-4 h-4 ${isSyncing ? 'animate-spin text-brand-accent' : 'text-brand-accent'}`} />
      <span className="text-sm font-semibold dark:text-gray-200 text-brand-bg">Force Refresh Knowledge</span>
    </button>
  );
};

export default SyncButton;
