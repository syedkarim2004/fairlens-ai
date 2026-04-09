import { motion } from 'framer-motion';
import { Zap, Brain, GitCompare } from 'lucide-react';
import { AIResponseCard } from './UIComponents';

export default function DualComparisonPanel({ groqAnalysis, gemmaAnalysis, showComparison = true }) {
  if (!showComparison) {
    return (
      <AIResponseCard
        title="AI Analysis"
        tag="Fast AI"
        tagIcon={<Zap size={14} />}
        content={groqAnalysis}
        engine="groq"
      />
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-xl font-black text-white flex items-center gap-2">
          <GitCompare className="text-[#8855ff]" /> Dual AI Reasoning
        </h2>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-[#00ff88] shadow-[0_0_8px_#00ff88]" />
            <span className="text-[10px] font-black uppercase tracking-widest text-[#9494b8]">Groq Core</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-[#5588ff] shadow-[0_0_8px_#5588ff]" />
            <span className="text-[10px] font-black uppercase tracking-widest text-[#9494b8]">Gemma Core</span>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <AIResponseCard
          title="PRIMARY ANALYSIS"
          tag="⚡ Fast AI"
          tagIcon={<Zap size={14} />}
          content={groqAnalysis}
          engine="groq"
          delay={0.1}
        />
        <AIResponseCard
          title="DEEP AUDIT"
          tag="🧠 Deep AI"
          tagIcon={<Brain size={14} />}
          content={gemmaAnalysis}
          engine="gemma"
          delay={0.2}
        />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="glass-card-premium p-6 border border-[#8855ff]/20 bg-[#8855ff]/5"
      >
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-2xl bg-[#8855ff]/10 text-[#8855ff]">
            <Brain size={24} />
          </div>
          <div>
            <h4 className="text-sm font-black text-white uppercase tracking-widest mb-1">Combined Intelligence Insight</h4>
            <p className="text-sm text-[#9494b8] leading-relaxed">
              Synthesizing both Groq's rapid pattern matching and Gemma's deep reasoning. 
              The intersection of these analyses confirms high-risk areas in your dataset's <span className="text-white border-b border-[#8855ff]">sensitive attributes</span>. 
              Review the detailed metrics above to prioritize mitigation strategies.
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
