import { motion } from 'framer-motion'

export default function FilePreviewTable({ data, columns }) {
  if (!data || data.length === 0) return null

  return (
    <div className="bg-white border border-border-subtle rounded-2xl overflow-hidden shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead className="bg-gray-50 border-b border-border-subtle">
            <tr>
              {columns.map((col) => (
                <th 
                  key={col} 
                  className="px-6 py-4 text-[10px] font-black text-text-muted uppercase tracking-widest"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, idx) => (
              <motion.tr 
                key={idx}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: idx * 0.05 }}
                className="border-b border-gray-50 last:border-0 hover:bg-gray-50/50 transition-colors"
              >
                {columns.map((col) => (
                  <td key={col} className="px-6 py-4 text-sm font-bold text-primary truncate max-w-[200px]">
                    {String(row[col])}
                  </td>
                ))}
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
      {data.length >= 3 && (
        <div className="p-4 bg-gray-50 border-t border-border-subtle text-center">
          <p className="text-[10px] font-bold text-text-muted uppercase tracking-widest">
            Showing initial {data.length} preview records
          </p>
        </div>
      )}
    </div>
  )
}
