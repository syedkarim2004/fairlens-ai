import { Search, Bell, User } from 'lucide-react'

export default function TopNav() {
  return (
    <header className="h-16 bg-white border-b border-border-subtle flex items-center justify-between px-8 sticky top-0 z-20">
      <div className="flex items-center gap-6">
        <div className="relative group">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted group-focus-within:text-primary transition-colors" size={18} />
          <input 
            type="text" 
            placeholder="Search audits, models, datasets..." 
            className="w-80 h-10 pl-10 pr-4 rounded-full bg-gray-50 border border-gray-100 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary transition-all" 
          />
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button className="p-2 text-text-muted hover:bg-gray-50 rounded-full transition-colors relative">
          <Bell size={20} />
          <span className="absolute top-2 right-2 w-2 h-2 bg-danger rounded-full border-2 border-white" />
        </button>
        
        <div className="h-8 w-px bg-border-subtle mx-2" />

        <div className="flex items-center gap-3 pl-2 cursor-pointer hover:opacity-80 transition-opacity">
          <div className="text-right hidden md:block">
            <p className="text-sm font-black text-primary leading-tight">James Doherty</p>
            <p className="text-[10px] font-bold text-text-muted uppercase tracking-widest">Enterprise Admin</p>
          </div>
          <div className="w-10 h-10 rounded-full bg-primary/5 border border-primary/10 flex items-center justify-center text-primary font-black overflow-hidden shadow-sm">
            JD
          </div>
        </div>
      </div>
    </header>
  )
}
