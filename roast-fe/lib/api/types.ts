/**
 * Hand-written from api_doc.yaml (Roast Anything backend OpenAPI schema).
 * Keep in sync with that file if the backend contract changes.
 */

// --- Envelope ---------------------------------------------------------------

export interface ApiSuccessEnvelope<T> {
  success: true
  data: T
  meta: Record<string, unknown>
}

export interface ApiPaginatedEnvelope<T> {
  success: true
  data: T[]
  meta: {
    count: number
    next: string | null
    previous: string | null
    page_size: number
  }
}

export type ApiErrorCode =
  | "VALIDATION_ERROR"
  | "AUTHENTICATION_FAILED"
  | "EMAIL_NOT_VERIFIED"
  | "PERMISSION_DENIED"
  | "NOT_FOUND"
  | "METHOD_NOT_ALLOWED"
  | "THROTTLED"
  | "ERROR"
  | "INTERNAL_ERROR"

export interface ApiErrorEnvelope {
  success: false
  error: {
    code: ApiErrorCode
    message: string
    details: unknown
    request_id: string | null
  }
}

// --- Enums (mirror api_doc.yaml's *Enum schemas exactly) -------------------

export type SubmissionType = "resume" | "website" | "github"
export type Visibility = "private" | "link" | "public"
export type SubmissionStatus = "draft" | "processing" | "ready" | "failed" | "deleted"
/** Shared by RoastRun.status and the extraction pipeline (ExtractionStatusEnum). */
export type ExtractionStatus = "queued" | "processing" | "completed" | "failed"
export type Language = "en" | "hi" | "hinglish"
export type Intensity = "gentle" | "sarcastic" | "brutal" | "nuclear"
export type Severity = "info" | "low" | "medium" | "high" | "critical"

// --- Auth --------------------------------------------------------------------

export interface User {
  id: string
  email: string
  display_name: string
  avatar_url: string
  email_verified: boolean
  created_at: string
}

export interface RegisterRequest {
  email: string
  password: string
  display_name?: string
  referral_code?: string
}

export interface VerifyEmailRequest {
  email: string
  code: string
}

export interface ResendVerificationRequest {
  email: string
}

export interface RequestPasswordResetRequest {
  email: string
}

export interface ConfirmPasswordResetRequest {
  email: string
  code: string
  new_password: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface TokenPair {
  access: string
  refresh: string
}

export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}

/** GET/PATCH /auth/me/ body — display_name/avatar_url only (MeUpdateSerializer). */
export interface PatchMeRequest {
  display_name?: string
  avatar_url?: string
}

/**
 * DELETE /auth/me/ body. The yaml documents this under the `patch` operation's
 * request body keyed by a `DELETE` content-type (a drf_spectacular
 * @extend_schema quirk) — it does NOT describe PATCH's body. Do not send
 * `password` on a PATCH request.
 */
export interface DeleteMeRequest {
  password: string
}

// --- Submissions ---------------------------------------------------------------

export interface SubmissionAsset {
  id: string
  original_filename: string
  content_type: string
  size_bytes: number
  created_at: string
}

export interface SubmissionList {
  id: string
  submission_type: SubmissionType
  title: string
  status: SubmissionStatus
  error_message: string
  visibility: Visibility
  source_url: string | null
  created_at: string
  updated_at: string
  assets: SubmissionAsset[]
}

/** Full detail representation — adds extracted_text/metadata (owner-scoped only). */
export interface Submission extends SubmissionList {
  extracted_text: string
  metadata: unknown
}

/** `file` is present for multipart (resume) requests, `source_url` for website/github. */
export interface SubmissionCreateRequest {
  submission_type: SubmissionType
  title?: string
  visibility?: Visibility
  source_url?: string
  file?: File
}

/** title/visibility are the only user-mutable fields post-creation. */
export interface SubmissionUpdateRequest {
  title?: string
  visibility?: Visibility
}

export interface SubmissionStatusPoll {
  id: string
  status: SubmissionStatus
  error_message: string
  created_at: string
  updated_at: string
}

// --- Roasts ------------------------------------------------------------------

export interface RoastFinding {
  id: string
  category: string
  severity: Severity
  title: string
  roast_text: string
  actual_feedback: string
  position: number
  metadata: unknown
  created_at: string
}

export interface RoastSection {
  id: string
  key: string
  title: string
  content: string
  position: number
  metadata: unknown
  created_at: string
}

export interface RoastRunList {
  id: string
  submission: string
  language: Language
  intensity: Intensity
  status: ExtractionStatus
  engine_version: string
  started_at: string | null
  completed_at: string | null
  error_message: string
  summary: string
  score: number | null
  created_at: string
}

/** Full detail representation — includes nested sections/findings. */
export interface RoastRun extends RoastRunList {
  updated_at: string
  final_verdict: string
  sections: RoastSection[]
  findings: RoastFinding[]
}

export interface RoastRunCreateRequest {
  language: Language
  intensity: Intensity
}

export interface RoastRunStatusPoll {
  id: string
  status: ExtractionStatus
  started_at: string | null
  completed_at: string | null
  error_message: string
}

export interface RoastQuota {
  limit: number
  used: number
  remaining: number
  resets_at: string | null
  /** 0 when no referral bonus is currently active. */
  bonus_amount: number
  bonus_expires_at: string | null
}

/** GET /api/v1/referrals/me/ — the caller's own referral code and stats. */
export interface ReferralInfo {
  code: string
  referral_url: string
  total_referred: number
  total_qualified: number
}

// --- Sharing -------------------------------------------------------------------

export type ReactionType = "fire" | "skull" | "laughing" | "clap"

export type ReactionTotals = Record<ReactionType, number>

/** Lighter representation for the list-links endpoint — omits `reactions`. */
export interface ShareLinkList {
  id: string
  token: string
  share_url: string
  is_active: boolean
  view_count: number
  revoked_at: string | null
  created_at: string
}

/** Full detail — create/get response. */
export interface ShareLink extends ShareLinkList {
  reactions: ReactionTotals
}

/** Narrow, PII-free subset of Submission exposed on a public share page. */
export interface PublicSubmission {
  submission_type: SubmissionType
  title: string
}

export interface PublicRoastSection {
  id: string
  key: string
  title: string
  content: string
  position: number
}

export interface PublicRoastFinding {
  id: string
  category: string
  severity: Severity
  title: string
  roast_text: string
  actual_feedback: string
  position: number
}

/**
 * GET /api/v1/share/public/{token}/ — deliberately excludes `id`, `owner`,
 * `engine_version`, `error_message`, and anything from Submission beyond
 * submission_type/title (no source_url/extracted_text/metadata).
 */
export interface PublicRoast {
  language: Language
  intensity: Intensity
  status: ExtractionStatus
  summary: string
  final_verdict: string
  score: number | null
  created_at: string
  submission: PublicSubmission
  sections: PublicRoastSection[]
  findings: PublicRoastFinding[]
  reactions: ReactionTotals
}

export interface ReactionCreateRequest {
  reaction_type: ReactionType
}

/**
 * GET /api/v1/share/wall-of-fame/ entry — opt-in only (the owning
 * Submission's visibility must be "public"). Same PII-avoidance rules as
 * PublicRoast: no `id`, no `owner`.
 */
export interface WallOfFameEntry {
  token: string
  language: Language
  intensity: Intensity
  summary: string
  final_verdict: string
  score: number | null
  submission: PublicSubmission
  view_count: number
  total_reactions: number
  created_at: string
}
