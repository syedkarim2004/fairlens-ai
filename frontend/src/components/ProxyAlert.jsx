import { motion } from 'framer-motion'
import { AlertTriangle, Fingerprint } from 'lucide-react'

export default function ProxyAlert({ proxyData, isSaaS = false }) {
  if (!proxyData || Object.keys(proxyData).length === 0) return null

  if (isSaaS) {
    return (
      <div className="bg-amber-50 border border-amber-200 rounded-[2rem] p-8 card-shadow space-y-6">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-amber-100 text-amber-600 rounded-2xl flex items-center justify-center">
            <AlertTriangle size={24} />
          </div>
          <div>
            <h3 className="text-lg font-black text-slate-900 tracking-tight">Proxy Variable Risk</h3>
            <p className="text-xs text-amber-800 font-bold uppercase tracking-widest mt-0.5">High Correlation Detected</p>
          </div>
        </div>

        <div className="space-y-3">
          {Object.entries(proxyData).map(([col, score]) => (
            <div 
              key={col} 
              className="bg-white/80 border border-amber-100 rounded-xl px-4 py-3 flex items-center justify-between group hover:border-amber-300 transition-colors"
            >
              <div className="flex items-center gap-3">
                <Fingerprint size={14} className="text-amber-500" />
                <span className="text-xs font-black text-slate-800 uppercase tracking-tight capitalize">{col}</span>
              </div>
              <span className="text-[10px] font-black font-mono text-amber-700 bg-amber-50 px-2 py-1 rounded">
                {Math.round(score * 100)}% Corr.
              </span>
            </div>
          ))}
        </div>

        <div className="pt-4 border-t border-amber-100">
           <p className="text-[10px] font-black text-amber-800 uppercase tracking-[0.1em] leading-relaxed">
             Recommendation: Consider masking high-dependency columns to prevent proxy-based demographic leakage.
           </p>
        </div>
      </div>
    )
  }

  return (
    <motion.div 
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className="bg-amber-50 border border-amber-100 rounded-[2.5rem] p-10 relative overflow-hidden card-shadow"
    >
      <div className="absolute -right-8 -bottom-8 opacity-5 pointer-events-none select-none">
        <AlertTriangle size={160} className="text-amber-600" />
      </div>

      <div className="flex items-start gap-6 relative">
        <div className="w-16 h-16 rounded-2xl bg-amber-100 text-amber-600 flex items-center justify-center flex-shrink-0 shadow-sm">
          <AlertTriangle size={32} />
        </div>
        <div className="flex-1">
          <h3 className="text-2xl font-black text-slate-900 tracking-tight mb-2">Proxy Variable Risk Notification</h3>
          <p className="text-sm text-slate-600 font-medium mb-8 max-w-2xl leading-relaxed">
            Non-protected columns demonstrate excessive statistical dependency with sensitive groups. These variables may inadvertently encode historical bias.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(proxyData).map(([col, score]) => (
              <div 
                key={col} 
                className="bg-white border border-amber-100 rounded-2xl px-5 py-4 flex items-center justify-between shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                  <span className="text-sm font-black text-slate-800 capitalize tracking-tight">{col}</span>
                </div>
                <span className="text-xs font-mono font-black text-amber-700 bg-amber-50 px-2 py-1 rounded">
                  {Math.round(score * 100)}% Reliability
                </span>
              </div>
            ))}
          </div>

          <div className="mt-10 pt-6 border-t border-amber-100/50">
            <p className="text-[10px] font-black text-amber-800 uppercase tracking-[0.2em] inline-flex items-center gap-2">
              <span className="w-4 h-px bg-amber-300" /> Administrative Action Required
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
