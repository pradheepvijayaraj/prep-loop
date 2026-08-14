import { describe, expect, it, vi } from "vitest";
import {
  createSessionKeyboardHandler,
  getShortcutAnswer,
} from "$lib/services/session-keyboard";
import type { Question } from "$lib/types";

const question: Question = {
  id: "q1",
  type: "single-choice",
  question: "Question",
  options: [
    { id: "a", text: "A" },
    { id: "b", text: "B" },
  ],
  correctAnswers: ["a"],
  explanation: "Because",
  marks: 2,
  negativeMarks: 0.5,
};

function createBaseHandler(
  overrides: Partial<Parameters<typeof createSessionKeyboardHandler>[0]> = {},
) {
  return createSessionKeyboardHandler({
    mode: "test",
    isPaused: () => false,
    isDialogOpen: () => false,
    getCurrentQuestion: () => question,
    onNext: vi.fn(),
    onPrevious: vi.fn(),
    onToggleFlag: vi.fn(),
    onOpenSubmit: vi.fn(),
    onOptionShortcut: vi.fn(),
    onPause: vi.fn(),
    onResume: vi.fn(),
    ...overrides,
  });
}

describe("createSessionKeyboardHandler", () => {
  it("opens submit dialog on ctrl-enter", () => {
    const onOpenSubmit = vi.fn();
    const handler = createBaseHandler({ onOpenSubmit });
    const event = new KeyboardEvent("keydown", { key: "Enter", ctrlKey: true });

    handler(event);

    expect(onOpenSubmit).toHaveBeenCalledOnce();
  });

  it("ignores shortcuts when a dialog is open", () => {
    const onNext = vi.fn();
    const handler = createBaseHandler({
      isDialogOpen: () => true,
      onNext,
    });
    const event = new KeyboardEvent("keydown", { key: "ArrowRight" });

    handler(event);

    expect(onNext).not.toHaveBeenCalled();
  });

  it("ignores shortcuts when typing in an input", () => {
    const onToggleFlag = vi.fn();
    const handler = createBaseHandler({ onToggleFlag });
    const event = new KeyboardEvent("keydown", { key: "f" });
    Object.defineProperty(event, "target", {
      value: document.createElement("input"),
    });

    handler(event);

    expect(onToggleFlag).not.toHaveBeenCalled();
  });

  it("routes option shortcuts from number keys", () => {
    const onOptionShortcut = vi.fn();
    const handler = createBaseHandler({ onOptionShortcut });
    const event = new KeyboardEvent("keydown", { key: "2" });

    handler(event);

    expect(onOptionShortcut).toHaveBeenCalledWith("b");
  });

  it("resumes a paused test on space", () => {
    const onResume = vi.fn();
    const onPause = vi.fn();
    const handler = createBaseHandler({
      isPaused: () => true,
      onResume,
      onPause,
    });
    const event = new KeyboardEvent("keydown", { key: " " });

    handler(event);

    expect(onResume).toHaveBeenCalledOnce();
    expect(onPause).not.toHaveBeenCalled();
  });

  it("supports practice-only feedback toggles", () => {
    const onToggleFeedback = vi.fn();
    const handler = createSessionKeyboardHandler({
      mode: "practice",
      isDialogOpen: () => false,
      getCurrentQuestion: () => question,
      onNext: vi.fn(),
      onPrevious: vi.fn(),
      onToggleFlag: vi.fn(),
      onOpenSubmit: vi.fn(),
      onOptionShortcut: vi.fn(),
      onToggleFeedback,
    });
    const event = new KeyboardEvent("keydown", { key: "r" });

    handler(event);

    expect(onToggleFeedback).toHaveBeenCalledOnce();
  });
});

describe("getShortcutAnswer", () => {
  it("toggles a single-choice answer", () => {
    expect(getShortcutAnswer(question, null, "a")).toBe("a");
    expect(getShortcutAnswer(question, "a", "a")).toBeNull();
  });

  it("uses the latest multiple-choice value without an IPC race", () => {
    const multiple = { ...question, type: "multiple-choice" as const };
    expect(getShortcutAnswer(multiple, ["a"], "b")).toEqual(["a", "b"]);
    expect(getShortcutAnswer(multiple, ["a", "b"], "a")).toEqual(["b"]);
  });
});
