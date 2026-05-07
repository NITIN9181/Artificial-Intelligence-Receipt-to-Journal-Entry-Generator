'use client'

import React, { useState, useEffect } from 'react'
import { apiClient, ApiError } from '@/lib/api-client'
import { toast } from 'sonner'
import { Search, Filter, ChevronDown, ChevronRight, FileText, FileDown, Receipt as ReceiptIcon } from 'lucide-react'

type JournalEntry = {
  id: string;
  entry_number: string;
  transaction_date: string;
  vendor_name: string;
  category: string;
  total_amount: number;
  status: string;
  line_items: Array<{ description: string; quantity: number; unit_price: number; line_total: number }>;
}

type ReceiptApiItem = {
  id: string
  status: string
  created_at: string
  extracted_data?: {
    date?: string
    vendor_name?: string
    expense_category?: string
    total_amount?: number
    line_items?: Array<{
      description?: string
      quantity?: number
      unit_price?: number
      line_total?: number
    }>
  }
}

export default function JournalEntriesPage() {
  const [entries, setEntries] = useState<JournalEntry[]>([])
  const [loading, setLoading] = useState(true)
  
  // Pagination & Filtering
  const [vendorSearch, setVendorSearch] = useState('')
  const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({})

  const loadEntries = async () => {
    setLoading(true)
    try {
      const data = await apiClient('/receipts')
      const formatted = (data.items || []).map((item: ReceiptApiItem) => {
        const ext = item.extracted_data || {}
        return {
          id: item.id,
          entry_number: `JE-${new Date(item.created_at).getFullYear()}-${item.id.substring(0, 5)}`,
          transaction_date: ext.date || (item.created_at ? item.created_at.split('T')[0] : ''),
          vendor_name: ext.vendor_name || 'Unknown Vendor',
          category: ext.expense_category || 'Operating Expense',
          total_amount: ext.total_amount || 0,
          status: item.status,
          line_items: (ext.line_items || []).map((li) => ({
            description: li.description,
            quantity: li.quantity || 1,
            unit_price: li.unit_price || 0,
            line_total: li.line_total || 0,
          })),
        }
      })
      
      // Filter locally
      const filtered = vendorSearch 
        ? formatted.filter((f) => f.vendor_name.toLowerCase().includes(vendorSearch.toLowerCase()))
        : formatted;
        
      setEntries(filtered)
    } catch (err) {
      const message =
        err instanceof ApiError
          ? ((err.body as { error?: string })?.error ?? err.message)
          : 'Failed to load journal entries'
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const timer = setTimeout(() => {
      void loadEntries()
    }, 0)
    return () => clearTimeout(timer)
  }, [vendorSearch])

  const toggleRow = (id: string) => {
    setExpandedRows(prev => ({...prev, [id]: !prev[id]}))
  }

  const getStatusBadge = (status: string) => {
    switch(status) {
      case 'POSTED': return <span className="px-2 py-1 bg-success/10 text-success border border-success/20 rounded font-sans text-[10px] uppercase tracking-wider font-bold">Posted</span>
      case 'REVIEWED': return <span className="px-2 py-1 bg-tertiary/10 text-tertiary border border-tertiary/20 rounded font-sans text-[10px] uppercase tracking-wider font-bold">Reviewed</span>
      case 'PENDING': 
      case 'EXTRACTING': return <span className="px-2 py-1 bg-white/5 text-foreground/70 border border-white/10 rounded font-sans text-[10px] uppercase tracking-wider font-bold">Pending</span>
      case 'REJECTED': return <span className="px-2 py-1 bg-error/10 text-error border border-error/20 rounded font-sans text-[10px] uppercase tracking-wider font-bold">Rejected</span>
      case 'QUARANTINED': return <span className="px-2 py-1 bg-warning/10 text-warning border border-warning/20 rounded font-sans text-[10px] uppercase tracking-wider font-bold">Quarantined</span>
      default: return <span className="px-2 py-1 bg-primary/10 text-primary border border-primary/20 rounded font-sans text-[10px] uppercase tracking-wider font-bold">{status}</span>
    }
  }

  const handleExport = async (format: 'csv' | 'pdf') => {
    try {
      const { createClient } = await import('@/utils/supabase/client');
      const supabase = createClient();
      const { data } = await supabase.auth.getSession();
      const token = data.session?.access_token;

      const baseUrl = process.env.NEXT_PUBLIC_FASTAPI_BASE_URL || 'http://localhost:8000';
      const url = new URL(`${baseUrl}/api/v1/journal-entries/export/${format}`);
      if (vendorSearch) url.searchParams.append('vendor', vendorSearch);

      const response = await fetch(url.toString(), {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Export failed');

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `journal_ledger.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(downloadUrl);
      document.body.removeChild(a);
      toast.success(`${format.toUpperCase()} exported successfully`);
    } catch {
      toast.error(`Failed to export ${format}`);
    }
  }

  return (
    <div className="flex-1 w-full max-w-[1400px] mx-auto p-4 md:p-6 lg:p-8 animate-fade-in pb-32">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-8 gap-4">
        <div>
          <h1 className="font-heading text-2xl md:text-3xl font-bold text-white tracking-tight">Journal Entries</h1>
          <p className="font-sans text-foreground/60 mt-1">Review, filter, and export the unified ledger.</p>
        </div>
        
        <div className="flex gap-3">
          <button onClick={() => handleExport('csv')} className="px-4 py-2 rounded-xl border border-white/10 hover:bg-white/5 transition-colors font-sans text-sm font-medium text-white flex items-center gap-2">
            <FileDown size={16} /> Export CSV
          </button>
          <button onClick={() => handleExport('pdf')} className="px-4 py-2 rounded-xl border border-white/10 hover:bg-white/5 transition-colors font-sans text-sm font-medium text-white flex items-center gap-2">
            <FileText size={16} /> Export PDF
          </button>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="glass-panel p-4 rounded-2xl mb-6 flex flex-wrap gap-4 items-center">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-foreground/40" />
          <input 
            type="text" 
            placeholder="Search vendor..."
            value={vendorSearch}
            onChange={(e) => setVendorSearch(e.target.value)}
            className="w-full bg-black/20 border border-white/10 rounded-xl pl-9 pr-4 py-2.5 text-white font-sans text-sm focus:border-primary focus:outline-none transition-colors"
          />
        </div>
        
        <div className="flex gap-4">
          <button className="px-4 py-2.5 bg-black/20 border border-white/10 rounded-xl flex items-center gap-2 text-white font-sans text-sm hover:border-white/20 transition-colors">
            <Filter size={16} className="text-primary" /> Filter
          </button>
          <input 
            type="date"
            className="px-4 py-2.5 bg-black/20 border border-white/10 rounded-xl text-white font-sans text-sm hover:border-white/20 transition-colors focus:border-primary focus:outline-none [color-scheme:dark]"
          />
        </div>
      </div>

      {/* Data Table */}
      <div className="glass-panel rounded-2xl overflow-hidden border border-white/5">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/10 bg-white/5">
                <th className="px-6 py-4 font-mono text-[10px] uppercase tracking-widest text-foreground/50 w-10"></th>
                <th className="px-6 py-4 font-mono text-[10px] uppercase tracking-widest text-foreground/50">Entry Number</th>
                <th className="px-6 py-4 font-mono text-[10px] uppercase tracking-widest text-foreground/50">Date</th>
                <th className="px-6 py-4 font-mono text-[10px] uppercase tracking-widest text-foreground/50">Vendor</th>
                <th className="px-6 py-4 font-mono text-[10px] uppercase tracking-widest text-foreground/50">Category</th>
                <th className="px-6 py-4 font-mono text-[10px] uppercase tracking-widest text-foreground/50 text-right">Amount</th>
                <th className="px-6 py-4 font-mono text-[10px] uppercase tracking-widest text-foreground/50 text-center">Status</th>
                <th className="px-6 py-4 font-mono text-[10px] uppercase tracking-widest text-foreground/50 text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-foreground/50">
                    <div className="flex flex-col items-center gap-3">
                      <div className="animate-spin w-8 h-8 border-2 border-t-primary border-primary/20 rounded-full"></div>
                      <span className="font-sans text-sm">Loading ledger data...</span>
                    </div>
                  </td>
                </tr>
              ) : entries.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-foreground/50 font-sans text-sm">
                    No journal entries found matching criteria.
                  </td>
                </tr>
              ) : (
                entries.map((entry) => (
                  <React.Fragment key={entry.id}>
                    {/* Main Row */}
                    <tr 
                      className={`border-b border-white/5 hover:bg-white/5 transition-colors cursor-pointer ${expandedRows[entry.id] ? 'bg-white/[0.02]' : ''}`}
                      onClick={() => toggleRow(entry.id)}
                    >
                      <td className="px-6 py-4 text-white/40">
                        {expandedRows[entry.id] ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                      </td>
                      <td className="px-6 py-4 font-mono text-sm text-primary">{entry.entry_number}</td>
                      <td className="px-6 py-4 font-sans text-sm text-foreground/80">{entry.transaction_date}</td>
                      <td className="px-6 py-4 font-sans text-sm font-medium text-white">{entry.vendor_name}</td>
                      <td className="px-6 py-4 font-sans text-sm text-foreground/80">{entry.category}</td>
                      <td className="px-6 py-4 font-mono text-sm text-white text-right font-bold">${(Number(entry.total_amount) || 0).toFixed(2)}</td>
                      <td className="px-6 py-4 text-center">{getStatusBadge(entry.status)}</td>
                      <td className="px-6 py-4 text-center">
                        <button className="text-tertiary hover:text-white transition-colors" onClick={(e) => { e.stopPropagation(); window.location.href = `/review/${entry.id}` }}>
                          <ReceiptIcon size={16} className="inline" />
                        </button>
                      </td>
                    </tr>
                    
                    {/* Expanded Row (Line Items Preview) */}
                    {expandedRows[entry.id] && (
                      <tr className="bg-black/40 border-b border-white/10">
                        <td colSpan={8} className="px-12 py-6">
                          <div className="glass-panel p-4 rounded-xl border border-white/5">
                            <h4 className="font-mono text-[10px] uppercase tracking-widest text-foreground/50 mb-3 border-b border-white/10 pb-2">Extracted Line Items</h4>
                            {entry.line_items && entry.line_items.length > 0 ? (
                              <div className="space-y-2">
                                {entry.line_items.map((item, idx) => (
                                  <div key={idx} className="flex justify-between font-mono text-xs text-white/80">
                                    <span className="truncate pr-4">{item.quantity > 1 ? `${item.quantity}x ` : ''}{item.description}</span>
                                    <span>${(Number(item.line_total) || 0).toFixed(2)}</span>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <p className="font-sans text-xs text-foreground/40 italic">No line items recorded.</p>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        <div className="p-4 border-t border-white/5 flex justify-between items-center bg-white/5">
          <span className="font-sans text-xs text-foreground/50">Showing 1 to {entries.length} of {entries.length} entries</span>
          <div className="flex gap-2">
            <button className="px-3 py-1.5 rounded-lg border border-white/10 text-white/40 font-sans text-xs hover:bg-white/5 disabled:opacity-50" disabled>Previous</button>
            <button className="px-3 py-1.5 rounded-lg bg-primary/20 border border-primary/30 text-primary font-sans text-xs">1</button>
            <button className="px-3 py-1.5 rounded-lg border border-white/10 text-white font-sans text-xs hover:bg-white/5">Next</button>
          </div>
        </div>
      </div>

    </div>
  )
}
