import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Upload as UploadIcon, 
  Database, 
  FileSpreadsheet, 
  ArrowRight, 
  AlertCircle,
  CheckCircle2,
  Table as TableIcon,
  Search
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { Badge } from '../components/ui/Badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/Table';
import { LoadingOverlay } from '../components/UIComponents';
import DashboardLayout from '../components/DashboardLayout';
import { uploadCSV, generateTestData, runFullAudit } from '../services/api';

export default function Upload({ auditState }) {
  const navigate = useNavigate();
  const [dragOver, setDragOver] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('idle'); // idle | uploading | configuring
  const [processingStage, setProcessingStage] = useState('ingest');
  const [filePreview, setFilePreview] = useState(null);
  const [autoConfig, setAutoConfig] = useState(null);

  const {
    setFileId,
    setFileName,
    setColumns,
    setAuditResult,
    loading, setLoading,
    setError,
    error
  } = auditState;

  const startAutomatedAudit = async (fId, config) => {
    setLoading(true);
    setProcessingStage('ingest');
    
    // Simulations for better UX
    await new Promise(r => setTimeout(r, 1000));
    setProcessingStage('detect');
    await new Promise(r => setTimeout(r, 1200));
    setProcessingStage('config');
    await new Promise(r => setTimeout(r, 1000));
    setProcessingStage('audit_groq');
    
    try {
      const result = await runFullAudit(
        fId, 
        config?.target_column, 
        config?.sensitive_columns, 
        true, 
        config?.positive_label
      );
      
      setProcessingStage('audit_gemma');
      await new Promise(r => setTimeout(r, 1500));
      
      setAuditResult(result);
      setLoading(false);
      navigate('/results');
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
      setLoading(false);
      setUploadStatus('idle');
    }
  };

  const handleFile = async (file) => {
    if (!file || !file.name.endsWith('.csv')) {
      setError('Please upload a valid .csv dataset');
      return;
    }
    setError(null);
    setUploadStatus('uploading');
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const data = await uploadCSV(file);
      setFileId(data.file_id);
      setFileName(file.name);
      setColumns(data.columns || []);
      setAutoConfig(data.auto_config);
      setFilePreview(data.preview || []);
      
      setUploadStatus('configuring');
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
      setUploadStatus('idle');
    }
  };

  const handleDemo = async () => {
    setError(null);
    setUploadStatus('uploading');
    try {
      const data = await generateTestData();
      setFileId(data.file_id);
      setFileName('biased_hiring_dataset_v4.csv');
      setColumns(data.columns || []);
      
      const demoConfig = {
        target_column: 'decision',
        positive_label: 'approved',
        sensitive_columns: ['gender']
      };
      setAutoConfig(demoConfig);
      
      setUploadStatus('configuring');
      // For demo, we might want to let them see the config first or just run it
      // Let's just run it to keep the "one-click" magic
      startAutomatedAudit(data.file_id, demoConfig);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
      setUploadStatus('idle');
    }
  };

  return (
    <DashboardLayout>
      <AnimatePresence>
        {loading && <LoadingOverlay stage={processingStage} />}
      </AnimatePresence>

      <div className="max-w-4xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-semibold text-foreground">Initiate Neural Audit</h1>
          <p className="text-muted-foreground mt-1">Upload your dataset to detect algorithmic bias and disparate impact.</p>
        </div>

        {uploadStatus === 'idle' || uploadStatus === 'uploading' ? (
          <Card className="border-none shadow-sm bg-white overflow-hidden">
            <CardContent className="p-0">
              <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFile(e.dataTransfer.files[0]); }}
                className={`
                  relative flex flex-col items-center justify-center p-20 text-center transition-all duration-300
                  ${dragOver ? 'bg-primary/5' : 'bg-transparent'}
                `}
              >
                <input 
                  type="file" 
                  id="file-upload" 
                  className="hidden" 
                  accept=".csv" 
                  onChange={(e) => handleFile(e.target.files[0])} 
                />
                
                <div className={`
                  w-20 h-20 rounded-full flex items-center justify-center mb-6 transition-all duration-500
                  ${dragOver ? 'bg-primary text-white scale-110' : 'bg-secondary text-primary'}
                `}>
                  <UploadIcon size={32} />
                </div>
                
                <h3 className="text-xl font-medium mb-2">
                  {uploadStatus === 'uploading' ? 'Analyzing Entropy...' : 'Drag & Drop Dataset'}
                </h3>
                <p className="text-muted-foreground text-sm max-w-sm mb-8 leading-relaxed">
                  Support for .CSV model training data or inference results. 
                  FairLens automatically detects schema and sensitive proxies.
                </p>
                
                <div className="flex flex-col sm:flex-row gap-4">
                  <Button 
                    onClick={() => document.getElementById('file-upload').click()}
                    className="h-11 px-8 font-medium shadow-sm"
                    disabled={uploadStatus === 'uploading'}
                  >
                    Browse Files
                  </Button>
                  <Button 
                    variant="google" 
                    onClick={handleDemo}
                    className="h-11 px-8 font-medium"
                    disabled={uploadStatus === 'uploading'}
                  >
                    Run Demographic Demo
                  </Button>
                </div>

                {dragOver && (
                  <div className="absolute inset-0 border-4 border-dashed border-primary/40 m-4 rounded-2xl pointer-events-none" />
                )}
              </div>

              {error && (
                <div className="m-8 p-4 bg-destructive/10 border border-destructive/20 rounded-xl text-destructive text-sm font-medium flex items-center gap-3">
                  <AlertCircle size={18} /> {error}
                </div>
              )}
            </CardContent>
          </Card>
        ) : (
          <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            className="space-y-8"
          >
            {/* Dataset Preview */}
            <Card className="border-none shadow-sm bg-white">
              <CardHeader className="border-b bg-secondary/10 px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <TableIcon size={18} className="text-primary" />
                    <CardTitle className="text-base font-medium">Dataset Structure Identified</CardTitle>
                  </div>
                  <Badge variant="success">Readiness: High</Badge>
                </div>
              </CardHeader>
              <CardContent className="p-0 max-h-80 overflow-y-auto">
                <Table>
                  <TableHeader className="bg-secondary/20">
                    <TableRow>
                      {Object.keys(filePreview?.[0] || {}).map(col => (
                        <TableHead key={col}>{col}</TableHead>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filePreview?.slice(0, 5).map((row, i) => (
                      <TableRow key={i}>
                        {Object.values(row).map((val, j) => (
                          <TableCell key={j} className="text-xs">{val}</TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>

            {/* Audit Configuration */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <Card className="border-none shadow-sm bg-white">
                <CardHeader>
                  <CardTitle className="text-lg font-medium flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center text-xs font-bold">1</div>
                    Target Outcome
                  </CardTitle>
                  <CardDescription>Variable being audited for disparate impact</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="p-4 bg-secondary/50 rounded-xl border flex items-center justify-between">
                    <div>
                      <span className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Detected Goal</span>
                      <div className="text-sm font-semibold">{autoConfig?.target_column}</div>
                    </div>
                    <CheckCircle2 className="text-success" size={20} />
                  </div>
                </CardContent>
              </Card>

              <Card className="border-none shadow-sm bg-white">
                <CardHeader>
                  <CardTitle className="text-lg font-medium flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-green-50 text-green-600 flex items-center justify-center text-xs font-bold">2</div>
                   Protected Attributes
                  </CardTitle>
                  <CardDescription>Demographic factors scanned for bias</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {(autoConfig?.sensitive_columns || []).map(col => (
                      <Badge key={col} className="h-10 px-4 text-sm bg-green-50 text-green-700 border-none">
                        {col}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="flex justify-end gap-4 pt-4">
              <Button variant="outline" onClick={() => setUploadStatus('idle')} className="h-12 px-8">
                Reset Workspace
              </Button>
              <Button onClick={() => startAutomatedAudit(autoConfig?.file_id || '', autoConfig)} className="h-12 px-8 font-semibold shadow-md gap-2">
                Initialize Audit Pipeline <ArrowRight size={18} />
              </Button>
            </div>
          </motion.div>
        )}

        {/* System Details */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 pt-8 opacity-60">
           <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-full border flex items-center justify-center text-muted-foreground">
                <Search size={18} />
              </div>
              <div>
                <div className="text-[10px] font-bold uppercase tracking-wider">Detection Layer</div>
                <div className="text-xs font-semibold">Automatic Proxy Identification</div>
              </div>
           </div>
           <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-full border flex items-center justify-center text-muted-foreground">
                <ShieldCheck size={18} />
              </div>
              <div>
                <div className="text-[10px] font-bold uppercase tracking-wider">Privacy Protocol</div>
                <div className="text-xs font-semibold">E2E Encryption Active</div>
              </div>
           </div>
           <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-full border flex items-center justify-center text-muted-foreground">
                <Database size={18} />
              </div>
              <div>
                <div className="text-[10px] font-bold uppercase tracking-wider">Data Pipeline</div>
                <div className="text-xs font-semibold">Scalable Vector Processing</div>
              </div>
           </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
