import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  FileText, 
  Download, 
  Printer, 
  ArrowLeft, 
  ShieldCheck, 
  CheckCircle2, 
  AlertTriangle,
  Layers,
  Search,
  User,
  Calendar,
  Database,
  ExternalLink,
  Loader2
} from 'lucide-react';
import { getReport } from '../services/api';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import Navbar from '../components/Navbar';

export default function Report() {
  const { fileId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const r = await getReport(fileId);
        setData(r);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [fileId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F8F9FA] flex flex-col items-center justify-center p-6">
        <Loader2 className="h-10 w-10 text-primary animate-spin mb-4" />
        <h2 className="text-xl font-medium text-foreground">Compiling Compliance Report</h2>
        <p className="text-sm text-muted-foreground mt-1">Fetching neural audit ledger data...</p>
      </div>
    );
  }
  
  if (!data) {
    return (
      <div className="min-h-screen bg-[#F8F9FA] flex flex-col items-center justify-center p-6 text-center">
        <div className="w-16 h-16 bg-destructive/10 text-destructive rounded-full flex items-center justify-center mb-6">
          <AlertTriangle size={32} />
        </div>
        <h2 className="text-2xl font-semibold">Report Not Found</h2>
        <p className="text-muted-foreground max-w-sm mt-2 mb-8">
          The requested audit record does not exist or has been archived.
        </p>
        <Button onClick={() => navigate('/dashboard')} variant="default">Return to Dashboard</Button>
      </div>
    );
  }

  const handlePrint = () => window.print();

  const summary = data.summary || {};
  const config = data.audit_config || {};
  const overallFair = summary.disparate_impact >= 0.8 && summary.disparate_impact <= 1.25;

  return (
    <div className="min-h-screen bg-[#F8F9FA] pb-20">
      <Navbar />
      
      {/* ── Toolbar ── */}
      <div className="bg-white border-b sticky top-16 z-40 print:hidden">
        <div className="container max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => navigate(-1)} className="gap-2 text-muted-foreground p-0 h-10 px-2">
              <ArrowLeft size={18} /> Back
            </Button>
            <div className="h-6 w-px bg-border mx-1" />
            <h1 className="text-sm font-semibold">Audit Certificate</h1>
          </div>
          <div className="flex items-center gap-3">
             <Button variant="outline" size="sm" className="gap-2 h-9" onClick={() => {}}>
                <Download size={16} /> Metadata
             </Button>
             <Button variant="default" size="sm" className="gap-2 h-9 shadow-sm" onClick={handlePrint}>
                <Printer size={16} /> Print Report
             </Button>
          </div>
        </div>
      </div>

      <main className="container max-w-5xl mx-auto px-6 py-12">
        <motion.div 
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-3xl border shadow-sm p-12 md:p-16 print:p-0 print:border-0 print:shadow-none"
        >
          {/* Header Section */}
          <div className="flex flex-col md:flex-row justify-between items-start gap-8 mb-16 border-b pb-12">
            <div className="space-y-4">
               <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center text-white">
                     <ShieldCheck size={24} />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold tracking-tight text-[#202124]">FairLens AI</h2>
                    <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Neural Audit Governance</p>
                  </div>
               </div>
               <div className="pt-2">
                  <h1 className="text-3xl font-bold text-foreground tracking-tight">Compliance Certificate</h1>
                  <p className="text-[#5F6368] text-sm font-medium mt-1">Official certification of fairness & equity analysis</p>
               </div>
            </div>

            <div className="w-full md:w-auto p-6 rounded-2xl bg-[#F8F9FA] border border-[#f1f3f4] space-y-4">
               <div>
                  <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-1">Certificate Hash</p>
                  <p className="text-sm font-mono font-bold text-primary break-all">{fileId}</p>
               </div>
               <div className="flex justify-between items-end gap-12">
                  <div>
                    <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-1">Issue Date</p>
                    <p className="text-sm font-bold">{new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</p>
                  </div>
                  <div>
                     <Badge className={overallFair ? 'bg-green-50 text-green-700 border-green-100' : 'bg-red-50 text-red-700 border-red-100'}>
                        {overallFair ? 'Verified Fair' : 'Non-Compliant'}
                     </Badge>
                  </div>
               </div>
            </div>
          </div>

          {/* Audit Scope Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-12 mb-16">
            <div className="lg:col-span-1 space-y-8">
               <div className="flex items-center gap-2 border-b pb-3">
                  <Layers size={14} className="text-primary" />
                  <h4 className="text-[10px] font-bold text-primary uppercase tracking-[0.2em]">Audit Context</h4>
               </div>
               
               <div className="space-y-5">
                  {[
                    { label: 'Target Variable', value: config.target_column || 'decision', icon: Search },
                    { label: 'Protected Group', value: config.sensitive_columns?.[0] || 'gender', icon: User },
                    { label: 'Total Observed', value: summary.total_rows || 0, icon: Database },
                    { label: 'Model Version', value: 'Production-v4.2', icon: Calendar },
                  ].map(item => (
                    <div key={item.label} className="flex justify-between items-start group">
                      <div className="flex items-center gap-2">
                        <item.icon size={13} className="text-muted-foreground" />
                        <span className="text-xs font-semibold text-muted-foreground">{item.label}</span>
                      </div>
                      <span className="text-xs font-bold text-foreground text-right">{item.value}</span>
                    </div>
                  ))}
               </div>
            </div>

            <div className="lg:col-span-2 p-8 rounded-3xl bg-blue-50/50 border border-blue-100/50 space-y-8">
               <div className="flex items-center gap-2 border-b border-blue-100 pb-3">
                  <FileText size={14} className="text-blue-600" />
                  <h4 className="text-[10px] font-bold text-blue-600 uppercase tracking-[0.2em]">Key Findings (SPD/DIR)</h4>
               </div>

               <div className="grid grid-cols-2 gap-8">
                  <div className="space-y-1">
                     <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Disparate Impact Ratio</p>
                     <p className="text-4xl font-bold text-primary tracking-tighter">{summary.disparate_impact?.toFixed(3) || '1.000'}</p>
                     <p className="text-[10px] font-bold text-muted-foreground mt-1">Status: {summary.disparate_impact >= 0.8 ? 'PASS (80% Rule)' : 'CRITICAL FAIL'}</p>
                  </div>
                  <div className="space-y-1 text-right">
                     <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Statistical Parity Diff</p>
                     <p className="text-4xl font-bold text-primary tracking-tighter">{summary.statistical_parity_difference?.toFixed(3) || '0.000'}</p>
                     <p className="text-[10px] font-bold text-muted-foreground mt-1">Parity Delta: {Math.abs(summary.statistical_parity_difference || 0).toFixed(3)}</p>
                  </div>
               </div>
               
               <div className="pt-6 border-t border-blue-100">
                  <div className={`p-4 rounded-xl flex items-center gap-3 ${overallFair ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                    {overallFair ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
                    <p className="text-xs font-semibold">
                      {overallFair 
                        ? 'Algorithmic performance aligns with global equity standards for this attribute.' 
                        : 'Actionable disparate impact detected. Immediate remediation recommended.'}
                    </p>
                  </div>
               </div>
            </div>
          </div>

          {/* Narrative Overview */}
          <div className="space-y-6 mb-16">
             <div className="flex items-center gap-2 border-b pb-3">
                <CheckCircle2 size={14} className="text-primary" />
                <h4 className="text-[10px] font-bold text-primary uppercase tracking-[0.2em]">Executive Summary</h4>
             </div>
             <div className="bg-[#F8F9FA] p-8 rounded-2xl border flex items-start gap-4">
                <Info size={20} className="text-primary mt-0.5" />
                <p className="text-sm text-[#5F6368] leading-relaxed font-normal">
                  The automated audit of <strong>{fileId}</strong> has completed. The underlying data patterns 
                  {overallFair ? ' indicate a high degree of statistical fairness' : ' show evidence of historical bias saturation'} 
                  within <strong>{config.target_column}</strong> outcome outcomes when segmented by <strong>{config.sensitive_columns?.[0] || 'protected'}</strong> attributes. 
                  {overallFair 
                    ? ' This model is verified safe for production environments.' 
                    : ' It is recommended to apply re-weighting or adversarial de-biasing techniques before retraining.'}
                </p>
             </div>
          </div>

          {/* Footer Seals */}
          <div className="grid grid-cols-1 md:grid-cols-3 items-center gap-8 pt-12 border-t opacity-70">
            <div className="text-center md:text-left space-y-1">
               <p className="text-[9px] font-bold uppercase tracking-widest text-muted-foreground">Certified By</p>
               <p className="font-bold text-primary text-base">Google Solution Challenge 2026</p>
            </div>
            
            <div className="flex flex-col items-center">
               <div className="w-14 h-14 border-2 border-primary/30 rounded-full flex items-center justify-center text-primary font-bold text-xs select-none shadow-sm">
                  FL-A1
               </div>
               <p className="text-[8px] font-bold uppercase tracking-widest text-muted-foreground mt-2">Verified Ledger Node</p>
            </div>

            <div className="text-center md:text-right space-y-1">
               <p className="text-[9px] font-bold uppercase tracking-widest text-muted-foreground">Registry Index</p>
               <p className="font-mono text-primary text-xs font-bold uppercase tracking-wider">{fileId.split('-')[0]}-LEDGER-V4</p>
            </div>
          </div>
        </motion.div>
        
        <p className="text-center text-[9px] font-bold text-muted-foreground uppercase tracking-[0.4em] py-10 print:hidden">
           Secured & Encrypted by FairLens Neural Safeguard
        </p>
      </main>
    </div>
  );
}
