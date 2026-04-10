import React from 'react';
import { Listbox, Transition } from '@headlessui/react';
import { Check, ChevronDown, Globe } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) {
  return twMerge(clsx(inputs));
}

const languages = [
  { id: 'en', name: 'English' },
  { id: 'hi', name: 'Hindi' },
  { id: 'hn', name: 'Hinglish' },
];

const LanguageSelector = ({ selected, onChange, isDark = true }) => {
  const currentLang = languages.find(l => l.name === selected) || languages[0];

  return (
    <div className="w-full">
      <Listbox value={currentLang} onChange={(val) => onChange(val.name)}>
        <div className="relative mt-1">
          <Listbox.Button className={cn(
             "relative w-full cursor-pointer rounded-xl border py-3 pl-10 pr-10 text-left focus:outline-none transition-all",
             isDark 
              ? "bg-white/5 border-white/10 hover:bg-white/10 text-gray-200" 
              : "bg-gray-50 border-gray-200 hover:bg-gray-100 text-brand-bg shadow-sm"
          )}>
            <span className="absolute inset-y-0 left-0 flex items-center pl-3">
              <Globe className="h-4 w-4 text-gray-400" aria-hidden="true" />
            </span>
            <span className="block truncate text-sm">{currentLang.name}</span>
            <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
              <ChevronDown className="h-4 w-4 text-gray-400" aria-hidden="true" />
            </span>
          </Listbox.Button>
          <Transition
            as={React.Fragment}
            leave="transition ease-in duration-100"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <Listbox.Options className={cn(
               "absolute z-[120] mt-1 max-h-60 w-full overflow-auto rounded-xl border py-1 text-base shadow-2xl focus:outline-none sm:text-sm custom-scrollbar",
               isDark ? "bg-[#1a1f2e] border-white/10" : "bg-white border-gray-200"
            )}>
              {languages.map((lang) => (
                <Listbox.Option
                  key={lang.id}
                  className={({ active }) =>
                    cn(
                       "relative cursor-pointer select-none py-2.5 pl-10 pr-4 transition-colors",
                       active 
                        ? (isDark ? 'bg-brand-accent/20 text-white' : 'bg-brand-accent/10 text-brand-bg') 
                        : (isDark ? 'text-gray-300' : 'text-gray-600')
                    )
                  }
                  value={lang}
                >
                  {({ selected }) => (
                    <>
                      <span className={cn("block truncate", selected ? 'font-bold text-brand-accent' : 'font-normal')}>
                        {lang.name}
                      </span>
                      {selected ? (
                        <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-brand-accent">
                          <Check className="h-4 w-4" aria-hidden="true" />
                        </span>
                      ) : null}
                    </>
                  )}
                </Listbox.Option>
              ))}
            </Listbox.Options>
          </Transition>
        </div>
      </Listbox>
    </div>
  );
};

export default LanguageSelector;
