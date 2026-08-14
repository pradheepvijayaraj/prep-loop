/**
 * Shared TypeScript type definitions.
 *
 * These types mirror the Rust backend types (src-tauri/src/backend/types.rs).
 * When adding or changing fields, ensure both sides stay in sync.
 *
 * SECTIONS:
 *   1. Enums & literals (QuestionType, Difficulty, etc.)
 *   2. Domain models (Question, QuestionBank, TestAttempt, etc.)
 *   3. Settings
 *   4. UI state types (TestSessionState, NavigationState, etc.)
 *   5. Constants (defaults, thresholds)
 */

// ── Enums & literals ───────────────────────────────────────────────

// Question Types
export type QuestionType =
  | "single-choice"
  | "multiple-choice"
  | "true-false"
  | "fill-blank"
  | "numerical";

export type Difficulty = "easy" | "medium" | "hard";

// ── Domain models ─────────────────────────────────────────────────

// Question Option (for choice-based questions)
export interface QuestionOption {
  id: string;
  text: string;
}

// Single Question
export interface Question {
  id: string;
  type: QuestionType;
  question: string;
  options?: QuestionOption[];
  correctAnswers: string[]; // Array to support multiple correct answers
  explanation: string;
  marks: number;
  negativeMarks: number;
  negativeMarksUnanswered?: number; // Optional: penalty for unanswered (defaults to 0)
  timeEstimate?: number; // Optional: estimated time in seconds
  difficulty?: Difficulty;
  tags?: string[];
}

// Question Bank Metadata
export interface QuestionBankMetadata {
  name: string;
  exam: string;
  totalQuestions: number;
  difficulty: Difficulty;
  defaultDuration: number; // seconds
  year?: number;
  stage?: string;
  paper?: string;
  section?: string;
  practiceMode?: "mcq" | "descriptive";
  contentVersion?: number;
}

// Question Bank (imported JSON structure)
export interface QuestionBank {
  metadata: QuestionBankMetadata;
  questions: Question[];
}

// Stored Question Bank (database record)
export interface StoredQuestionBank {
  id: string;
  name: string;
  exam: string;
  metadata: string; // JSON string
  totalQuestions: number;
  difficulty: Difficulty;
  defaultDuration: number;
  importedAt: number; // Unix timestamp
}

// Test Modes
export type TestMode = "test" | "practice";

// Test Status
export type TestStatus = "in_progress" | "paused" | "completed";

// Test Attempt (active test session)
export interface TestAttempt {
  id: string;
  bankId: string;
  mode: TestMode;
  status: TestStatus;
  duration: number; // configured duration in seconds
  timeRemaining: number; // seconds left
  startedAt: number; // Unix timestamp
  completedAt?: number; // Unix timestamp
  score?: number;
  maxScore?: number;
}

export interface TestAttemptHistoryEntry {
  id: string;
  completedAt: number;
  paper: string;
  score: number;
  maxScore: number;
}

// Test Result (calculated after submission)
export interface TestResult {
  attemptId: string;
  totalQuestions: number;
  correct: number;
  wrong: number;
  unanswered: number;
  flagged: number;
  score: number;
  maxScore: number;
  timeTaken: number; // seconds
  categoryBreakdown?: CategoryScore[];
}

// Category Score (for tag-based breakdown)
export interface CategoryScore {
  category: string;
  positiveMarks: number;
  negativeMarks: number;
}

// Question Review Item (for detailed review)
export interface QuestionReviewItem {
  question: Question;
  userAnswer: string | string[] | null;
  isCorrect: boolean;
  isFlagged: boolean;
  marksObtained: number;
}

export interface QuestionSearchResult {
  questionId: string;
  bankId: string;
  bankName: string;
  questionNumber: number;
  question: string;
  options: QuestionOption[];
  year?: number | null;
  stage: string;
  paper: string;
  section: string;
  mainTag: string;
  subtags: string[];
  similarity: number;
}

export interface QuestionSearchResponse {
  query: string;
  searchedQuestions: number;
  totalMatches: number;
  results: QuestionSearchResult[];
}

// ── Settings ──────────────────────────────────────────────────────

// Settings
export interface Settings {
  // Appearance
  theme: "system" | "light" | "dark";

  // Navigator
  navigatorExpanded: boolean;

  // Library
  lastLibrarySelectionId: string | null;

  // Practice Mode
  practiceShowImmediateFeedback: boolean;

  // Test Preferences
  autoSubmitOnTimerEnd: boolean;
}

// Default Settings
export const DEFAULT_SETTINGS: Settings = {
  theme: "system",
  navigatorExpanded: false,
  lastLibrarySelectionId: null,
  practiceShowImmediateFeedback: true,
  autoSubmitOnTimerEnd: true,
};

// Timer State
export type TimerState = "normal" | "warning" | "critical";

// Timer thresholds (in seconds)
export const TIMER_THRESHOLDS = {
  WARNING: 600, // 10 minutes
  CRITICAL: 300, // 5 minutes
} as const;

// Import Result
export interface ImportResult {
  success: boolean;
  bankId?: string;
  error?: string;
  validationErrors?: string[];
}

// Question Bank with Questions (for display)
export interface QuestionBankWithQuestions extends StoredQuestionBank {
  questions: Question[];
}

// ── UI state types & constants ─────────────────────────────────────

// Test Session State (for stores)
export interface TestSessionState {
  attemptId: string | null;
  bankId: string | null;
  mode: TestMode | null;
  questions: Question[];
  duration: number;
  currentIndex: number;
  answers: Map<string, string | string[]>;
  flags: Set<string>;
  timeRemaining: number;
  isPaused: boolean;
  isSubmitting: boolean;
}

// Initial Test Session State
export const INITIAL_TEST_SESSION_STATE: TestSessionState = {
  attemptId: null,
  bankId: null,
  mode: null,
  questions: [],
  duration: 0,
  currentIndex: 0,
  answers: new Map(),
  flags: new Set(),
  timeRemaining: 0,
  isPaused: false,
  isSubmitting: false,
};
