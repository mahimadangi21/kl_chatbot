import React from 'react';
import { Menu, Transition } from '@headlessui/react';
import { Cpu, ChevronDown, Check, Zap, Sparkles, Brain } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) {
  return twMerge(clsx(inputs));
}

const models = [
  { id: 'groq', name: 'Groq (Fast)', icon: Zap, color: 'text-yellow-500' },
  { id: 'gemini', name: 'Gemini (Accurate)', icon: Sparkles, color: 'text-purple-500' },
];

const ModelSelector = ({ selected, onChange, theme }) => {
  const currentModel = models.find(m => m.name === selected) || models[0];
  const isDark = theme === 'dark';

  return (
    <div className="relative">
      <Menu as="div" className="relative inline-block text-left">
        <Menu.Button className={cn(
          "flex items-center gap-2 px-4 py-2 rounded-full border transition-all shadow-sm active:scale-95",
          isDark 
            ? "bg-white/5 border-white/10 text-white hover:bg-white/10" 
            : "bg-slate-100 border-slate-300 text-black hover:bg-white"
        )}>
          <currentModel.icon className={`w-3.5 h-3.5 ${currentModel.color}`} />
          <span className="text-[10px] tracking-widest whitespace-nowrap font-black uppercase">
            Model: {currentModel.name.split(' ')[0]}
          </span>
          <ChevronDown className="w-3 h-3 ml-1 opacity-50" />
        </Menu.Button>

        <Transition
          as={React.Fragment}
          enter="transition ease-out duration-100"
          enterFrom="transform opacity-0 scale-95 -translate-y-2"
          enterTo="transform opacity-100 scale-100 translate-y-0"
          leave="transition ease-in duration-75"
          leaveFrom="transform opacity-100 scale-100 translate-y-0"
          leaveTo="transform opacity-0 scale-95 -translate-y-2"
        >
          <Menu.Items className="absolute right-0 mt-2 w-56 origin-top-right rounded-2xl dark:bg-[#1a2333] bg-white border dark:border-white/10 border-gray-200 shadow-2xl ring-1 ring-black/5 focus:outline-none overflow-hidden z-[110]">
            <div className="px-1 py-1">
              <div className="px-3 py-2 text-[10px] font-black dark:text-gray-400 text-gray-500 uppercase tracking-[0.2em]">Select Intelligence Engine</div>
               {models.map((model) => (
                <Menu.Item key={model.id}>
                  {({ active }) => (
                    <button
                      onClick={() => onChange(model.name)}
                      className={`${
                        active 
                          ? 'dark:bg-white/10 bg-gray-100' 
                          : ''
                      } group flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-xs transition-colors text-black dark:text-white`}
                    >
                      <div className="flex items-center gap-3">
                        <model.icon className={`w-4 h-4 ${model.color}`} />
                        <span className={selected === model.name ? 'font-bold' : ''}>{model.name}</span>
                      </div>
                      {selected === model.name && <Check className="w-4 h-4 text-brand-accent" />}
                    </button>
                  )}
                </Menu.Item>
              ))}
            </div>
            <div className="dark:bg-black/40 bg-gray-100 p-3 flex items-center gap-2">
               <div className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-[0_0_8px_#22c55e]" />
               <span className="text-[10px] dark:text-gray-400 text-gray-500 font-bold uppercase tracking-widest">Enterprise Ready</span>
            </div>
          </Menu.Items>
        </Transition>
      </Menu>
    </div>
  );
};

export default ModelSelector;
