import React from 'react';
import { Menu, Transition } from '@headlessui/react';
import { User, LogOut, Settings, Languages, ChevronUp } from 'lucide-react';
import toast from 'react-hot-toast';

const ProfileDropdown = ({ onOpenSettings }) => {
  const handleLogout = () => {
    toast.success('Logged out successfully');
  };

  return (
    <div className="relative w-full">
      <Menu as="div" className="relative inline-block w-full text-left">
        <div>
          <Menu.Button className="w-full flex items-center gap-3 px-3 py-3 hover:bg-white/5 rounded-2xl cursor-pointer transition-all border border-transparent hover:border-white/10 group">
            <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-sm font-bold shadow-lg ring-2 ring-white/5 group-hover:ring-brand-accent/30 transition-all">
              MD
            </div>
            <div className="flex-1 overflow-hidden text-left">
              <div className="font-semibold text-xs text-white truncate">Mahima Dangi</div>
              <div className="text-[10px] text-gray-500 truncate italic">Academy Admin</div>
            </div>
            <ChevronUp className="w-4 h-4 text-gray-500 group-hover:text-white transition-colors" />
          </Menu.Button>
        </div>
        <Transition
          as={React.Fragment}
          enter="transition ease-out duration-100"
          enterFrom="transform opacity-0 scale-95 -translate-y-2"
          enterTo="transform opacity-100 scale-100 translate-y-0"
          leave="transition ease-in duration-75"
          leaveFrom="transform opacity-100 scale-100 translate-y-0"
          leaveTo="transform opacity-0 scale-95 -translate-y-2"
        >
          <Menu.Items className="absolute bottom-full left-0 mb-2 w-56 origin-bottom-left divide-y divide-white/5 rounded-2xl bg-[#1a1f2e] border border-white/10 shadow-2xl ring-1 ring-black/5 focus:outline-none overflow-hidden">
            <div className="px-1 py-1">
              <Menu.Item>
                {({ active }) => (
                  <button className={`${active ? 'bg-white/5 text-white' : 'text-gray-400'} group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors`}>
                    <User className="w-4 h-4" />
                    View Profile
                  </button>
                )}
              </Menu.Item>
              <Menu.Item>
                {({ active }) => (
                  <button 
                    onClick={onOpenSettings}
                    className={`${active ? 'bg-white/5 text-white' : 'text-gray-400'} group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors`}
                  >
                    <Settings className="w-4 h-4" />
                    Settings
                  </button>
                )}
              </Menu.Item>
            </div>
            <div className="px-1 py-1">
              <Menu.Item>
                {({ active }) => (
                  <button 
                    onClick={handleLogout}
                    className={`${active ? 'bg-red-500/10 text-red-500' : 'text-gray-400'} group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors`}
                  >
                    <LogOut className="w-4 h-4" />
                    Logout
                  </button>
                )}
              </Menu.Item>
            </div>
          </Menu.Items>
        </Transition>
      </Menu>
    </div>
  );
};

export default ProfileDropdown;
