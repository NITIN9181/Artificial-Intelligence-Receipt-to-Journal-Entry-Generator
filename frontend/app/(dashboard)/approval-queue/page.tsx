"use client";

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { useAuth } from '@/lib/auth-context';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { Receipt } from '@/types';
import { ApprovalCard } from '@/components/approval/ApprovalCard';
import { ReviewCommentModal } from '@/components/approval/ReviewCommentModal';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { ClipboardCheck } from 'lucide-react';

export default function ApprovalQueuePage() {
  const { isReviewer } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [rejectingId, setRejectingId] = useState<string | null>(null);

  // Redirect non-reviewers
  if (!isReviewer) {
    router.push('/dashboard');
    return null;
  }

  const { data: receipts, isLoading } = useQuery({
    queryKey: ['pending-review'],
    queryFn: () => apiClient<Receipt[]>('/receipts/pending-review'),
    refetchInterval: 30000,
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) =>
      apiClient<Receipt>(`/receipts/${id}/approve`, { method: 'POST' }),
    onSuccess: () => {
      toast.success('Receipt approved successfully');
      queryClient.invalidateQueries({ queryKey: ['pending-review'] });
      queryClient.invalidateQueries({ queryKey: ['pending-review-count'] });
    },
    onError: (error: any) => {
      toast.error(`Approval failed: ${error.message || 'Unknown error'}`);
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, comment }: { id: string; comment: string }) =>
      apiClient<Receipt>(`/receipts/${id}/reject`, {
        method: 'POST',
        body: JSON.stringify({ comment }),
      }),
    onSuccess: () => {
      toast.success('Receipt rejected');
      setRejectingId(null);
      queryClient.invalidateQueries({ queryKey: ['pending-review'] });
      queryClient.invalidateQueries({ queryKey: ['pending-review-count'] });
    },
    onError: (error: any) => {
      toast.error(`Rejection failed: ${error.message || 'Unknown error'}`);
    },
  });

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[#dae2fd] font-[Manrope]">
          Approval Queue
        </h1>
        <p className="text-[#dae2fd]/60 mt-1">
          {receipts?.length || 0} receipts awaiting review
        </p>
      </div>

      {receipts?.length === 0 ? (
        <div className="text-center py-20 bg-white/5 rounded-xl border border-white/10">
          <ClipboardCheck className="w-16 h-16 text-[#dae2fd]/30 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-[#dae2fd]">All caught up!</h3>
          <p className="text-[#dae2fd]/50 mt-2">No receipts pending review.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {receipts?.map((receipt) => (
            <ApprovalCard
              key={receipt.id}
              receipt={receipt}
              onApprove={() => approveMutation.mutate(receipt.id)}
              onReject={() => setRejectingId(receipt.id)}
              onView={() => router.push(`/review/${receipt.id}`)}
              isApproving={approveMutation.isPending && approveMutation.variables === receipt.id}
              isRejecting={rejectMutation.isPending && rejectMutation.variables?.id === receipt.id}
            />
          ))}
        </div>
      )}

      <ReviewCommentModal
        isOpen={!!rejectingId}
        onClose={() => setRejectingId(null)}
        onSubmit={(comment) => {
          if (rejectingId) {
            rejectMutation.mutate({ id: rejectingId, comment });
          }
        }}
        isLoading={rejectMutation.isPending}
      />
    </div>
  );
}
