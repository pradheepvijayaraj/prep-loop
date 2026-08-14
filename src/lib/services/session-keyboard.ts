/**
 * Keyboard shortcut handler factory for test/practice sessions.
 *
 * Creates a `keydown` event handler that dispatches keyboard shortcuts
 * to appropriate callbacks:
 *
 *   n / ArrowRight   \u2192  Next question
 *   b / ArrowLeft    \u2192  Previous question
 *   f               \u2192  Toggle flag
 *   Space           \u2192  Pause/resume (test mode)
 *   r               \u2192  Toggle feedback (practice mode)
 *   Ctrl+Enter      \u2192  Open submit dialog
 *   1\u20139             \u2192  Select option by number
 *
 * Shortcuts are suppressed when a dialog is open, the test is paused,
 * or the user is typing in an input field.
 */
import type { Question } from "$lib/types";

export function isTypingTarget(target: EventTarget | null): boolean {
  return (
    target instanceof HTMLInputElement ||
    target instanceof HTMLTextAreaElement ||
    (target instanceof HTMLElement && target.isContentEditable)
  );
}

/** Compute an option-key answer synchronously from the latest store value. */
export function getShortcutAnswer(
  question: Question,
  currentAnswer: string | string[] | null,
  optionId: string,
): string | string[] | null {
  if (question.type === "multiple-choice") {
    const selections = Array.isArray(currentAnswer)
      ? [...currentAnswer]
      : typeof currentAnswer === "string"
        ? [currentAnswer]
        : [];
    const index = selections.indexOf(optionId);
    if (index >= 0) selections.splice(index, 1);
    else selections.push(optionId);
    return selections.length > 0 ? selections : null;
  }

  return currentAnswer === optionId ? null : optionId;
}

interface SessionKeyboardOptions {
  mode: "test" | "practice";
  isPaused?: () => boolean;
  isDialogOpen: () => boolean;
  getCurrentQuestion: () => Question | null;
  onNext: () => void;
  onPrevious: () => void;
  onToggleFlag: () => void | Promise<void>;
  onOpenSubmit: () => void;
  onOptionShortcut: (optionId: string) => void | Promise<void>;
  onPause?: () => void | Promise<void>;
  onResume?: () => void | Promise<void>;
  onToggleFeedback?: () => void;
}

export function createSessionKeyboardHandler(options: SessionKeyboardOptions) {
  return (event: KeyboardEvent) => {
    const key = event.key.toLowerCase();
    const isSpace = event.code === "Space" || key === " " || key === "spacebar";

    if (isTypingTarget(event.target)) {
      return;
    }

    if (key === "backspace" || isSpace) {
      event.preventDefault();
    }

    if (key === "backspace") {
      return;
    }

    if (isSpace) {
      if (options.mode === "test") {
        if (options.isPaused?.()) {
          void options.onResume?.();
        } else {
          void options.onPause?.();
        }
      }
      return;
    }

    if (options.isDialogOpen()) {
      return;
    }

    if (options.isPaused?.()) {
      return;
    }

    if (key === "enter" && (event.ctrlKey || event.metaKey)) {
      event.preventDefault();
      options.onOpenSubmit();
      return;
    }

    if (event.ctrlKey || event.metaKey || event.altKey) {
      return;
    }

    switch (key) {
      case "arrowright":
        event.preventDefault();
        options.onNext();
        return;
      case "arrowleft":
        event.preventDefault();
        options.onPrevious();
        return;
      case "f":
        event.preventDefault();
        void options.onToggleFlag();
        return;
      case "r":
        if (options.mode === "practice" && options.onToggleFeedback) {
          event.preventDefault();
          options.onToggleFeedback();
        }
        return;
      default:
        break;
    }

    const index = Number.parseInt(event.key, 10) - 1;
    const question = options.getCurrentQuestion();

    if (index < 0 || index > 8 || !question?.options) {
      return;
    }

    const option = question.options[index];
    if (!option) {
      return;
    }

    event.preventDefault();
    void options.onOptionShortcut(option.id);
  };
}
