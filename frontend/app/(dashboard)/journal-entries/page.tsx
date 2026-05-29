'use client'

import React, { useState, useEffect } from 'react'
import { apiClient, ApiError, getBaseUrl } from '@/lib/api-client'
import { toast } from 'sonner'
import { Search, Filter, ChevronDown, ChevronRight, FileText, FileDown, Receipt as ReceiptIcon, MoreVertical } from 'lucide-react'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'

type JournalEntryLine = {
  id: string;
  account_code: string;
  account_name: string;
  debit: number;
  credit: number;
  description: string | null;
  line_order: number;
}

type JournalEntry = {
  id: string;
  receipt_id: string;
  entry_number: string;
  entry_date: string;
  reference: string | null;
  description: string | null;
  total_debit: number;
  total_credit: number;
  status: string;
  lines: JournalEntryLine[];
}

type JournalEntriesResponse = {
  data: JournalEntry[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    total_pages: number;
  };
}

export default function JournalEntriesPage() {
  const [entries, setEntries] = useState<JournalEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [pagination, setPagination] = useState({ page: 1, per_page: 25, total: 0, total_pages: 0 })

  // Filtering
  const [vendorSearch, setVendorSearch] = useState('')
  const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({})

  const loadEntries = async (page = 1) => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ page: String(page), per_page: '25' })
      if (vendorSearch) params.append('vendor', vendorSearch)

      const data = await apiClient<JournalEntriesResponse>(`/journal-entries?${params.toString()}`)
      setEntries(data.data || [])
      setPagination(data.pagination || { page: 1, per_page: 25, total: 0, total_pages: 0 })
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
      void loadEntries(1)
    }, 0)
    return () => clearTimeout(timer)
  }, [vendorSearch])

  const toggleRow = (id: string) => {
    setExpandedRows(prev => ({...prev, [id]: !prev[id]}))
  }

  const getStatusBadge = (status: string) => {
    switch(status) {
      case 'POSTED': return <span className="px-2 py-1 bg-success/10 text-success border border-success/20 rounded font-sans text-[10px] uppercase tracking-wider font-bold">Posted</span>
      case 'REVERSED': return <span className="px-2 py-1 bg-tertiary/10 text-tertiary border border-tertiary/20 rounded font-sans text-[10px] uppercase tracking-wider font-bold">Reversed</span>
      case 'DRAFT': return <span className="px-2 py-1 bg-white/5 text-foreground/70 border border-white/10 rounded font-sans text-[10px] uppercase tracking-wider font-bold">Draft</span>
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
      const baseUrl = getBaseUrl();
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

  const handleIndividualExport = async (id: string, format: 'xml' | 'csv' | 'sqlite', entryNumber: string) => {
    try {
      const { createClient } = await import('@/utils/supabase/client');
      const supabase = createClient();
      const { data } = await supabase.auth.getSession();
      const token = data.session?.access_token;
      const baseUrl = getBaseUrl();
      const url = new URL(`${baseUrl}/api/v1/gnucash/journal-entries/${id}/export?format=${format}`);

      const response = await fetch(url.toString(), {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Export failed');

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `JE_${entryNumber}.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);

      const formatName = format === 'xml' ? 'GnuCash XML' : format.toUpperCase();
      toast.success(`Exported ${entryNumber} to ${formatName}`);
    } catch {
      toast.error(`Failed to export ${entryNumber}`);
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
                <th className="px-6 py-4 font-mono text-[10px] uppercase tracking-widest text-foreground/50">Reference / Vendor</th>
                <th className="px-6 py-4 font-mono text-[10px] uppercase tracking-widest text-foreground/50 text-right">Debit</th>
                <th className="px-6 py-4 font-mono text-[10px] uppercase tracking-widest text-foreground/50 text-right">Credit</th>
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
                      <td className="px-6 py-4 font-sans text-sm text-foreground/80">{entry.entry_date}</td>
                      <td className="px-6 py-4 font-sans text-sm font-medium text-white">{entry.reference || entry.description || '—'}</td>
                      <td className="px-6 py-4 font-mono text-sm text-white text-right font-bold">${(Number(entry.total_debit) || 0).toFixed(2)}</td>
                      <td className="px-6 py-4 font-mono text-sm text-white text-right font-bold">${(Number(entry.total_credit) || 0).toFixed(2)}</td>
                      <td className="px-6 py-4 text-center">{getStatusBadge(entry.status)}</td>
                      <td className="px-6 py-4 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <button className="text-tertiary hover:text-white transition-colors" onClick={(e) => { e.stopPropagation(); window.location.href = `/review/${entry.receipt_id}` }}>
                            <ReceiptIcon size={16} />
                          </button>
                          {entry.status === 'POSTED' && (
                            <div onClick={(e) => e.stopPropagation()}>
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <button className="text-foreground/50 hover:text-white transition-colors p-1">
                                    <MoreVertical size={16} />
                                  </button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end" className="bg-surface-container-high border-white/10 text-white">
                                  <DropdownMenuItem onClick={() => handleIndividualExport(entry.id, 'xml', entry.entry_number)} className="hover:bg-white/10 cursor-pointer">
                                    Export as GnuCash XML
                                  </DropdownMenuItem>
                                  <DropdownMenuItem onClick={() => handleIndividualExport(entry.id, 'csv', entry.entry_number)} className="hover:bg-white/10 cursor-pointer">
                                    Export as CSV
                                  </DropdownMenuItem>
                                  <DropdownMenuItem onClick={() => handleIndividualExport(entry.id, 'sqlite', entry.entry_number)} className="hover:bg-white/10 cursor-pointer">
                                    Export as SQLite
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>

                    {/* Expanded Row (Debit/Credit Lines) */}
                    {expandedRows[entry.id] && (
                      <tr className="bg-black/40 border-b border-white/10">
                        <td colSpan={8} className="px-12 py-6">
                          <div className="glass-panel p-4 rounded-xl border border-white/5">
                            <h4 className="font-mono text-[10px] uppercase tracking-widest text-foreground/50 mb-3 border-b border-white/10 pb-2">Journal Entry Lines</h4>
                            {entry.lines && entry.lines.length > 0 ? (
                              <table className="w-full text-xs font-mono">
                                <thead>
                                  <tr className="text-foreground/40 border-b border-white/5">
                                    <th className="text-left pb-2 pr-4">Account</th>
                                    <th className="text-left pb-2 pr-4">Description</th>
                                    <th className="text-right pb-2 pr-4">Debit</th>
                                    <th className="text-right pb-2">Credit</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {entry.lines.map((line) => (
                                    <tr key={line.id} className="text-white/80 border-b border-white/5 last:border-0">
                                      <td className="py-1.5 pr-4">{line.account_code} — {line.account_name}</td>
                                      <td className="py-1.5 pr-4 text-foreground/60">{line.description || '—'}</td>
                                      <td className="py-1.5 pr-4 text-right">{Number(line.debit) > 0 ? `$${Number(line.debit).toFixed(2)}` : '—'}</td>
                                      <td className="py-1.5 text-right">{Number(line.credit) > 0 ? `$${Number(line.credit).toFixed(2)}` : '—'}</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
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
          <span className="font-sans text-xs text-foreground/50">
            Showing {entries.length} of {pagination.total} entries
          </span>
          <div className="flex gap-2">
            <button
              className="px-3 py-1.5 rounded-lg border border-white/10 text-white/40 font-sans text-xs hover:bg-white/5 disabled:opacity-50"
              disabled={pagination.page <= 1}
              onClick={() => loadEntries(pagination.page - 1)}
            >
              Previous
            </button>
            {Array.from({ length: Math.min(pagination.total_pages, 5) }, (_, i) => {
              const pageNum = i + 1;
              return (
                <button
                  key={pageNum}
                  className={`px-3 py-1.5 rounded-lg border font-sans text-xs ${pagination.page === pageNum ? 'bg-primary/20 border-primary/30 text-primary' : 'border-white/10 text-white hover:bg-white/5'}`}
                  onClick={() => loadEntries(pageNum)}
                >
                  {pageNum}
                </button>
              );
            })}
            <button
              className="px-3 py-1.5 rounded-lg border border-white/10 text-white font-sans text-xs hover:bg-white/5 disabled:opacity-50"
              disabled={pagination.page >= pagination.total_pages}
              onClick={() => loadEntries(pagination.page + 1)}
            >
              Next
            </button>
          </div>
        </div>
      </div>

    </div>
  )
}
