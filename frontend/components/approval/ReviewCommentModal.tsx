"use client";

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Loader2 } from 'lucide-react';

interface ReviewCommentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (comment: string) => void;
  isLoading: boolean;
}

export function ReviewCommentModal({
  isOpen,
  onClose,
  onSubmit,
  isLoading,
}: ReviewCommentModalProps) {
  const [comment, setComment] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!comment.trim()) return;
    onSubmit(comment);
    setComment('');
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-[#0b1326] border-white/10 text-[#dae2fd]">
        <DialogHeader>
          <DialogTitle className="text-[#dae2fd]">Reject Receipt</DialogTitle>
          <DialogDescription className="text-[#dae2fd]/60">
            Please provide a reason for rejection. The preparer will see this comment.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 mt-4">
          <div>
            <Label htmlFor="comment" className="text-[#dae2fd]/80">
              Rejection Reason <span className="text-red-400">*</span>
            </Label>
            <Textarea
              id="comment"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="e.g., Missing receipt image, incorrect totals, illegible vendor name..."
              className="mt-2 bg-white/5 border-white/10 text-[#dae2fd] placeholder:text-[#dae2fd]/30 focus:border-[#c0c1ff]"
              rows={4}
              required
            />
          </div>

          <div className="flex justify-end gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              className="border-white/20 text-[#dae2fd] hover:bg-white/10"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isLoading || !comment.trim()}
              className="bg-red-500 hover:bg-red-600 text-white"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
              ) : null}
              Reject Receipt
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
