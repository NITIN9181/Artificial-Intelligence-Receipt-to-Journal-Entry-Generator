"use client";

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { useAuth } from '@/lib/auth-context';
import { Receipt, ReceiptStatus } from '@/types';
import { toast } from 'sonner';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Send, RotateCcw, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { formatDate, formatCurrency } from '@/lib/utils';

const STATUS_CONFIG: Record<ReceiptStatus, { label: string; color: string; icon: React.ElementType }> = {
  UPLOADED: { label: 'Uploaded', color: '#94A3B8', icon: Clock },
  EXTRACTING: { label: 'Extracting', color: '#818CF8', icon: Clock },
  EXTRACTED: { label: 'Extracted', color: '#3B82F6', icon: CheckCircle },
  EXTRACTION_FAILED: { label: 'Extraction Failed', color: '#EF4444', icon: AlertCircle },
  VALIDATION_FAILED: { label: 'Validation Failed', color: '#EF4444', icon: AlertCircle },
  REVIEWED: { label: 'Ready to Submit', color: '#14B8A6', icon: CheckCircle },
  PENDING_REVIEW: { label: 'Awaiting Review', color: '#818CF8', icon: Clock },
  POSTED: { label: 'Posted', color: '#22C55E', icon: CheckCircle },
  REJECTED: { label: 'Rejected', color: '#EF4444', icon: AlertCircle },
  QUARANTINED: { label: 'Quarantined', color: '#F59E0B', icon: AlertCircle },
};

interface SubmissionCardProps {
  receipt: Receipt;
  statusConfig: { label: string; color: string; icon: React.ElementType };
  onSubmit: () => void;
  onEdit: () => void;
  isSubmitting: boolean;
}

function SubmissionCard({ receipt, statusConfig, onSubmit, onEdit, isSubmitting }: SubmissionCardProps) {
  const extracted = receipt.extracted_data as any;

  return (
    <Card className="bg-white/5 border-white/10 p-4 hover:border-white/20 transition-colors">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h3 className="font-medium text-[#dae2fd]">
              {extracted?.vendor_name || 'Unknown Vendor'}
            </h3>
            <Badge style={{ borderColor: statusConfig.color, color: statusConfig.color }} variant="outline">
              {statusConfig.label}
            </Badge>
          </div>
          <p className="text-sm text-[#dae2fd]/50 mt-1">
            {formatCurrency(extracted?.total)} • {formatDate(receipt.created_at)}
          </p>

          {receipt.status === 'REJECTED' && receipt.review_comments?.[0] && (
            <div className="mt-3 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
              <p className="text-sm text-red-300">
                <span className="font-semibold">Rejection reason:</span>{' '}
                {receipt.review_comments[0].comment}
              </p>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          {receipt.status === 'REVIEWED' && (
            <Button
              size="sm"
              onClick={onSubmit}
              disabled={isSubmitting}
              className="bg-[#c0c1ff] text-[#0b1326] hover:bg-[#c0c1ff]/90"
            >
              <Send className="w-4 h-4 mr-1" />
              Submit for Review
            </Button>
          )}

          {(receipt.status === 'REJECTED' || receipt.status === 'EXTRACTED') && (
            <Button
              size="sm"
              variant="outline"
              onClick={onEdit}
              className="border-white/20 text-[#dae2fd] hover:bg-white/10"
            >
              <RotateCcw className="w-4 h-4 mr-1" />
              Edit & Resubmit
            </Button>
          )}

          {receipt.status === 'PENDING_REVIEW' && (
            <span className="text-sm text-[#dae2fd]/50 flex items-center gap-1">
              <Clock className="w-4 h-4" />
              Waiting for reviewer
            </span>
          )}
        </div>
      </div>
    </Card>
  );
}

export default function SubmissionsPage() {
  const { user } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data: receipts, isLoading } = useQuery({
    queryKey: ['my-submissions'],
    queryFn: () => apiClient<Receipt[]>('/receipts/my'),
  });

  const submitMutation = useMutation({
    mutationFn: (id: string) =>
      apiClient<Receipt>(`/receipts/${id}/submit`, { method: 'POST' }),
    onSuccess: () => {
      toast.success('Submitted for review');
      queryClient.invalidateQueries({ queryKey: ['my-submissions'] });
    },
    onError: (error: any) => toast.error(error.message || 'Submission failed'),
  });

  if (isLoading) return <LoadingSpinner />;

  const grouped = receipts?.reduce((acc, receipt) => {
    const status = receipt.status;
    if (!acc[status]) acc[status] = [];
    acc[status].push(receipt);
    return acc;
  }, {} as Record<ReceiptStatus, Receipt[]>) || ({} as Record<ReceiptStatus, Receipt[]>);

  const statusOrder: ReceiptStatus[] = ['REVIEWED', 'PENDING_REVIEW', 'REJECTED', 'POSTED', 'EXTRACTED', 'UPLOADED'];

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold text-[#dae2fd] font-[Manrope] mb-8">
        My Submissions
      </h1>

      <div className="space-y-8">
        {statusOrder.map((status) => {
          const items = grouped[status];
          if (!items?.length) return null;

          const config = STATUS_CONFIG[status];
          const Icon = config.icon;

          return (
            <section key={status}>
              <div className="flex items-center gap-2 mb-4">
                <Icon className="w-5 h-5" style={{ color: config.color }} />
                <h2 className="text-lg font-semibold text-[#dae2fd]">
                  {config.label}
                </h2>
                <Badge className="bg-white/10 text-[#dae2fd]/70">
                  {items.length}
                </Badge>
              </div>

              <div className="grid gap-3">
                {items.map((receipt) => (
                  <SubmissionCard
                    key={receipt.id}
                    receipt={receipt}
                    statusConfig={config}
                    onSubmit={() => submitMutation.mutate(receipt.id)}
                    onEdit={() => router.push(`/review/${receipt.id}`)}
                    isSubmitting={submitMutation.isPending}
                  />
                ))}
              </div>
            </section>
          );
        })}

        {(!receipts || receipts.length === 0) && (
          <div className="text-center py-20">
            <p className="text-[#dae2fd]/50">No submissions yet.</p>
            <Button
              onClick={() => router.push('/upload')}
              className="mt-4 bg-[#c0c1ff] text-[#0b1326] hover:bg-[#c0c1ff]/90"
            >
              Upload Your First Receipt
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
