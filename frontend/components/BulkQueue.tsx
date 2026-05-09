import React, { useState, useEffect } from 'react';
import { fetchApi } from '@/utils/apiClient';
import { toast } from 'sonner';
import { Loader2, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function BulkQueue({ batchId, initialReceipts }: { batchId: string, initialReceipts: any[] }) {
  const router = useRouter();
  const [receipts, setReceipts] = useState<any[]>(initialReceipts);
  const [batchStatus, setBatchStatus] = useState<any>(null);
  const [processing, setProcessing] = useState(false);
  const [pollInterval, setPollInterval] = useState<NodeJS.Timeout | null>(null);

  const startProcessing = async () => {
    try {
      setProcessing(true);
      await fetchApi('/receipts/bulk-extract', {
        method: 'POST',
        body: JSON.stringify({ batch_id: batchId })
      });
      toast.success('Batch extraction started');
      pollBatchStatus();
    } catch (err: any) {
      toast.error('Failed to start extraction', { description: err.message });
      setProcessing(false);
    }
  };

  const pollBatchStatus = () => {
    const interval = setInterval(async () => {
      try {
        const status = await fetchApi(`/receipts/batch/${batchId}`) as any;
        setBatchStatus(status);
        
        // Fetch individual receipts to update cards
        const batchReceipts = await fetchApi('/receipts?limit=100') as any;
        const updated = batchReceipts.items.filter((r: any) => r.id && receipts.some(ir => ir.id === r.id));
        if (updated.length > 0) {
            setReceipts(prev => prev.map(r => updated.find((ur: any) => ur.id === r.id) || r));
        }

        if (status.extracting === 0 && status.uploaded === 0) {
          clearInterval(interval);
          setProcessing(false);
          toast.success('Batch processing complete!');
        }
      } catch (err) {
        console.error('Polling error', err);
      }
    }, 5000);
    setPollInterval(interval);
  };

  useEffect(() => {
    return () => {
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [pollInterval]);

  const getStatusBadge = (status: string, index: number) => {
    switch (status) {
      case 'UPLOADED':
      case 'PENDING':
        return <span className="px-2 py-1 bg-white/10 text-white/50 border border-white/20 rounded font-sans text-[10px] uppercase tracking-wider font-bold" data-status="WAITING">Waiting...</span>;
      case 'EXTRACTING':
        return <span className="px-2 py-1 bg-primary/10 text-primary border border-primary/20 rounded font-sans text-[10px] uppercase tracking-wider font-bold flex items-center gap-1" data-status="EXTRACTING"><Loader2 size={10} className="animate-spin" /> Extracting</span>;
      case 'EXTRACTED':
      case 'REVIEWED':
        return <span className="px-2 py-1 bg-success/10 text-success border border-success/20 rounded font-sans text-[10px] uppercase tracking-wider font-bold" data-status="EXTRACTED">Extracted</span>;
      case 'EXTRACTION_FAILED':
        return <span className="px-2 py-1 bg-error/10 text-error border border-error/20 rounded font-sans text-[10px] uppercase tracking-wider font-bold" data-status="FAILED">Failed</span>;
      default:
        return <span className="px-2 py-1 bg-white/10 text-white border border-white/20 rounded font-sans text-[10px] uppercase tracking-wider font-bold">{status}</span>;
    }
  };

  const getExtractingIndex = () => {
    // Determine queue position
    const waitingOrExtracting = receipts.filter(r => r.status === 'UPLOADED' || r.status === 'EXTRACTING' || r.status === 'PENDING');
    const extractingIdx = waitingOrExtracting.findIndex(r => r.status === 'EXTRACTING');
    return extractingIdx >= 0 ? extractingIdx + 1 : 1;
  };

  return (
    <div className="w-full mt-8 animate-fade-in" data-testid="batch-queue">
      <div className="flex justify-between items-end mb-4">
        <div>
          <h3 className="font-heading text-2xl font-bold text-white mb-1">Batch Processing</h3>
          {batchStatus && (
            <p className="font-sans text-sm text-white/60">
              {batchStatus.extracted} of {batchStatus.total} receipts extracted
            </p>
          )}
        </div>
        {!processing && (!batchStatus || (batchStatus.extracting === 0 && batchStatus.uploaded > 0)) && (
          <button 
            onClick={startProcessing}
            data-testid="start-processing"
            className="px-6 py-2.5 rounded-full bg-gradient-to-r from-primary to-secondary text-background font-heading text-sm font-bold tracking-wide shadow-[0_0_15px_rgba(192,193,255,0.2)] hover:shadow-[0_0_25px_rgba(192,193,255,0.4)] transition-all"
          >
            Start Processing
          </button>
        )}
      </div>

      {batchStatus && batchStatus.total > 0 && (
         <div className="w-full bg-white/5 rounded-full h-2 mb-6 border border-white/10 overflow-hidden">
            <div 
              className="bg-primary h-full transition-all duration-500 ease-out"
              style={{ width: `${(batchStatus.extracted / batchStatus.total) * 100}%` }}
            ></div>
         </div>
      )}

      <div className="space-y-3">
        {receipts.map((receipt, index) => {
          const isFailed = receipt.status === 'EXTRACTION_FAILED';
          const isExtracting = receipt.status === 'EXTRACTING';
          
          return (
            <div key={receipt.id} className={`glass-panel p-4 rounded-xl flex items-center justify-between border ${isFailed ? 'border-error/30 bg-error/5' : 'border-white/10'}`}>
              <div className="flex items-center gap-4">
                <div className={`w-10 h-10 rounded bg-black/40 flex items-center justify-center border ${isFailed ? 'border-error/20 text-error' : 'border-white/10 text-white/40'}`}>
                  {isFailed ? <AlertCircle size={20} /> : <CheckCircle size={20} className={receipt.status === 'EXTRACTED' || receipt.status === 'REVIEWED' ? 'text-success' : 'text-white/20'} />}
                </div>
                <div>
                  <h4 className="font-sans text-sm font-medium text-white truncate max-w-[200px] sm:max-w-xs">{receipt.filename || receipt.original_filename}</h4>
                  {isExtracting && (
                    <p className="font-sans text-xs text-primary mt-1">
                      Processing receipt... Queue position: {getExtractingIndex()}
                    </p>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-4">
                {getStatusBadge(receipt.status, index)}
                
                {(receipt.status === 'EXTRACTED' || receipt.status === 'REVIEWED') && (
                  <button 
                    onClick={() => router.push(`/review/${receipt.id}`)}
                    className="text-tertiary hover:text-white transition-colors text-sm font-medium ml-2"
                  >
                    Review →
                  </button>
                )}

                {isFailed && (
                  <button 
                    onClick={() => router.push(`/review/${receipt.id}`)}
                    className="px-3 py-1.5 bg-error/20 text-error border border-error/30 rounded text-xs font-bold hover:bg-error/30 transition-colors"
                  >
                    Manual Entry
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
