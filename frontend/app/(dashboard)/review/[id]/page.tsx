'use client'

import { useState, useEffect, useMemo, use } from 'react'
import { useRouter } from 'next/navigation'
import { apiClient, ApiError } from '@/lib/api-client'
import { toast } from 'sonner'
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch'
import { CheckCircle, AlertTriangle, RefreshCw, ZoomIn, ZoomOut, Maximize, AlertCircle, Save, Cpu } from 'lucide-react'

// --- Types ---
type LineItem = {
  description: string;
  quantity: number;
  unit_price: number;
  line_total: number;
  category?: string;
}

type ReceiptData = {
  id: string;
  status: 'UPLOADED' | 'PENDING' | 'EXTRACTING' | 'EXTRACTED' | 'REVIEWED' | 'POSTED' | 'REJECTED' | 'QUARANTINED' | 'VALIDATION_FAILED' | 'EXTRACTION_FAILED';
  extraction_error?: string | null;
  image_url?: string;
  vendor_name: string | null;
  transaction_date: string | null;
  currency: string;
  subtotal: number | null;
  tax_amount: number | null;
  tip_amount: number | null;
  total_amount: number | null;
  line_items: LineItem[];
  confidence_scores?: {
    vendor_name: number;
    transaction_date: number;
    amounts: number;
  };
}

export default function ReviewPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)
  const router = useRouter()
  const [receipt, setReceipt] = useState<ReceiptData | null>(null)
  const [loading, setLoading] = useState(true)
  const [polling, setPolling] = useState(false)
  
  // Editable form state
  const [formData, setFormData] = useState({
    vendor_name: '',
    transaction_date: '',
    currency: 'USD',
    subtotal: 0,
    tax_amount: 0,
    tip_amount: 0,
    total_amount: 0,
  })
  
  const [lineItems, setLineItems] = useState<LineItem[]>([])

  const loadReceipt = async () => {
    try {
      const data = await apiClient(`/receipts/${resolvedParams.id}`) as any
      setReceipt(data)
      
      if (data.status === 'EXTRACTING' || data.status === 'PENDING') {
        setPolling(true)
      } else {
        setPolling(false)
        const ext = data.extracted_data || {}
        setFormData({
          vendor_name: ext.vendor_name || '',
          transaction_date: ext.date || '',
          currency: ext.currency || 'USD',
          subtotal: ext.subtotal || 0,
          tax_amount: ext.tax_amount || 0,
          tip_amount: ext.tip_amount || 0,
          total_amount: ext.total_amount || 0,
        })
        setLineItems(ext.line_items || [])
      }
    } catch (err) {
      const message =
        err instanceof ApiError
          ? ((err.body as { error?: string })?.error ?? err.message)
          : 'Failed to load receipt'
      toast.error('Failed to load receipt', { description: message })
      setPolling(false)
    } finally {
      setLoading(false)
    }
  }

  // Poll every 5s if extracting
  useEffect(() => {
    const timer = setTimeout(() => {
      void loadReceipt()
    }, 0)
    
    let interval: NodeJS.Timeout
    if (polling) {
      interval = setInterval(() => {
        void loadReceipt()
      }, 5000)
    }
    
    return () => {
      clearTimeout(timer)
      clearInterval(interval)
    }
  }, [polling, resolvedParams.id])

  // Math Validation (Debits vs Credits)
  const validation = useMemo(() => {
    const calcSubtotal = lineItems.reduce((acc, item) => acc + (Number(item.line_total) || 0), 0)
    const tax = Number(formData.tax_amount) || 0
    const tip = Number(formData.tip_amount) || 0
    const total = Number(formData.total_amount) || 0
    
    const diffExclusive = Math.abs(calcSubtotal + tax + tip - total)
    const diffInclusive = Math.abs(calcSubtotal + tip - total)
    
    const diff = Math.min(diffExclusive, diffInclusive)
    const isBalanced = diff < 0.05
    
    const calcTotal = diffExclusive < diffInclusive ? calcSubtotal + tax + tip : calcSubtotal + tip

    return {
      calcSubtotal,
      calcTotal,
      isBalanced,
      diff
    }
  }, [formData, lineItems])

  const handleSave = async (post: boolean = false) => {
    try {
      // Send corrections to the backend
      const correctionPayload = {
        vendor_name: formData.vendor_name || undefined,
        date: formData.transaction_date || undefined,
        currency: formData.currency || undefined,
        subtotal: formData.subtotal || undefined,
        tax_amount: formData.tax_amount || undefined,
        tip_amount: formData.tip_amount || undefined,
        total_amount: formData.total_amount || undefined,
        line_items: lineItems.map(li => ({
          description: li.description,
          quantity: li.quantity || 1,
          unit_price: li.unit_price || li.line_total,
          line_total: li.line_total,
        })),
      }

      await apiClient(`/receipts/${resolvedParams.id}/correct`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(correctionPayload),
      })

      if (post) {
        // Journalize the receipt
        await apiClient(`/receipts/${resolvedParams.id}/journalize`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({}),
        })
        toast.success("Receipt Approved & Posted to Ledger!")
        router.push('/journal-entries')
      } else {
        toast.success("Changes saved")
      }
    } catch (err) {
      const message =
        err instanceof ApiError
          ? ((err.body as { error?: string })?.error ?? err.message)
          : 'Save failed'
      toast.error("Save failed", { description: message })
    }
  }

  // Helper for confidence colors
  const getConfidenceClass = (score?: number) => {
    if (score === undefined) return 'border-transparent'
    if (score >= 0.8) return 'border-transparent'
    if (score >= 0.6) return 'border-l-warning'
    if (score >= 0.4) return 'border-l-orange-500'
    return 'border-l-error'
  }

  if (loading) {
    return <div className="flex-1 flex items-center justify-center min-h-[500px]">
      <div className="animate-spin w-12 h-12 border-4 border-t-primary border-primary/20 rounded-full"></div>
    </div>
  }

  if (polling) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-[500px] animate-fade-in">
        <div className="relative w-32 h-32 mb-8">
          <div className="absolute inset-0 rounded-full border-4 border-primary/20 border-t-primary animate-spin"></div>
          <div className="absolute inset-0 rounded-full border-4 border-secondary/20 border-b-secondary animate-spin-slow"></div>
          <div className="absolute inset-0 flex items-center justify-center">
            <Cpu className="w-10 h-10 text-primary animate-pulse" />
          </div>
        </div>
        <h2 className="font-heading text-3xl font-bold text-white mb-3">Atmospheric Extraction in Progress</h2>
        <p className="font-sans text-foreground/60 text-lg">Queue position: Analyzing...</p>
        <p className="font-sans text-foreground/40 mt-2 text-sm max-w-md text-center">
          Our Llama models are parsing the line items and ensuring cryptographic math balance. This typically takes 5-15 seconds.
        </p>
      </div>
    )
  }

  if (!receipt) return <div className="text-center mt-20 text-error">Receipt not found</div>

  return (
    <div className="flex-1 w-full max-w-[1400px] mx-auto p-4 md:p-6 lg:p-8 animate-fade-in pb-32">
      
      <div className="flex justify-between items-end mb-6">
        <div>
          <h1 className="font-heading text-2xl md:text-3xl font-bold text-white tracking-tight">Review Receipt</h1>
          <p className="font-sans text-foreground/60 mt-1">Verify extraction accuracy before posting to the ledger.</p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => handleSave(false)} className="px-5 py-2.5 rounded-xl border border-white/10 hover:bg-white/5 transition-colors font-sans text-sm font-medium text-white flex items-center gap-2">
            <Save size={16} /> Save Draft
          </button>
          <button 
            onClick={() => handleSave(true)}
            disabled={!validation.isBalanced}
            className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-primary to-secondary text-background font-heading text-sm font-bold shadow-[0_0_20px_rgba(192,193,255,0.3)] hover:shadow-[0_0_30px_rgba(192,193,255,0.5)] transition-all disabled:opacity-50 disabled:grayscale disabled:cursor-not-allowed flex items-center gap-2"
          >
            <CheckCircle size={18} /> Approve & Post
          </button>
        </div>
      </div>

      {(receipt.status === 'VALIDATION_FAILED' || receipt.status === 'EXTRACTION_FAILED') && (
        <div className="mb-6 p-4 bg-error-container/20 border border-error/50 rounded-xl flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-error mt-0.5 shrink-0" />
          <div>
            <h4 className="font-heading font-bold text-error">Extraction Error</h4>
            <p className="font-sans text-sm text-error/80 mt-1">{receipt.extraction_error || "The AI model encountered an error while parsing this receipt."}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-[calc(100vh-200px)] min-h-[700px]">
        
        {/* Left Panel - Image Viewer */}
        <div className="glass-panel rounded-2xl overflow-hidden flex flex-col relative">
          <div className="absolute top-4 right-4 z-10 flex gap-2">
            <button className="p-2 bg-background/80 backdrop-blur-md rounded-lg border border-white/10 hover:bg-white/10 transition-colors text-white tooltip-trigger">
              <RefreshCw size={18} />
            </button>
          </div>
          
          <TransformWrapper initialScale={1} minScale={0.5} maxScale={4} centerOnInit>
            {({ zoomIn, zoomOut, resetTransform }) => (
              <>
                <div className="absolute bottom-4 right-4 z-10 flex gap-2 bg-background/80 backdrop-blur-md rounded-xl border border-white/10 p-1 shadow-lg">
                  <button onClick={() => zoomOut()} className="p-2 hover:bg-white/10 rounded-lg text-white transition-colors"><ZoomOut size={18} /></button>
                  <button onClick={() => resetTransform()} className="p-2 hover:bg-white/10 rounded-lg text-white transition-colors"><Maximize size={18} /></button>
                  <button onClick={() => zoomIn()} className="p-2 hover:bg-white/10 rounded-lg text-white transition-colors"><ZoomIn size={18} /></button>
                </div>
                <TransformComponent wrapperClass="!w-full !h-full flex-1" contentClass="!w-full !h-full flex items-center justify-center">
                  {receipt.image_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={receipt.image_url} alt="Receipt" className="max-w-full max-h-full object-contain" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-foreground/40 font-mono text-sm bg-black/20">
                      [ No Image Available ]
                    </div>
                  )}
                </TransformComponent>
              </>
            )}
          </TransformWrapper>
        </div>

        {/* Right Panel - Editable Form */}
        <div className="flex flex-col gap-6 overflow-y-auto pr-2 custom-scrollbar">
          
          {/* Header Data */}
          <div className="glass-panel p-6 rounded-2xl space-y-4">
            <h3 className="font-heading text-lg font-bold text-white border-b border-white/10 pb-2 mb-4">Header Data</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className={`pl-3 ${getConfidenceClass(receipt.confidence_scores?.vendor_name)}`}>
                <label className="block font-mono text-[10px] uppercase tracking-widest text-foreground/60 mb-1">Vendor Name</label>
                <input 
                  type="text" 
                  value={formData.vendor_name} 
                  onChange={(e) => setFormData({...formData, vendor_name: e.target.value})}
                  className="w-full bg-transparent border-b border-white/20 focus:border-primary focus:outline-none py-1 text-white font-sans text-sm transition-colors"
                />
              </div>
              <div className={`pl-3 ${getConfidenceClass(receipt.confidence_scores?.transaction_date)}`}>
                <label className="block font-mono text-[10px] uppercase tracking-widest text-foreground/60 mb-1">Date</label>
                <input 
                  type="date" 
                  value={formData.transaction_date} 
                  onChange={(e) => setFormData({...formData, transaction_date: e.target.value})}
                  className="w-full bg-transparent border-b border-white/20 focus:border-primary focus:outline-none py-1 text-white font-sans text-sm transition-colors [color-scheme:dark]"
                />
              </div>
            </div>
          </div>

          {/* Line Items */}
          <div className="glass-panel p-6 rounded-2xl">
            <div className="flex justify-between items-center border-b border-white/10 pb-2 mb-4">
              <h3 className="font-heading text-lg font-bold text-white">Line Items</h3>
              <button 
                onClick={() => setLineItems([...lineItems, { description: '', quantity: 1, unit_price: 0, line_total: 0 }])}
                className="text-primary text-sm font-sans hover:text-primary/80 transition-colors"
              >
                + Add Item
              </button>
            </div>
            
            <div className="space-y-3">
              {lineItems.map((item, idx) => (
                <div key={idx} className="flex gap-3 items-end">
                  <div className="flex-1 relative">
                    {item.quantity > 1 && (
                      <span className="absolute left-3 top-2.5 text-foreground/50 font-mono text-xs">{item.quantity}x</span>
                    )}
                    <input 
                      type="text" 
                      value={item.description}
                      placeholder="Item description"
                      onChange={(e) => {
                        const newItems = [...lineItems];
                        newItems[idx].description = e.target.value;
                        setLineItems(newItems);
                      }}
                      className={`w-full bg-black/20 border border-white/10 rounded-lg py-2 text-white font-sans text-sm focus:border-primary focus:outline-none transition-colors ${item.quantity > 1 ? 'pl-9 pr-3' : 'px-3'}`}
                    />
                  </div>
                  <div className="w-32 relative">
                    <span className="absolute left-3 top-2 text-foreground/40 font-mono text-sm">$</span>
                    <input 
                      type="number" 
                      value={item.line_total || ''}
                      onChange={(e) => {
                        const newItems = [...lineItems];
                        newItems[idx].line_total = parseFloat(e.target.value) || 0;
                        setLineItems(newItems);
                      }}
                      className="w-full bg-black/20 border border-white/10 rounded-lg pl-7 pr-3 py-2 text-white font-mono text-sm focus:border-primary focus:outline-none transition-colors"
                    />
                  </div>
                  <button 
                    onClick={() => setLineItems(lineItems.filter((_, i) => i !== idx))}
                    className="p-2 text-foreground/40 hover:text-error transition-colors mb-0.5"
                  >
                    ×
                  </button>
                </div>
              ))}
              {lineItems.length === 0 && (
                <div className="text-center py-6 text-foreground/40 font-sans text-sm border border-dashed border-white/10 rounded-xl">
                  No line items extracted.
                </div>
              )}
            </div>
          </div>

          {/* Amounts & Math */}
          <div className="glass-panel p-6 rounded-2xl">
            <h3 className="font-heading text-lg font-bold text-white border-b border-white/10 pb-2 mb-4">Totals</h3>
            
            <div className={`space-y-4 pl-3 ${getConfidenceClass(receipt.confidence_scores?.amounts)}`}>
              <div className="flex justify-between items-center text-sm">
                <span className="font-sans text-foreground/70">Calculated Subtotal</span>
                <span className="font-mono text-white">${validation.calcSubtotal.toFixed(2)}</span>
              </div>
              
              <div className="flex gap-4">
                <div className="flex-1">
                  <label className="block font-mono text-[10px] uppercase tracking-widest text-foreground/60 mb-1">Tax</label>
                  <div className="relative">
                    <span className="absolute left-0 top-1 text-foreground/40 font-mono text-sm">$</span>
                    <input 
                      type="number" 
                      value={formData.tax_amount || ''} 
                      onChange={(e) => setFormData({...formData, tax_amount: parseFloat(e.target.value) || 0})}
                      className="w-full bg-transparent border-b border-white/20 focus:border-primary focus:outline-none py-1 pl-4 text-white font-mono text-sm transition-colors"
                    />
                  </div>
                </div>
                <div className="flex-1">
                  <label className="block font-mono text-[10px] uppercase tracking-widest text-foreground/60 mb-1">Tip</label>
                  <div className="relative">
                    <span className="absolute left-0 top-1 text-foreground/40 font-mono text-sm">$</span>
                    <input 
                      type="number" 
                      value={formData.tip_amount || ''} 
                      onChange={(e) => setFormData({...formData, tip_amount: parseFloat(e.target.value) || 0})}
                      className="w-full bg-transparent border-b border-white/20 focus:border-primary focus:outline-none py-1 pl-4 text-white font-mono text-sm transition-colors"
                    />
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-white/5 flex justify-between items-center">
                <span className="font-sans font-medium text-white">Receipt Total</span>
                <div className="relative w-32">
                    <span className="absolute left-0 top-1 text-foreground/40 font-mono text-lg">$</span>
                    <input 
                      type="number" 
                      value={formData.total_amount || ''} 
                      onChange={(e) => setFormData({...formData, total_amount: parseFloat(e.target.value) || 0})}
                      className="w-full bg-transparent border-b-2 border-white/40 focus:border-primary focus:outline-none py-1 pl-5 text-white font-mono text-lg font-bold transition-colors"
                    />
                  </div>
              </div>
            </div>
          </div>

          {/* T-Account Preview */}
          <div className={`glass-panel rounded-2xl overflow-hidden border ${validation.isBalanced ? 'border-success/30' : 'border-error/50 shadow-[0_0_20px_rgba(239,68,68,0.2)]'} transition-all duration-500`}>
            <div className={`p-4 ${validation.isBalanced ? 'bg-success/10' : 'bg-error-container/40'} border-b border-white/5 flex items-center justify-between`}>
              <div className="flex items-center gap-2">
                {validation.isBalanced ? <CheckCircle className="text-success w-5 h-5" /> : <AlertTriangle className="text-error w-5 h-5 animate-pulse" />}
                <h3 className={`font-heading text-sm font-bold ${validation.isBalanced ? 'text-success' : 'text-error'}`}>
                  {validation.isBalanced ? 'Ledger Balanced' : 'Ledger Imbalance Detected'}
                </h3>
              </div>
              {!validation.isBalanced && (
                <span className="font-mono text-xs text-error font-bold">Diff: ${validation.diff.toFixed(2)}</span>
              )}
            </div>
            
            <div className="p-6 bg-black/40">
              <div className="grid grid-cols-2 gap-6 relative">
                <div className="absolute left-1/2 top-0 bottom-0 w-px bg-white/10 -translate-x-1/2"></div>
                
                {/* Debits */}
                <div>
                  <h4 className="font-mono text-[10px] text-foreground/50 uppercase tracking-widest text-center border-b border-white/10 pb-2 mb-3">Debits (Expenses)</h4>
                  <div className="space-y-2">
                    {lineItems.map((item, i) => (
                      <div key={i} className="flex justify-between font-mono text-xs text-white/80">
                        <span className="truncate pr-2">{item.quantity > 1 ? `${item.quantity}x ` : ''}{item.description || 'Item'}</span>
                        <span>${(Number(item.line_total) || 0).toFixed(2)}</span>
                      </div>
                    ))}
                    {(formData.tax_amount || 0) > 0 && (
                      <div className="flex justify-between font-mono text-xs text-white/80">
                        <span>Tax</span>
                        <span>${(Number(formData.tax_amount) || 0).toFixed(2)}</span>
                      </div>
                    )}
                    {(formData.tip_amount || 0) > 0 && (
                      <div className="flex justify-between font-mono text-xs text-white/80">
                        <span>Tip</span>
                        <span>${(Number(formData.tip_amount) || 0).toFixed(2)}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Credits */}
                <div>
                  <h4 className="font-mono text-[10px] text-foreground/50 uppercase tracking-widest text-center border-b border-white/10 pb-2 mb-3">Credits (Liabilities)</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between font-mono text-xs text-white/80">
                      <span className="truncate pr-2">Accounts Payable</span>
                      <span>${(Number(formData.total_amount) || 0).toFixed(2)}</span>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Math summary footer */}
              <div className="mt-6 pt-4 border-t border-white/20 flex justify-between font-mono text-sm font-bold">
                <span className="text-white">${validation.calcTotal.toFixed(2)}</span>
                <span className="text-white">${(Number(formData.total_amount) || 0).toFixed(2)}</span>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
