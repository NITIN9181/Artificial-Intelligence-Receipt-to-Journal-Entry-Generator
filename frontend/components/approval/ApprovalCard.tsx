"use client";

import { Receipt } from '@/types';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Check, X, Eye, Loader2 } from 'lucide-react';
import { formatDate, formatCurrency } from '@/lib/utils';

interface ApprovalCardProps {
  receipt: Receipt;
  onApprove: () => void;
  onReject: () => void;
  onView: () => void;
  isApproving: boolean;
  isRejecting: boolean;
}

export function ApprovalCard({
  receipt,
  onApprove,
  onReject,
  onView,
  isApproving,
  isRejecting,
}: ApprovalCardProps) {
  const extracted = receipt.extracted_data as any;

  return (
    <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-6 hover:border-[#c0c1ff]/30 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-lg font-semibold text-[#dae2fd]">
              {extracted?.vendor_name || 'Unknown Vendor'}
            </h3>
            <Badge variant="outline" className="border-[#818CF8] text-[#818CF8]">
              PENDING_REVIEW
            </Badge>
          </div>

          <div className="grid grid-cols-3 gap-4 text-sm mt-3">
            <div>
              <p className="text-[#dae2fd]/50">Date</p>
              <p className="text-[#dae2fd]">{formatDate(extracted?.date)}</p>
            </div>
            <div>
              <p className="text-[#dae2fd]/50">Total</p>
              <p className="text-[#dae2fd] font-mono">
                {formatCurrency(extracted?.total)}
              </p>
            </div>
            <div>
              <p className="text-[#dae2fd]/50">Submitted By</p>
              <p className="text-[#dae2fd]">{receipt.user?.full_name || 'Unknown'}</p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onView}
            className="border-white/20 text-[#dae2fd] hover:bg-white/10"
          >
            <Eye className="w-4 h-4 mr-1" />
            View
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={onReject}
            disabled={isApproving || isRejecting}
            className="border-red-500/30 text-red-400 hover:bg-red-500/10 hover:text-red-300"
          >
            {isRejecting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <X className="w-4 h-4 mr-1" />
            )}
            Reject
          </Button>

          <Button
            size="sm"
            onClick={onApprove}
            disabled={isApproving || isRejecting}
            className="bg-[#22C55E] hover:bg-[#22C55E]/90 text-white"
          >
            {isApproving ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Check className="w-4 h-4 mr-1" />
            )}
            Approve
          </Button>
        </div>
      </div>
    </div>
  );
}
