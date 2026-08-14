<script lang="ts">
  import type { Question } from "$lib/types";
  import { Button } from "$lib/components/ui/button";
  import { Checkbox } from "$lib/components/ui/checkbox";
  import MathText from "$lib/components/math-text.svelte";
  import { formatMarks } from "$lib/utils";
  import { Flag } from "@lucide/svelte";
  import ScrollIndicator from "$lib/components/scroll-indicator.svelte";

  const BROAD_CATEGORY_TAGS = new Set([
    "Agriculture",
    "Art & Culture",
    "Current Events",
    "Disaster Management",
    "Economy",
    "Environment & Ecology",
    "Ethics, Integrity & Aptitude",
    "Geography",
    "Governance",
    "History",
    "Indian Society",
    "International Relations",
    "Internal Security",
    "Mathematics",
    "Polity & Constitution",
    "Science & Technology",
    "Social Justice",
    "CSAT",
    "Essay & Philosophical Themes",
  ]);

  interface Props {
    question: Question;
    index: number;
    total: number;
    answer: string | string[] | null;
    isFlagged: boolean;
    allowTextSelection?: boolean;
    showFeedback?: boolean;
    showTags?: boolean;
    readOnly?: boolean;
    onAnswer: (answer: string | string[] | null) => void;
    onToggleFlag: () => void;
  }

  let {
    question,
    index,
    total,
    answer,
    isFlagged,
    allowTextSelection = false,
    showFeedback = false,
    showTags = false,
    readOnly = false,
    onAnswer,
    onToggleFlag,
  }: Props = $props();

  let selectedOptions = $state<string[]>([]);
  let textAnswer = $state("");
  let workspaceElement = $state<HTMLElement | null>(null);
  let promptElement = $state<HTMLElement | null>(null);
  let answerElement = $state<HTMLElement | null>(null);
  const displayTags = $derived(
    (question.tags ?? []).filter((tag) => BROAD_CATEGORY_TAGS.has(tag)),
  );

  $effect(() => {
    question.id;

    if (Array.isArray(answer)) {
      selectedOptions = [...answer];
      textAnswer = "";
    } else if (typeof answer === "string") {
      textAnswer = answer;
      selectedOptions = [answer];
    } else {
      selectedOptions = [];
      textAnswer = "";
    }
  });

  $effect(() => {
    question.id;
    promptElement?.scrollTo({ top: 0, behavior: "auto" });
    answerElement?.scrollTo({ top: 0, behavior: "auto" });
  });

  function handleSingleChoice(value: string) {
    if (selectedOptions.includes(value)) {
      selectedOptions = [];
      onAnswer(null);
      return;
    }

    selectedOptions = [value];
    onAnswer(value);
  }

  function handleMultipleChoice(optionId: string, checked: boolean) {
    let nextSelected: string[];

    if (checked) {
      nextSelected = [...new Set([...selectedOptions, optionId])];
    } else {
      nextSelected = selectedOptions.filter((id) => id !== optionId);
    }

    selectedOptions = nextSelected;
    onAnswer(nextSelected.length > 0 ? nextSelected : null);
  }

  function handleTextInput(value: string) {
    textAnswer = value;
    onAnswer(value.trim() || null);
  }

  function isCorrectAnswer(optionId: string): boolean {
    return question.correctAnswers.includes(optionId);
  }

  function getOptionClass(optionId: string): string {
    if (!showFeedback) return "";

    const isSelected = selectedOptions.includes(optionId);
    const isCorrect = isCorrectAnswer(optionId);

    if (isCorrect) return "border-chart-2 bg-chart-2/5";
    if (isSelected && !isCorrect) return "border-destructive bg-destructive/5";
    return "";
  }
</script>

<div
  class="question-card flex h-full min-h-0 w-full min-w-0 max-w-none flex-col"
>
  <div class="flex items-start justify-between gap-4 pb-6">
    <div class="space-y-1">
      <div
        class="flex items-center gap-1.5 text-xs font-bold uppercase tracking-[0.16em] text-muted-foreground/75"
      >
        <span>{question.type}</span>
      </div>
      <div class="flex items-center gap-3 text-xs font-bold tracking-widest">
        <span class="text-chart-2">+{formatMarks(question.marks)}</span>
        {#if question.negativeMarks > 0}
          <span class="text-destructive"
            >-{formatMarks(question.negativeMarks)}</span
          >
        {/if}
      </div>
      {#if showTags && displayTags.length}
        <div class="mt-3 flex flex-wrap gap-1.5">
          {#each displayTags as tag}
            <span
              class="rounded-none border border-border/35 px-2 py-1 text-[0.62rem] font-semibold uppercase tracking-[0.12em] text-muted-foreground/80"
              >{tag}</span
            >
          {/each}
        </div>
      {/if}
    </div>
    <Button
      variant="ghost"
      size="icon"
      onclick={onToggleFlag}
      aria-label={isFlagged ? "Unflag question" : "Flag question"}
      title={isFlagged ? "Flagged" : "Flag question"}
      class="h-9 w-9 rounded-full transition-[background-color,border-color,color,box-shadow,transform] {isFlagged
        ? 'border-flag/35 bg-flag/12 text-flag shadow-sm'
        : 'text-muted-foreground/70 hover:text-foreground/85'}"
    >
      <Flag class="h-4 w-4" />
    </Button>
  </div>

  <div class="relative min-h-0 flex-1">
    <div bind:this={workspaceElement} class="question-card__workspace">
      <div class="question-card__column question-card__column--prompt">
        <section
          bind:this={promptElement}
          class="question-card__pane question-card__pane--prompt"
        >
          {#key `prompt-${question.id}`}
            <div class="question-card__content-enter">
              <div
                class={`question-card__question whitespace-pre-wrap ${allowTextSelection ? "select-text" : ""}`}
              >
                <MathText text={question.question} />
              </div>
            </div>
          {/key}
        </section>
        <ScrollIndicator
          scroller={promptElement}
          updateTrigger={question.id}
          right={2}
          insetY={0}
        />
      </div>

      <div class="question-card__column question-card__column--answer">
        <section
          bind:this={answerElement}
          class="question-card__pane question-card__pane--answer"
        >
          {#key `answer-${question.id}`}
            <div class="question-card__content-enter">
              <div class="answer-panel">
                {#if question.type === "single-choice" || question.type === "true-false"}
                  <div class="space-y-2.5">
                    {#each question.options || [] as option}
                      {@const isSelected = selectedOptions.includes(option.id)}
                      <button
                        type="button"
                        class="group answer-option w-full text-left {showFeedback
                          ? getOptionClass(option.id)
                          : isSelected
                            ? 'answer-option--selected'
                            : 'answer-option--idle'}"
                        onclick={() => handleSingleChoice(option.id)}
                        disabled={readOnly}
                        aria-pressed={isSelected}
                      >
                        <div class="answer-option__leading">
                          <div
                            class="answer-option__control {isSelected
                              ? 'answer-option__control--selected'
                              : 'answer-option__control--idle'}"
                          >
                            <div
                              class="answer-option__control-dot {isSelected
                                ? 'answer-option__control-dot--visible'
                                : ''}"
                            ></div>
                          </div>
                        </div>
                        <div
                          class={`answer-option__text ${allowTextSelection ? "select-text" : ""}`}
                        >
                          <MathText text={option.text} />
                        </div>
                        {#if showFeedback && isCorrectAnswer(option.id)}
                          <div class="answer-option__feedback-dot"></div>
                        {/if}
                      </button>
                    {/each}
                  </div>
                {:else if question.type === "multiple-choice"}
                  <div class="space-y-2.5">
                    {#each question.options || [] as option}
                      <div
                        class="group answer-option {showFeedback
                          ? getOptionClass(option.id)
                          : selectedOptions.includes(option.id)
                            ? 'answer-option--selected'
                            : 'answer-option--idle'}"
                      >
                        <div class="answer-option__leading">
                          <Checkbox
                            id={`option-${question.id}-${option.id}`}
                            checked={selectedOptions.includes(option.id)}
                            onCheckedChange={(checked) =>
                              handleMultipleChoice(option.id, !!checked)}
                            disabled={readOnly}
                            class="h-4 w-4 border-2"
                          />
                        </div>
                        <label
                          for={`option-${question.id}-${option.id}`}
                          class={`answer-option__text cursor-pointer ${allowTextSelection ? "select-text" : ""}`}
                        >
                          <MathText text={option.text} />
                        </label>
                        {#if showFeedback && isCorrectAnswer(option.id)}
                          <div class="answer-option__feedback-dot"></div>
                        {/if}
                      </div>
                    {/each}
                  </div>
                {:else if question.type === "fill-blank" || question.type === "numerical"}
                  {@const isOpenEnded =
                    question.correctAnswers[0] === "__open__"}
                  <div class="space-y-4">
                    {#if isOpenEnded}
                      <div
                        class="answer-option answer-option--input items-start"
                      >
                        <div
                          class="answer-option__leading answer-option__leading--spacer"
                          aria-hidden="true"
                        ></div>
                        <textarea
                          id="answer"
                          value={textAnswer}
                          oninput={(e) =>
                            handleTextInput(e.currentTarget.value)}
                          disabled={readOnly}
                          placeholder="Draft your answer (practice notes only)"
                          rows="8"
                          class="answer-option__input min-h-[10rem] resize-y"
                        ></textarea>
                      </div>
                    {:else}
                      <div class="answer-option answer-option--input">
                        <div
                          class="answer-option__leading answer-option__leading--spacer"
                          aria-hidden="true"
                        ></div>
                        <input
                          id="answer"
                          type={question.type === "numerical"
                            ? "number"
                            : "text"}
                          value={textAnswer}
                          oninput={(e) =>
                            handleTextInput(e.currentTarget.value)}
                          disabled={readOnly}
                          placeholder="Answer"
                          class="answer-option__input"
                        />
                      </div>
                      {#if showFeedback}
                        <div class="answer-panel__feedback-card">
                          <span
                            class="text-[0.7rem] font-bold uppercase tracking-[0.18em] text-muted-foreground/70"
                            >Correct Answer</span
                          >
                          <span class="text-lg font-semibold text-chart-2"
                            >{question.correctAnswers[0]}</span
                          >
                        </div>
                      {/if}
                    {/if}
                  </div>
                {/if}

                {#if showFeedback && question.explanation}
                  <div class="answer-panel__feedback-card border-t-0 pt-0">
                    <p
                      class="text-[0.7rem] font-bold uppercase tracking-[0.18em] text-muted-foreground/70"
                    >
                      Explanation
                    </p>
                    <p
                      class="max-w-2xl text-base leading-relaxed text-muted-foreground/82"
                    >
                      {question.explanation}
                    </p>
                  </div>
                {/if}
              </div>
            </div>
          {/key}
        </section>
      </div>
    </div>
    <ScrollIndicator scroller={workspaceElement} updateTrigger={question.id} />
  </div>
</div>

<style>
  .question-card__workspace {
    display: flex;
    min-height: 0;
    flex: 1;
    flex-direction: column;
    gap: 1.25rem;
    overflow-y: auto;
    scrollbar-width: none;
    -ms-overflow-style: none;
  }

  .question-card__workspace::-webkit-scrollbar,
  .question-card__pane::-webkit-scrollbar {
    display: none;
  }

  .question-card__pane {
    min-height: 0;
    min-width: 0;
    flex: 1 1 auto;
    scrollbar-width: none;
    -ms-overflow-style: none;
  }

  .question-card__column {
    position: relative;
    display: flex;
    flex-direction: column;
    min-height: 0;
    min-width: 0;
    overflow: hidden;
  }

  .question-card__pane--prompt {
    padding-bottom: 1.25rem;
    border-bottom: 1px solid color-mix(in oklab, var(--border) 82%, transparent);
  }

  .question-card__pane--answer {
    padding-top: 0.25rem;
  }

  .question-card__question {
    max-width: min(52ch, 100%);
    font-size: clamp(0.98rem, 0.94rem + 0.18vw, 1.12rem);
    font-weight: 500;
    line-height: 1.55;
    letter-spacing: -0.02em;
    color: color-mix(in oklab, var(--foreground) 92%, transparent);
  }

  .question-card__content-enter {
    animation: question-card-content-swap 160ms cubic-bezier(0.22, 1, 0.36, 1);
    will-change: opacity, transform;
  }

  .answer-panel {
    display: flex;
    min-height: 0;
    flex: 1;
    flex-direction: column;
    gap: 0.9rem;
  }

  .answer-option {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr) auto;
    align-items: start;
    gap: 0.9rem;
    border: 1px solid color-mix(in oklab, var(--border) 74%, transparent);
    background: color-mix(in oklab, var(--background) 97%, var(--card));
    padding: 0.95rem 1rem;
    transition:
      border-color 0.18s ease,
      background 0.18s ease;
  }

  .answer-option:hover {
    border-color: color-mix(in oklab, var(--foreground) 18%, var(--border));
    background: color-mix(in oklab, var(--background) 93%, var(--muted));
  }

  .answer-option--idle {
    background: color-mix(in oklab, var(--background) 97%, var(--card));
  }

  .answer-option--selected {
    border-color: color-mix(in oklab, var(--foreground) 22%, var(--border));
    background: color-mix(in oklab, var(--background) 88%, var(--muted));
    box-shadow:
      0 0 0 1px rgba(255, 255, 255, 0.08) inset,
      0 0 18px rgba(255, 255, 255, 0.08);
  }

  .answer-option__leading {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    /* Sit with the first line of option text (grid is items-start) */
    padding-top: 0.28rem;
  }

  .answer-option__leading--spacer {
    width: 1rem;
    flex-shrink: 0;
  }

  .answer-option__control {
    display: flex;
    height: 1rem;
    width: 1rem;
    flex-shrink: 0;
    align-items: center;
    justify-content: center;
    border-radius: 999px;
    border: 2px solid currentColor;
    transition:
      color 0.18s ease,
      border-color 0.18s ease;
  }

  .answer-option__control--idle {
    color: color-mix(in oklab, var(--muted-foreground) 78%, transparent);
  }

  .answer-option__control--selected {
    color: color-mix(in oklab, var(--foreground) 92%, transparent);
  }

  .answer-option__control-dot {
    height: 0.45rem;
    width: 0.45rem;
    border-radius: 999px;
    background: currentColor;
    opacity: 0;
    transform: scale(0.55);
    transition:
      opacity 0.18s ease,
      transform 0.18s ease;
  }

  .answer-option__control-dot--visible {
    opacity: 1;
    transform: scale(1);
  }

  .answer-option__text {
    min-width: 0;
    padding: 0.1rem 0;
    font-size: clamp(0.95rem, 0.92rem + 0.12vw, 1.05rem);
    font-weight: 500;
    line-height: 1.42;
    letter-spacing: -0.015em;
    color: color-mix(in oklab, var(--foreground) 95%, transparent);
  }

  .answer-option__feedback-dot {
    height: 0.55rem;
    width: 0.55rem;
    margin-top: 0.4rem;
    border-radius: 999px;
    background: var(--chart-2);
  }

  .answer-option--input {
    align-items: stretch;
  }

  .answer-option__input {
    width: 100%;
    height: 100%;
    min-height: calc(1.42em + 0.2rem);
    border: 0;
    outline: none;
    background: transparent;
    border: 0;
    padding: 0.1rem 0;
    font-size: clamp(1.02rem, 0.95rem + 0.22vw, 1.2rem);
    font-weight: 500;
    line-height: 1.42;
    letter-spacing: -0.02em;
    color: color-mix(in oklab, var(--foreground) 95%, transparent);
    box-shadow: none;
    appearance: none;
    -webkit-appearance: none;
    -moz-appearance: textfield;
  }

  .answer-option__input::placeholder {
    color: color-mix(in oklab, var(--muted-foreground) 74%, transparent);
  }

  .answer-option__input:focus-visible {
    outline: none;
    box-shadow: none;
  }

  .answer-option__input::-webkit-outer-spin-button,
  .answer-option__input::-webkit-inner-spin-button {
    margin: 0;
    -webkit-appearance: none;
  }

  .answer-panel__feedback-card {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    border-top: 1px solid color-mix(in oklab, var(--border) 74%, transparent);
    padding-top: 1rem;
  }

  @keyframes question-card-content-swap {
    from {
      opacity: 0;
      transform: translate3d(0, 6px, 0);
    }

    to {
      opacity: 1;
      transform: translate3d(0, 0, 0);
    }
  }

  @media (min-width: 1100px) {
    .question-card__workspace {
      position: absolute;
      inset: 0;
      display: grid;
      grid-template-columns: minmax(0, 60%) minmax(22rem, 40%);
      gap: 2rem;
      overflow: hidden;
    }

    .question-card__pane {
      overflow-y: auto;
      overscroll-behavior: contain;
      scrollbar-gutter: stable;
    }

    .question-card__column--prompt {
      border-right: 1px solid
        color-mix(in oklab, var(--foreground) 22%, var(--border));
    }

    .question-card__pane--prompt {
      padding-right: 2rem;
      padding-bottom: 0;
      border-right: 0;
      border-bottom: 0;
    }

    .question-card__pane--answer {
      min-height: 0;
      padding-left: 0.25rem;
      padding-right: 0;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .question-card__content-enter {
      animation: none;
    }
  }
</style>
