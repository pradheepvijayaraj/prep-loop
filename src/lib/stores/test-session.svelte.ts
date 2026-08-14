import type {
  Question,
  TestMode,
  TestSessionState,
  TimerState,
} from "$lib/types";
import { INITIAL_TEST_SESSION_STATE, TIMER_THRESHOLDS } from "$lib/types";
import {
  saveAnswer as dbSaveAnswer,
  toggleFlag as dbToggleFlag,
  updateTimeRemaining,
  pauseTest,
  resumeTest,
} from "$lib/services/test-session";
import { logError } from "$lib/services/logger";
import { SessionCountdown } from "$lib/services/session-timer";

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

/**
 * Reactive test-session state (Svelte 5 `$state` rune).
 *
 * NOTE on reactivity (#1): Svelte 5's deep-reactive proxy tracks individual
 * property mutations, so writing `state.currentIndex++` only invalidates
 * subscribers of `currentIndex`. Full-object replacement (`state = { … }`)
 * happens only during lifecycle events (init / clear) where a complete
 * re-render is expected and acceptable.
 */
let state = $state<TestSessionState>({ ...INITIAL_TEST_SESSION_STATE });

/** Invalidates every async continuation when the active session changes. */
let sessionEpoch = 0;

/**
 * Promises for in-flight answer saves, drained before submission.
 *
 * DESIGN: We track every `saveAnswer` promise here so that
 * `flushPendingSaves()` can wait for them all to settle before
 * `submitTest` runs — otherwise the backend could score stale data.
 */
const pendingSaves = new Map<string, Set<Promise<void>>>();

/**
 * Map from `attemptId:questionId` → latest save promise.
 *
 * DESIGN: Serialises writes per-question so rapid answer changes don't
 * arrive at the backend out of order.  Each new save awaits the
 * previous one for the *same* question (but NOT for different questions,
 * keeping them parallelised).
 */
const questionSaveLocks = new Map<string, Promise<void>>();

/**
 * Simple boolean lock to prevent double-click flag toggles.
 *
 * Unlike `questionSaveLocks`, a single boolean is enough here because
 * flag toggling affects only the *current* question and the UI blocks
 * navigation while toggling.
 */
const flagToggleLocks = new Map<string, Promise<void>>();

/** Serialises timer writes per attempt so an older value cannot land last. */
const timerPersistChains = new Map<string, Promise<void>>();
const countdown = new SessionCountdown({
  onChange: (seconds) => {
    state.timeRemaining = seconds;
  },
  onPersist: () => persistTimer(),
  onExpire: () => persistTimer(),
});

function isCurrentSession(epoch: number, attemptId: string): boolean {
  return sessionEpoch === epoch && state.attemptId === attemptId;
}

function answersEqual(
  left: string | string[] | null | undefined,
  right: string | string[] | null | undefined,
): boolean {
  if (Array.isArray(left) && Array.isArray(right)) {
    return (
      left.length === right.length &&
      left.every((item, index) => item === right[index])
    );
  }
  return left === right;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Return the current reactive test-session state.
 *
 * @returns The live `TestSessionState` object. Because it is a `$state`
 *          proxy, property reads inside Svelte components will automatically
 *          subscribe to changes.
 */
export function getTestSessionState(): TestSessionState {
  return state;
}

/**
 * Initialise (or re-initialise) the test session.
 *
 * Clears any previous timer, resets state, and starts a new countdown
 * when `mode === "test"` and there is time remaining.
 *
 * @param attemptId       Backend attempt ID (UUID).
 * @param bankId          Question bank the attempt is drawn from.
 * @param mode            `"test"` (timed) or `"practice"` (untimed).
 * @param questions       Ordered list of questions for the session.
 * @param duration        Total configured duration in seconds.
 * @param timeRemaining   Seconds left (may differ from `duration` on resume).
 * @param existingAnswers Pre-populated answers (resume scenario).
 * @param existingFlags   Pre-populated flags (resume scenario).
 */
export function initTestSession(
  attemptId: string,
  bankId: string,
  mode: TestMode,
  questions: Question[],
  duration: number,
  timeRemaining: number,
  existingAnswers?: Map<string, string | string[]>,
  existingFlags?: Set<string>,
): void {
  // Clear any existing timer
  stopTimer(true);
  sessionEpoch += 1;

  // Full-object replacement is intentional here: initTestSession is a
  // lifecycle boundary where every field changes, so there's no benefit
  // to per-field mutation.  Svelte 5 will re-wrap the new object in a
  // fresh deep-reactive proxy.
  state = {
    attemptId,
    bankId,
    mode,
    questions,
    duration,
    currentIndex: 0,
    answers: existingAnswers || new Map(),
    flags: existingFlags || new Set(),
    timeRemaining,
    isPaused: false,
    isSubmitting: false,
  };

  // Start timer for test mode
  if (mode === "test" && timeRemaining > 0) {
    countdown.start(timeRemaining);
  }
}

/**
 * Determine the visual timer state based on the remaining time and
 * the configured thresholds.
 *
 * @returns `"critical"` | `"warning"` | `"normal"`
 */
export function getTimerState(): TimerState {
  if (state.timeRemaining <= TIMER_THRESHOLDS.CRITICAL) return "critical";
  if (state.timeRemaining <= TIMER_THRESHOLDS.WARNING) return "warning";
  return "normal";
}

/**
 * Navigate to a specific question by index.
 *
 * @param index Zero-based question index. Out-of-range values are ignored.
 */
export function goToQuestion(index: number): void {
  if (index >= 0 && index < state.questions.length) {
    state.currentIndex = index;
  }
}

/**
 * Advance to the next question. No-op if already on the last question.
 */
export function nextQuestion(): void {
  if (state.currentIndex < state.questions.length - 1) {
    state.currentIndex++;
  }
}

/**
 * Go back to the previous question. No-op if already on the first question.
 */
export function previousQuestion(): void {
  if (state.currentIndex > 0) {
    state.currentIndex--;
  }
}

/**
 * Return the question at `state.currentIndex`, or `null` if the question
 * list is empty.
 */
export function getCurrentQuestion(): Question | null {
  return state.questions[state.currentIndex] || null;
}

/**
 * Persist the user's answer for the current question.
 *
 * **Optimistic UI** – the local state is updated immediately so the UI
 * feels instant.  If the backend write fails the local state is
 * **rolled back** to the previous value and the error is re-thrown so
 * callers can surface a toast / notification.
 *
 * Uses per-question locking to prevent out-of-order writes when the user
 * changes answers rapidly.  The lock key includes `attemptId` to prevent
 * cross-session interference.
 *
 * @param answer The selected answer, or `null` to clear.
 * @throws Re-throws backend errors after rolling back and logging.
 */
export async function saveAnswer(
  answer: string | string[] | null,
): Promise<void> {
  const question = getCurrentQuestion();
  if (!question || !state.attemptId) return;

  const questionId = question.id;
  const attemptId = state.attemptId;
  const epoch = sessionEpoch;

  // Lock key includes attemptId to prevent cross-session races
  const lockKey = `${attemptId}:${questionId}`;

  // ── Snapshot for rollback (#2) ──────────────────────────────────────
  const previousAnswer = state.answers.has(questionId)
    ? state.answers.get(questionId)!
    : undefined; // undefined = key was absent

  // Update local state immediately for responsive UI (optimistic).
  // IMPORTANT: We create a *new* Map each time because Svelte 5 only
  // triggers reactivity for `state.answers` when the reference itself
  // changes.  Mutating the existing Map in-place (`state.answers.set(…)`)
  // would NOT notify Svelte subscribers.
  const nextAnswers = new Map(state.answers);
  if (answer === null) {
    nextAnswers.delete(questionId);
  } else {
    nextAnswers.set(questionId, answer);
  }
  state.answers = nextAnswers;

  // Wait for any previous save on this question to complete
  const previousSave = questionSaveLocks.get(lockKey);

  // DESIGN: The IIFE creates an immediately-started promise.  Its `.catch`
  // is chained onto the IIFE result — NOT onto the `await` inside — so
  // rollback logic runs for errors in *both* the previous-save wait and
  // the actual DB write.
  const saveOperation = (async () => {
    // Wait for previous save to complete (ignore errors, we still proceed)
    if (previousSave) {
      await previousSave.catch(() => {});
    }

    // Save to database
    await dbSaveAnswer(attemptId, questionId, answer);
  })().catch((error) => {
    // ── Rollback on failure (#2) ────────────────────────────────────
    if (
      isCurrentSession(epoch, attemptId) &&
      answersEqual(state.answers.get(questionId), answer)
    ) {
      const rollbackAnswers = new Map(state.answers);
      if (previousAnswer === undefined) {
        rollbackAnswers.delete(questionId);
      } else {
        rollbackAnswers.set(questionId, previousAnswer);
      }
      state.answers = rollbackAnswers;
    }

    void logError("Failed to save answer", error);
    throw error;
  });

  // Track this save operation
  questionSaveLocks.set(lockKey, saveOperation);
  const attemptSaves = pendingSaves.get(attemptId) ?? new Set<Promise<void>>();
  attemptSaves.add(saveOperation);
  pendingSaves.set(attemptId, attemptSaves);

  try {
    await saveOperation;
  } finally {
    attemptSaves.delete(saveOperation);
    if (attemptSaves.size === 0) pendingSaves.delete(attemptId);
    // Only clear the lock if this is still the latest save for this question
    if (questionSaveLocks.get(lockKey) === saveOperation) {
      questionSaveLocks.delete(lockKey);
    }
  }
}

/**
 * Look up the currently saved answer for a question.
 *
 * @param questionId Question ID to look up.
 * @returns The stored answer, or `null` if unanswered.
 */
export function getAnswer(questionId: string): string | string[] | null {
  return state.answers.get(questionId) ?? null;
}

/**
 * Toggle the flag on the current question.
 *
 * The backend is the source of truth: the flag state returned by
 * `dbToggleFlag` is applied to local state.  A simple boolean lock
 * prevents double-click issues.
 *
 * @throws Re-throws backend errors after logging.
 */
export async function toggleCurrentFlag(): Promise<void> {
  const question = getCurrentQuestion();
  if (!question || !state.attemptId) return;
  const attemptId = state.attemptId;
  const questionId = question.id;
  const epoch = sessionEpoch;
  const lockKey = `${attemptId}:${questionId}`;
  const previousToggle = flagToggleLocks.get(lockKey);
  const operation = (async () => {
    if (previousToggle) await previousToggle.catch(() => {});
    const isFlagged = await dbToggleFlag(attemptId, questionId);
    if (!isCurrentSession(epoch, attemptId)) return;
    const nextFlags = new Set(state.flags);
    if (isFlagged) nextFlags.add(questionId);
    else nextFlags.delete(questionId);
    state.flags = nextFlags;
  })();
  flagToggleLocks.set(lockKey, operation);
  try {
    await operation;
  } catch (error) {
    void logError("Failed to toggle question flag", error);
    throw error;
  } finally {
    if (flagToggleLocks.get(lockKey) === operation)
      flagToggleLocks.delete(lockKey);
  }
}

/**
 * Check whether a question is currently flagged.
 */
export function isFlagged(questionId: string): boolean {
  return state.flags.has(questionId);
}

/**
 * Check whether a question has been answered.
 */
export function isAnswered(questionId: string): boolean {
  return state.answers.has(questionId);
}

/**
 * Pause the test.
 *
 * Sets `isPaused` optimistically. On backend failure the flag is
 * rolled back to `false` and the error is re-thrown.
 *
 * @throws Re-throws backend errors after rollback and logging.
 */
export async function pause(): Promise<void> {
  if (!state.attemptId || state.mode !== "test" || state.isPaused) return;
  countdown.pause();
  const attemptId = state.attemptId;
  const epoch = sessionEpoch;
  state.isPaused = true;

  try {
    await pauseTest(attemptId, state.timeRemaining);
  } catch (error) {
    if (isCurrentSession(epoch, attemptId)) {
      state.isPaused = false;
      countdown.resume(state.timeRemaining);
    }
    void logError("Failed to pause test", error);
    throw error;
  }
}

/**
 * Resume a paused test.
 *
 * Sets `isPaused` to `false` optimistically. On backend failure the flag
 * is rolled back to `true` and the error is re-thrown.
 *
 * @throws Re-throws backend errors after rollback and logging.
 */
export async function resume(): Promise<void> {
  if (!state.attemptId || state.mode !== "test" || !state.isPaused) return;
  const attemptId = state.attemptId;
  const epoch = sessionEpoch;
  state.isPaused = false;
  countdown.resume(state.timeRemaining);

  try {
    await resumeTest(attemptId);
  } catch (error) {
    if (isCurrentSession(epoch, attemptId)) {
      state.isPaused = true;
      countdown.pause();
    }
    void logError("Failed to resume test", error);
    throw error;
  }
}

/**
 * Set the submitting flag (disables navigation while submission is pending).
 */
export function setSubmitting(isSubmitting: boolean): void {
  state.isSubmitting = isSubmitting;
}

/**
 * Return navigation metadata for the current question.
 */
export function getNavigationInfo(): {
  current: number;
  total: number;
  canNext: boolean;
  canPrevious: boolean;
} {
  return {
    current: state.currentIndex + 1,
    total: state.questions.length,
    canNext: state.currentIndex < state.questions.length - 1,
    canPrevious: state.currentIndex > 0,
  };
}

/**
 * Return progress statistics (answered / flagged / total).
 */
export function getProgress(): {
  answered: number;
  flagged: number;
  total: number;
} {
  return {
    answered: state.answers.size,
    flagged: state.flags.size,
    total: state.questions.length,
  };
}

/**
 * Tear down the current test session.
 *
 * Stops the timer, drains in-flight saves, clears locks, and resets
 * every field of the session state individually (avoids a full-object
 * replacement so Svelte's granular reactivity can short-circuit
 * unchanged subscribers).
 */
export function clearTestSession(persistTimer = true): void {
  stopTimer(persistTimer);
  sessionEpoch += 1;

  // Reset fields individually (#1) — avoids an unnecessary full-proxy
  // re-wrap while keeping the code explicit about what gets cleared.
  state.attemptId = null;
  state.bankId = null;
  state.mode = null;
  state.questions = [];
  state.duration = 0;
  state.currentIndex = 0;
  state.answers = new Map();
  state.flags = new Set();
  state.timeRemaining = 0;
  state.isPaused = false;
  state.isSubmitting = false;
}

/**
 * Check whether the countdown has reached zero (test mode only).
 */
export function isTimerExpired(): boolean {
  return state.mode === "test" && state.timeRemaining <= 0;
}

/**
 * Wait for every in-flight answer save to settle before submission.
 *
 * Uses `Promise.allSettled` so that all saves complete even if some fail,
 * then throws a single consolidated error if any save rejected.
 *
 * @throws {Error} If one or more saves failed, with a count in the message.
 */
export async function flushPendingSaves(): Promise<void> {
  if (!state.attemptId) return;
  const currentSaves = pendingSaves.get(state.attemptId);
  if (!currentSaves?.size) return;
  const results = await Promise.allSettled([...currentSaves]);
  const failCount = results.filter((r) => r.status === "rejected").length;
  if (failCount > 0) {
    throw new Error(`${failCount} answer(s) failed to save`);
  }
}

function stopTimer(shouldPersist = false): void {
  countdown.stop();
  if (shouldPersist) persistTimer();
}

/**
 * Fire-and-forget helper that persists the current `timeRemaining` to the
 * backend.  Errors are logged but not propagated.
 */
function persistTimer(): void {
  if (!state.attemptId) return;
  const attemptId = state.attemptId;
  const timeRemaining = state.timeRemaining;
  const previous = timerPersistChains.get(attemptId) ?? Promise.resolve();
  const operation = previous
    .catch(() => {})
    .then(() => updateTimeRemaining(attemptId, timeRemaining))
    .catch((error) => {
      void logError(`Failed to persist timer (attempt=${attemptId})`, error);
    });
  timerPersistChains.set(attemptId, operation);
  void operation.finally(() => {
    if (timerPersistChains.get(attemptId) === operation)
      timerPersistChains.delete(attemptId);
  });
}
