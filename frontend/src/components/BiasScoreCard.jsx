import { motion } from 'framer-motion'

const RiskBadge = ({ risk }) => {
  const colors = {
    HIGH: 'bg-red-100 text-red-700',
    MEDIUM: 'bg-yellow-100 text-yellow-700',
    LOW: 'bg-green-100 text-green-700',
  }
  return (
    <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${colors[risk] || colors.MEDIUM}`}>
      {risk} RISK
    </span>
  )
}

export default function BiasScoreCard({ column, metrics }) {
  // AIF360 disparate impact: standard is 0.8 to 1.25.
  // Below 0.8 is biased against unprivileged. 
  // Above 1.25 is biased against privileged.
  const di = metrics.disparate_impact_ratio || metrics.disparate_impact || 0
  const spd = metrics.statistical_parity_difference || 0
  
  let risk = 'LOW'
  if (di < 0.8) risk = 'HIGH'
  else if (di < 0.9) risk = 'MEDIUM'

  // Gauge Percentage (0 to 2 range mapped to 0-100%)
  const gaugePercent = Math.min(Math.max((di / 2) * 100, 0), 100)

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm hover:shadow-md transition-shadow"
    >
      <div className="flex justify-between items-start mb-6">
        <div>
          <h3 className="text-lg font-bold text-dark capitalize">{column} Analysis</h3>
          <p className="text-sm text-gray-500">AIF360 Parity Metrics</p>
        </div>
        <RiskBadge risk={risk} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
        {/* Visual Gauge */}
        <div className="relative pt-4">
          <div className="flex justify-between text-xs font-semibold text-gray-400 mb-2">
            <span>0.0</span>
            <span className="text-primary">1.0 (Ideal)</span>
            <span>2.0</span>
          </div>
          <div className="h-4 w-full bg-gray-100 rounded-full overflow-hidden flex relative">
            {/* Ideal Zone Background */}
            <div className="absolute left-[40%] right-[37.5%] h-full bg-green-50" title="Fair Zone" />
            {/* Actual Pointer */}
            <motion.div 
              initial={{ width: 0 }}
              animate={{ width: `${gaugePercent}%` }}
              className={`h-full relative z-10 ${risk === 'HIGH' ? 'bg-red-500' : risk === 'MEDIUM' ? 'bg-yellow-500' : 'bg-primary'}`}
            />
          </div>
          <p className="mt-4 text-center">
            <span className="text-3xl font-black text-dark">{di.toFixed(3)}</span>
            <span className="block text-xs font-bold text-gray-400 uppercase tracking-widest mt-1">Disparate Impact Ratio</span>
          </p>
        </div>

        {/* Interpretation */}
        <div className="space-y-4">
          <div className="p-4 bg-gray-50 rounded-xl">
            <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">Statistical Parity Diff</p>
            <p className="text-xl font-bold text-dark">{spd.toFixed(3)}</p>
          </div>
          <div className="text-sm text-gray-600 leading-relaxed">
            {risk === 'HIGH' ? (
              <p>⚠️ <span className="font-bold">Significant Bias Detected.</span> The model shows a strong preference for specific groups, potentially violating the 80% rule.</p>
            ) : risk === 'MEDIUM' ? (
              <p>⚡ <span className="font-bold">Mild Disparity.</span> There are minor differences in outcome rates. Monitoring is recommended.</p>
            ) : (
              <p>✅ <span className="font-bold">Fair Distribution.</span> Outcomes are distributed equitably across this protected attribute.</p>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  )
}
