export type UserRole = 'PREPARER' | 'REVIEWER' | 'ADMIN';

export interface User {
  id: string;
  full_name: string | null;
  company_name: string | null;
  role: UserRole;
  created_at: string;
  email?: string;
}

export type ReceiptStatus =
  | 'UPLOADED'
  | 'EXTRACTING'
  | 'EXTRACTED'
  | 'EXTRACTION_FAILED'
  | 'VALIDATION_FAILED'
  | 'REVIEWED'
  | 'PENDING_REVIEW'
  | 'POSTED'
  | 'REJECTED'
  | 'QUARANTINED';

export interface Receipt {
  id: string;
  user_id: string;
  user?: User;
  image_url: string;
  status: ReceiptStatus;
  extracted_data: Record<string, any> | null;
  confidence_scores: Record<string, number> | null;
  raw_llm_output: string | null;
  extraction_error: string | null;
  extracted_at: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
  review_comments?: ReviewComment[];
}

export interface ReviewComment {
  id: string;
  receipt_id: string;
  reviewer_id: string | null;
  reviewer?: User;
  comment: string;
  action: 'APPROVED' | 'REJECTED' | 'RETURNED';
  created_at: string;
}

export interface JournalEntry {
  id: string;
  receipt_id: string;
  entry_number: string;
  entry_date: string;
  description: string | null;
  total_debit: number;
  total_credit: number;
  status: 'DRAFT' | 'POSTED' | 'REVERSED' | 'QUARANTINED';
  reversal_of_id: string | null;
  posted_by: string | null;
  posted_at: string | null;
  created_at: string;
  lines?: JournalEntryLine[];
}

export interface JournalEntryLine {
  id: string;
  journal_entry_id: string;
  account_code: string;
  account_name: string;
  debit: number;
  credit: number;
  description: string | null;
  line_order: number;
}

export interface GnuCashMapping {
  id: string;
  internal_account_code: string;
  gnucash_account_path: string;
}
