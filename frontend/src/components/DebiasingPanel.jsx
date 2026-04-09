import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Zap, 
  Download, 
  Settings, 
  CheckCircle2, 
  AlertCircle,
  Activity,
  Maximize2
} from 'lucide-react'
import { runDebias } from '../services/api'
import Badge from './ui/Badge'

export default function DebiasingPanel({ fileId, targetCol, sensitiveCol }) {
  const [method, setMethod] = useState('smote')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleDebias = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await runDebias(fileId, targetCol, sensitiveCol, method)
      setResult(data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const downloadCSV = () => {
    if (!result?.fixed_dataset) return
    const csvContent = "data:text/csv;charset=utf-8," 
      + Object.keys(result.fixed_dataset[0]).join(",") + "\n"
      + result.fixed_dataset.map(row => Object.values(row).join(",")).join("\n")
    
    const encodedUri = encodeURI(csvContent)
    const link = document.createElement("a")
    link.setAttribute("href", encodedUri)
    link.setAttribute("download", `fairlens_fixed_${method}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const methods = [
    { id: 'smote', title: 'SMOTE Resampling', desc: 'Synthetic minority oversampling to balance distributions.', icon: Activity },
    { id: 'reweighting', title: 'Sample Reweighting', desc: 'Adjusts group importance without changing row count.', icon: Maximize2 },
    { id: 'threshold', title: 'Threshold Calibration', desc: 'Shifts dynamic decision boundaries per group.', icon: Settings },
  ]

  return (
    <div className="bg-slate-900 rounded-[2.5rem] p-10 text-white shadow-2xl shadow-slate-900/20 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full -mr-32 -mt-32" />
      
      <div className="flex flex-col lg:flex-row justify-between items-start gap-8 relative z-10 mb-12">
        <div className="max-w-xl space-y-4">
          <Badge variant="success" size="sm" className="bg-emerald-500/20 text-emerald-400 border-emerald-500/20">Remediation Module</Badge>
          <h2 className="text-3xl font-black tracking-tight">Algorithmic Bias Mitigation</h2>
          <p className="text-slate-400 font-medium leading-relaxed">
            Select a mitigation strategy to remediate the identified algorithmic disparities. FairLens will generate a sanitized training set ready for deployment.
          </p>
        </div>

        <button 
          onClick={handleDebias}
          disabled={loading || !!result}
          className={`px-10 py-5 rounded-2xl font-black text-lg transition-all flex items-center gap-3 whitespace-nowrap ${loading || result ? 'bg-slate-800 text-slate-500 border border-white/5' : 'bg-white text-slate-900 hover:scale-105 active:scale-95 shadow-xl shadow-white/10'}`}
        >
          {loading ? (
            <>
              <span className="w-5 h-5 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
              Processing...
            </>
          ) : result ? (
            <>
              <CheckCircle2 size={24} className="text-emerald-500" />
              Audit Mitigated
            </>
          ) : (
            <>
              <Zap size={24} />
              Optimize Fairness
            </>
          )}
        </button>
      </div>

      {!result ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative z-10">
          {methods.map((m) => (
            <button 
              key={m.id}
              onClick={() => setMethod(m.id)}
              className={`p-8 rounded-[2rem] border-2 text-left transition-all group ${method === m.id ? 'border-primary bg-primary/10 shadow-lg shadow-primary/5' : 'border-slate-800 bg-slate-800/30 hover:bg-slate-800/60'}`}
            >
              <div className={`w-12 h-12 rounded-2xl flex items-center justify-center mb-6 transition-colors ${method === m.id ? 'bg-primary text-white' : 'bg-slate-700 text-slate-400 group-hover:text-white group-hover:bg-slate-600'}`}>
                <m.icon size={24} />
              </div>
              <h4 className="text-lg font-black mb-2 transition-colors">{m.title}</h4>
              <p className="text-xs text-slate-400 font-bold leading-relaxed transition-colors group-hover:text-slate-300 uppercase tracking-widest">{m.desc}</p>
            </button>
          ))}
        </div>
      ) : (
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative z-10 bg-white/5 rounded-[2rem] p-10 border border-white/10"
        >
          <div className="flex flex-col md:flex-row items-center justify-between gap-12">
            <div className="grid grid-cols-2 gap-12 grow">
              <div>
                <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3">Input Observations</p>
                <p className="text-4xl font-black tracking-tight">{result.original_rows.toLocaleString()}</p>
              </div>
              <div className="border-l border-white/10 pl-12">
                <p className="text-[10px] font-black text-emerald-500 uppercase tracking-widest mb-3">Fairness Optimized Rows</p>
                <div className="flex items-center gap-3">
                  <p className="text-4xl font-black text-emerald-400 tracking-tight">{result.resampled_rows.toLocaleString()}</p>
                  <div className="p-1 px-2 bg-emerald-400/10 text-emerald-400 rounded-md text-[9px] font-black uppercase">
                    Balanced
                  </div>
                </div>
              </div>
            </div>
            
            <button 
              onClick={downloadCSV}
              className="bg-white text-slate-900 px-10 py-5 rounded-3xl font-black flex items-center gap-3 shadow-xl hover:bg-slate-50 hover:scale-105 active:scale-95 transition-all"
            >
              <Download size={24} />
              Export remediated.csv
            </button>
          </div>

          {method === 'threshold' && result.thresholds && (
            <div className="mt-12 pt-10 border-t border-white/10 space-y-6">
              <h4 className="text-[10px] font-black text-slate-500 uppercase tracking-[.3em]">Decision Boundary Recalibration</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                {Object.entries(result.thresholds).map(([grp, val]) => (
                  <div key={grp} className="bg-white/5 rounded-2xl p-5 border border-white/10 group hover:border-white/20 transition-all">
                    <p className="text-[10px] font-black text-slate-500 uppercase truncate mb-2">{grp}</p>
                    <p className="text-2xl font-black font-mono tracking-tighter text-emerald-400 group-hover:scale-110 transition-transform origin-left">{parseFloat(val).toFixed(3)}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      )}

      {error && (
        <div className="mt-8 p-5 bg-red-400/10 border border-red-400/20 rounded-2xl flex items-center gap-3 text-red-400 font-bold animate-shake">
          <AlertCircle size={20} />
          {error}
        </div>
      )}
    </div>
  )
}
