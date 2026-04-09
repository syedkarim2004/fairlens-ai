import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { 
  ShieldCheck, 
  Zap, 
  Database, 
  FileCheck, 
  ArrowRight,
  BarChart,
  Lock,
  Search
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card, CardContent } from '../components/ui/Card';
import Navbar from '../components/Navbar';

export default function Landing() {
  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      
      {/* ── Hero Section ── */}
      <section className="relative pt-20 pb-32 overflow-hidden">
        <div className="container px-6 mx-auto max-w-7xl relative z-10">
          <div className="flex flex-col items-center text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent text-accent-foreground text-xs font-semibold mb-8 uppercase tracking-wider"
            >
              <ShieldCheck size={14} />
              Enterprise AI Safety Platform
            </motion.div>
            
            <motion.h1 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-5xl md:text-7xl font-semibold tracking-tight text-[#202124] leading-[1.1] mb-8"
            >
              Unbiased AI Decisions. <br />
              <span className="text-primary font-bold">Scientifically Verified.</span>
            </motion.h1>
            
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="max-w-2xl text-xl text-[#5F6368] mb-12 leading-relaxed"
            >
              The world's first dual-core auditing platform for mission-critical machine learning. 
              Detect bias, ensure compliance, and build trust in seconds.
            </motion.p>
            
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="flex flex-col sm:flex-row items-center gap-4"
            >
              <Link to="/login">
                <Button size="lg" className="px-8 text-lg font-medium h-14 rounded-full">
                  Get Started for Free
                </Button>
              </Link>
              <Link to="/dashboard?demo=true">
                <Button variant="outline" size="lg" className="px-8 text-lg font-medium h-14 rounded-full">
                  Run Interactive Demo
                </Button>
              </Link>
            </motion.div>
          </div>
        </div>
        
        {/* Background Visual Element */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-primary/5 rounded-full blur-[120px] -z-10" />
      </section>

      {/* ── Stats/Logos Row ── */}
      <section className="py-12 border-y bg-secondary/30">
        <div className="container px-6 mx-auto max-w-7xl">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {[
              { label: 'Audits Completed', val: '1.2M+' },
              { label: 'Bias Detected', val: '450K+' },
              { label: 'Compliance Level', val: 'SOC2 Type II' },
              { label: 'Data Protected', val: '100% Secure' },
            ].map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="text-2xl font-bold text-foreground mb-1">{stat.val}</div>
                <div className="text-xs text-muted-foreground uppercase tracking-widest font-semibold">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features Section ── */}
      <section className="py-32">
        <div className="container px-6 mx-auto max-w-7xl">
          <div className="text-center mb-20">
            <h2 className="text-3xl md:text-4xl font-semibold mb-4">Engineered for Absolute Trust</h2>
            <p className="text-muted-foreground text-lg">Automating the complex math of fairness for modern AI systems.</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: Search,
                title: 'Bias Detection',
                desc: 'Automatic identification of disparate impact across 20+ protected attributes in tabular datasets.',
                color: 'bg-blue-50 text-blue-600'
              },
              {
                icon: BarChart,
                title: 'Deep SHAP Analysis',
                desc: 'Quantum-accelerated feature importance analysis to understand exactly WHY bias exists.',
                color: 'bg-green-50 text-green-600'
              },
              {
                icon: FileCheck,
                title: 'Compliance Shield',
                desc: 'Generate boardroom-ready PDF reports that satisfy EEOC, GDPR, and AI Act requirements.',
                color: 'bg-purple-50 text-purple-600'
              }
            ].map((feat, i) => (
              <Card key={feat.title} className="border-none shadow-none hover:bg-secondary/50 transition-google p-8">
                <div className={`w-12 h-12 rounded-xl ${feat.color} flex items-center justify-center mb-6`}>
                  <feat.icon size={24} />
                </div>
                <h3 className="text-xl font-semibold mb-4">{feat.title}</h3>
                <p className="text-muted-foreground leading-relaxed">
                  {feat.desc}
                </p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* ── How it Works ── */}
      <section className="py-32 bg-secondary/30">
        <div className="container px-6 mx-auto max-w-7xl">
          <div className="grid lg:grid-cols-2 gap-20 items-center">
            <div>
              <h2 className="text-4xl font-semibold mb-8">Three steps to a <br /><span className="text-primary italic">fairer future.</span></h2>
              <div className="space-y-12">
                {[
                  { step: '01', title: 'Ingest Dataset', desc: 'Securely upload your ML training data or model predictions in CSV or Parquet format.' },
                  { step: '02', title: 'Neural Audit', desc: 'Our dual-AI engine cross-references statistical parity with causal feature attribution.' },
                  { step: '03', title: 'Remediate', desc: 'Download detailed mitigation strategies to remove bias without sacrificing accuracy.' },
                ].map((item) => (
                  <div key={item.step} className="flex gap-6">
                    <div className="text-3xl font-bold text-primary opacity-30">{item.step}</div>
                    <div>
                      <h4 className="text-xl font-semibold mb-2">{item.title}</h4>
                      <p className="text-muted-foreground">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-white rounded-3xl p-8 shadow-md-soft border">
               <div className="aspect-video bg-secondary rounded-2xl flex items-center justify-center flex-col gap-4">
                  <BarChart size={48} className="text-primary/20" />
                  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-[0.3em]">System Interface Preview</span>
               </div>
               <div className="mt-8 space-y-4">
                  <div className="h-4 w-3/4 bg-secondary rounded" />
                  <div className="h-4 w-full bg-secondary rounded" />
                  <div className="h-4 w-1/2 bg-secondary rounded" />
               </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Simple Footer ── */}
      <footer className="py-20 border-t">
        <div className="container px-6 mx-auto max-w-7xl flex flex-col md:flex-row justify-between items-center gap-10">
          <div className="flex items-center space-x-2">
            <div className="bg-primary rounded-lg p-1">
              <ShieldCheck className="h-6 w-6 text-white" />
            </div>
            <span className="text-xl font-medium tracking-tight">FairLensAI</span>
          </div>
          <div className="text-sm text-muted-foreground text-center">
            © 2026 Syed Abdul Karim. Built for global AI compliance.
          </div>
          <div className="flex gap-8">
            {['Terms', 'Privacy', 'Status', 'Security'].map(item => (
              <span key={item} className="text-sm font-medium text-muted-foreground hover:text-primary cursor-pointer transition-colors">
                {item}
              </span>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}
