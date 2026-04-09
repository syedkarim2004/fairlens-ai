import { motion } from 'framer-motion'
import { BarChart3, Info } from 'lucide-react'

export default function ShapChart({ shapData }) {
  // Defensive check for various types of empty data
  if (!shapData || typeof shapData !== 'object' || Object.keys(shapData).length === 0 || shapData.error) {
    return (
      <div className="h-64 border border-dashed border-slate-200 rounded-[2rem] flex flex-col items-center justify-center text-center p-8 bg-slate-50/50">
        <BarChart3 size={40} className="text-slate-300 mb-4" />
        <p className="text-slate-400 font-bold text-sm tracking-tight uppercase">Feature Attribution Unavailable</p>
        <p className="text-[10px] text-slate-400 mt-1 uppercase tracking-widest font-black opacity-60">SHAP kernel failed to converge on sample size</p>
      </div>
    )
  }

  // Transform object { feature: score } to sorted array of top 5 (Dashboard style)
  const entries = Object.entries(shapData)
    .map(([k, v]) => [k, Number(v) || 0])
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5)

  if (entries.length === 0) return null

  const maxVal = Math.max(...entries.map(([, v]) => v), 0.0001)

  return (
    <div className="space-y-8">
      <div className="space-y-5">
        {entries.map(([feature, value], idx) => {
          const widthPercent = (value / maxVal) * 100
          const isSuspect = ['gender', 'sex', 'race', 'age'].some(s => feature.toLowerCase().includes(s))

          return (
            <div key={feature} className="group">
              <div className="flex justify-between items-center mb-2 px-1">
                <span className="text-xs font-black text-slate-700 tracking-tight capitalize group-hover:text-primary transition-colors">{feature}</span>
                <span className="text-[10px] font-mono font-black text-slate-400 uppercase tracking-widest">{(value * 100).toFixed(1)}% Impact</span>
              </div>
              <div className="h-4 bg-slate-50 rounded-full overflow-hidden border border-slate-100 group-hover:shadow-sm transition-shadow">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: `${widthPercent}%` }}
                  transition={{ delay: idx * 0.1, duration: 1, ease: "easeOut" }}
                  className={`h-full ${isSuspect ? 'bg-danger' : 'bg-primary'}`}
                />
              </div>
            </div>
          )
        })}
      </div>

      <div className="p-5 bg-slate-50 rounded-2xl border border-slate-100 flex items-start gap-3">
        <Info size={16} className="text-primary mt-0.5 shrink-0" />
        <div className="space-y-1">
          <p className="text-[10px] font-black text-primary uppercase tracking-widest">Interpretation Protocol</p>
          <p className="text-[11px] text-slate-500 leading-relaxed font-bold">
            Higher percentages indicate stronger model attribution. Red bars (protected attributes) indicate direct disparate treatment risk.
          </p>
        </div>
      </div>
    </div>
  )
}
