'use client'

import { useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useDropzone } from 'react-dropzone'
import imageCompression from 'browser-image-compression'
import { UploadCloud, CheckCircle, AlertCircle, Loader2, Camera, Receipt, Cpu, X } from 'lucide-react'
import { fetchApi } from '@/utils/apiClient'
import { toast } from 'sonner'
import BulkQueue from '@/components/BulkQueue'

export default function UploadPage() {
  const router = useRouter()
  const [status, setStatus] = useState<"IDLE" | "COMPRESSING" | "UPLOADING" | "ERROR" | "QUEUE">("IDLE")
  const [errorMsg, setErrorMsg] = useState("")
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [batchData, setBatchData] = useState<{ batchId: string, receipts: any[] } | null>(null)

  const processSingleFile = async (file: File) => {
    // Fallback logic for exactly 1 file (Phase 1 legacy intact)
    try {
      setStatus('COMPRESSING')
      let fileToUpload = file

      if (file.type.startsWith('image/') && file.size > 5 * 1024 * 1024) {
        toast.info('Compressing large image...')
        const options = { maxSizeMB: 4.5, maxWidthOrHeight: 2400, useWebWorker: true, fileType: 'image/jpeg', initialQuality: 0.85 }
        fileToUpload = await imageCompression(file, options)
      }

      setStatus('UPLOADING')
      const formData = new FormData()
      formData.append('file', fileToUpload, file.name)
      
      const response = await fetchApi('/receipts/upload', { method: 'POST', body: formData })
      await fetchApi(`/receipts/${response.id}/extract`, { method: 'POST' })

      toast.success('Receipt uploaded successfully!')
      router.push(`/review/${response.id}`)

    } catch (err: any) {
      console.error('Upload error:', err)
      setErrorMsg(err.message || 'An unexpected error occurred during upload.')
      setStatus('ERROR')
      toast.error('Upload failed', { description: err.message })
    }
  }

  const handleUploadAll = async () => {
    if (selectedFiles.length === 0) return;
    if (selectedFiles.length === 1) {
      return processSingleFile(selectedFiles[0]);
    }

    try {
      setStatus('UPLOADING');
      const formData = new FormData();
      selectedFiles.forEach(file => {
         // Optionally compress here as well if needed, but omitted for simplicity in bulk
         formData.append('files', file, file.name);
      });

      const response = await fetchApi('/receipts/bulk-upload', {
        method: 'POST',
        body: formData
      });

      toast.success(`${response.total} receipts uploaded successfully!`);
      setBatchData({ batchId: response.batch_id, receipts: response.receipts });
      setStatus('QUEUE');

    } catch (err: any) {
      console.error('Bulk upload error:', err);
      setErrorMsg(err.message || 'Bulk upload failed.');
      setStatus('ERROR');
      toast.error('Bulk upload failed', { description: err.message });
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const onDrop = useCallback((acceptedFiles: File[]) => {
    // Filter large files
    const valid = acceptedFiles.filter(f => {
       if (f.size > 20 * 1024 * 1024) {
           toast.error(`File ${f.name} too large`, { description: 'Maximum file size is 20MB.' });
           return false;
       }
       return true;
    });

    if (valid.length > 0) {
      setSelectedFiles(prev => {
         const combined = [...prev, ...valid];
         return combined.slice(0, 20); // enforce max 20
      });
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'image/heic': ['.heic'],
      'application/pdf': ['.pdf']
    },
    maxFiles: 20,
    disabled: status === 'UPLOADING' || status === 'COMPRESSING'
  })

  return (
    <div className="flex-1 w-full max-w-5xl mx-auto flex flex-col min-h-full p-6 md:p-12 animate-fade-in">
      <div className="flex flex-col h-full gap-6">
        
        {/* Header Section */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-4">
          <div>
            <h2 className="font-heading text-3xl md:text-4xl font-bold text-white mb-2 tracking-tight">Upload Receipt</h2>
            <p className="font-sans text-white/60">Drag and drop documents or take a new photo to log expenses.</p>
          </div>
          <div className="mt-4 md:mt-0 glass-panel px-5 py-2.5 rounded-full flex items-center gap-3 border border-white/10 shadow-[0_4px_20px_rgba(0,0,0,0.3)]">
            <Receipt className="text-tertiary w-4 h-4" />
            <span className="font-mono text-white text-sm font-medium" data-testid="file-count">
              {selectedFiles.length} of 20 <span className="text-white/50 text-xs ml-1 font-sans font-normal">files</span>
            </span>
          </div>
        </div>

        {status === 'QUEUE' && batchData ? (
          <BulkQueue batchId={batchData.batchId} initialReceipts={batchData.receipts} />
        ) : (
        <>
        {/* Central Drag and Drop Zone */}
        <div 
          {...getRootProps()}
          className={`w-full min-h-[350px] glass-panel-active rounded-2xl flex flex-col items-center justify-center p-8 relative overflow-hidden group border-dashed border transition-all duration-300 cursor-pointer
            ${isDragActive ? 'border-primary bg-primary/10 scale-[1.02] shadow-[0_0_50px_rgba(192,193,255,0.2)]' : 'border-primary/30 hover:border-primary/60'}`}
        >
          <input {...getInputProps()} capture="environment" />
          <div className="absolute inset-0 bg-gradient-to-b from-primary/0 to-primary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
          
          <div className="relative z-10 flex flex-col items-center text-center w-full">
            {status === 'IDLE' && selectedFiles.length === 0 && (
              <div className="flex flex-col items-center animate-fade-in pointer-events-none">
                <div className="w-20 h-20 rounded-full bg-white/5 border border-white/10 flex items-center justify-center mb-6 shadow-[0_0_30px_rgba(192,193,255,0.1)] group-hover:shadow-[0_0_50px_rgba(192,193,255,0.25)] transition-all duration-300 group-hover:scale-105">
                  <UploadCloud size={40} className="text-primary" />
                </div>
                <h3 className="font-heading text-2xl font-bold text-white mb-2">Drop files here</h3>
                <p className="font-sans text-white/60 max-w-md mb-8 leading-relaxed text-sm">
                  Supports PDF, JPG, PNG up to 20MB. Upload up to 20 receipts at once.
                </p>
                <div className="flex flex-col sm:flex-row items-center gap-4 pointer-events-auto">
                  <button className="px-6 py-3 rounded-full bg-gradient-to-r from-primary to-secondary text-background font-heading text-sm font-bold tracking-wide shadow-[0_0_20px_rgba(192,193,255,0.3)] hover:shadow-[0_0_30px_rgba(192,193,255,0.5)] transition-all transform hover:scale-105 active:scale-95 flex items-center gap-2">
                    <Camera size={18} />
                    Take Photo
                  </button>
                  <button className="px-6 py-3 rounded-full border border-white/20 text-white font-sans text-sm font-medium hover:bg-white/10 transition-colors">
                    Browse Files
                  </button>
                </div>
              </div>
            )}

            {status === 'IDLE' && selectedFiles.length > 0 && (
              <div className="flex flex-col w-full max-w-2xl animate-fade-in pointer-events-auto" onClick={e => e.stopPropagation()}>
                <div className="flex justify-between items-center mb-4 w-full">
                    <h3 className="font-heading text-xl font-bold text-white">Selected Files</h3>
                    <button 
                      data-testid="upload-all"
                      onClick={handleUploadAll}
                      className="px-6 py-2.5 rounded-full bg-gradient-to-r from-primary to-secondary text-background font-heading text-sm font-bold tracking-wide shadow-[0_0_15px_rgba(192,193,255,0.2)] hover:shadow-[0_0_25px_rgba(192,193,255,0.4)] transition-all"
                    >
                      Upload All
                    </button>
                </div>
                <div className="space-y-2 w-full max-h-[300px] overflow-y-auto pr-2">
                  {selectedFiles.map((f, i) => (
                    <div key={i} className="flex justify-between items-center glass-panel p-3 rounded-lg border border-white/10">
                      <span className="text-white text-sm font-sans truncate pr-4">{f.name}</span>
                      <button onClick={(e) => { e.stopPropagation(); removeFile(i); }} className="text-white/40 hover:text-error transition-colors p-1">
                        <X size={16} />
                      </button>
                    </div>
                  ))}
                </div>
                {selectedFiles.length < 20 && (
                  <p className="mt-4 text-white/50 text-sm font-sans">
                    You can drop {20 - selectedFiles.length} more files here.
                  </p>
                )}
              </div>
            )}

            {status === 'COMPRESSING' && (
              <div className="flex flex-col items-center animate-fade-in pointer-events-none">
                <div className="w-20 h-20 rounded-full border-4 border-t-primary border-primary/20 animate-spin mb-6"></div>
                <h3 className="font-heading text-xl font-bold text-primary mb-2">Optimizing Image...</h3>
                <p className="font-sans text-white/60 text-sm">Compressing large file for faster processing.</p>
              </div>
            )}

            {status === 'UPLOADING' && (
              <div className="flex flex-col items-center animate-fade-in pointer-events-none">
                <div className="relative w-24 h-24 mb-6">
                  <svg className="w-full h-full -rotate-90 animate-spin-slow" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="6" className="text-white/10" />
                    <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="6" strokeDasharray="283" strokeDashoffset="75" className="text-primary drop-shadow-[0_0_12px_rgba(192,193,255,0.6)]" strokeLinecap="round" />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Loader2 size={32} className="text-primary animate-spin" />
                  </div>
                </div>
                <h3 className="font-heading text-xl font-bold text-primary mb-2">Securely Uploading...</h3>
                <p className="font-sans text-white/60 text-sm">Encrypting and transferring to secure storage.</p>
              </div>
            )}

            {status === 'ERROR' && (
              <div className="flex flex-col items-center animate-fade-in pointer-events-none">
                <div className="w-20 h-20 rounded-full bg-error-container/30 flex items-center justify-center mb-6 border border-error/30 shadow-[0_0_30px_rgba(255,180,171,0.2)]">
                  <AlertCircle size={40} className="text-error" />
                </div>
                <h3 className="font-heading text-xl font-bold text-error mb-2">Upload Failed</h3>
                <p className="font-sans text-white/80 mb-6 max-w-md text-sm">{errorMsg}</p>
                <button 
                  className="px-8 py-2.5 bg-transparent border border-white/20 rounded-full hover:bg-white/10 font-sans text-sm font-medium transition-colors pointer-events-auto text-white"
                  onClick={(e) => { e.stopPropagation(); setStatus('IDLE') }}
                >
                  Try Again
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Feature Highlights */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
          <div className="glass-panel p-6 rounded-2xl flex items-start gap-4 hover:bg-white/5 transition-colors cursor-default border border-white/5">
            <div className="p-3 rounded-lg bg-success/20 text-success border border-success/30 shadow-inner">
              <CheckCircle size={24} />
            </div>
            <div>
              <h4 className="font-heading text-lg font-bold text-white mb-1">100% Balanced Ledger</h4>
              <p className="font-sans text-sm text-white/50 leading-relaxed">
                Every uploaded receipt is cross-referenced with your connected accounts to ensure perfect synchronization.
              </p>
            </div>
          </div>
          
          <div className="glass-panel p-6 rounded-2xl flex items-start gap-4 hover:bg-white/5 transition-colors cursor-default border border-white/5">
            <div className="p-3 rounded-lg bg-tertiary/10 text-tertiary border border-tertiary/20 shadow-inner">
              <Cpu size={24} />
            </div>
            <div>
              <h4 className="font-heading text-lg font-bold text-white mb-1">Automated AI Extraction</h4>
              <p className="font-sans text-sm text-white/50 leading-relaxed">
                Our Atmospheric Intelligence models instantly parse line items, tax, and totals with 99.9% accuracy.
              </p>
            </div>
          </div>
        </div>
        </>
        )}
      </div>
    </div>
  )
}
