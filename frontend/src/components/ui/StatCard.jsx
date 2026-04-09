import { motion } from 'framer-motion'

export default function StatCard({ label, value, icon: Icon, trend, status = 'neutral' }) {
  const statusStyles = {
    safe: 'text-accent bg-accent/10',
    warning: 'text-amber-600 bg-amber-50',
    danger: 'text-danger bg-danger/10',
    neutral: 'text-text-muted bg-gray-50',
  }

  return (
    <motion.div 
      whileHover={{ y: -4 }}
      className="bg-white p-6 rounded-[1.25rem] border border-border-subtle shadow-sm flex flex-col gap-4 card-transition"
    >
      <div className="flex justify-between items-start">
        <div className={`p-2.5 rounded-xl ${statusStyles[status]}`}>
          <Icon size={20} />
        </div>
        {trend && (
          <span className={`text-[10px] font-black px-2 py-0.5 rounded-full uppercase tracking-widest ${trend > 0 ? 'bg-accent/10 text-accent' : 'bg-danger/10 text-danger'}`}>
            {trend > 0 ? '+' : ''}{trend}%
          </span>
        )}
      </div>

      <div>
        <p className="text-xs font-bold text-text-muted uppercase tracking-widest mb-1">{label}</p>
        <h3 className="text-3xl font-black text-primary tracking-tight">{value}</h3>
      </div>
    </motion.div>
  )
}
