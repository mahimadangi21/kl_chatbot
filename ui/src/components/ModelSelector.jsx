import React from 'react';
import { Menu, Transition } from '@headlessui/react';
import { Cpu, ChevronDown, Check, Zap, Sparkles, Brain } from 'lucide-react';

const models = [
  { id: 'groq', name: 'Groq (Fast)', icon: Zap, color: 'text-yellow-500' },
  { id: 'gemini', name: 'Gemini (Accurate)', icon: Sparkles, color: 'text-purple-500' },
];

const ModelSelector = ({ selected, onChange }) => {
  const currentModel = models.find(m => m.name === selected) || models[0];

  return (
    <div className="relative">
      <Menu as="div" className="relative inline-block text-left">
        <Menu.Button className="flex items-center gap-2 px-3 py-1.5 bg-white/5 hover:bg-white/10 dark:hover:bg-white/5 rounded-full border border-white/5 text-[10px] text-gray-400 hover:text-white font-black tracking-widest uppercase transition-all shadow-inner active:scale-95">
          <currentModel.icon className={`w-3.5 h-3.5 ${currentModel.color}`} />
          <span>Model: {currentModel.name.split(' ')[0]}</span>
          <ChevronDown className="w-3 h-3 ml-1" />
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
          <Menu.Items className="absolute right-0 mt-2 w-56 origin-top-right rounded-2xl bg-[#1a2333] border border-white/10 shadow-2xl ring-1 ring-black/5 focus:outline-none overflow-hidden z-[110]">
            <div className="px-1 py-1">
              <div className="px-3 py-2 text-[10px] font-black text-gray-500 uppercase tracking-[0.2em]">Select Intelligence Engine</div>
              {models.map((model) => (
                <Menu.Item key={model.id}>
                  {({ active }) => (
                    <button
                      onClick={() => onChange(model.name)}
                      className={`${
                        active ? 'bg-white/5 text-white' : 'text-gray-400'
                      } group flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-xs transition-colors`}
                    >
                      <div className="flex items-center gap-3">
                        <model.icon className={`w-4 h-4 ${model.color}`} />
                        <span className={selected === model.name ? 'font-bold text-white' : ''}>{model.name}</span>
                      </div>
                      {selected === model.name && <Check className="w-4 h-4 text-brand-accent" />}
                    </button>
                  )}
                </Menu.Item>
              ))}
            </div>
            <div className="bg-black/20 p-3 flex items-center gap-2">
               <div className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-[0_0_8px_#22c55e]" />
               <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">Enterprise Ready</span>
            </div>
          </Menu.Items>
        </Transition>
      </Menu>
    </div>
  );
};

export default ModelSelector;
