import React, { useState } from 'react';
import { RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';

const SyncButton = () => {
  const [isSyncing, setIsSyncing] = useState(false);

  const handleSync = async () => {
    setIsSyncing(true);
    const toastId = toast.loading('Synchronizing Knowledge Base...');
    
    try {
      const response = await fetch('http://127.0.0.1:8000/sync', { method: 'POST' });
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
    }
  };

  return (
    <button
      onClick={handleSync}
      disabled={isSyncing}
      className={`w-full flex items-center justify-center gap-3 px-4 py-3 rounded-xl border border-white/10 transition-all ${
        isSyncing 
          ? 'bg-white/5 cursor-not-allowed opacity-50' 
          : 'bg-white/5 hover:bg-white/10 active:scale-95'
      }`}
    >
      <RefreshCw className={`w-4 h-4 ${isSyncing ? 'animate-spin text-brand-accent' : 'text-gray-400'}`} />
      <span className="text-sm font-medium">Sync Knowledge Base</span>
    </button>
  );
};

export default SyncButton;
