<script lang="ts">
  import type { Question } from "$lib/types";
  import { Button } from "$lib/components/ui/button";
  import { ChevronLeft, ChevronRight } from "@lucide/svelte";
  import ScrollIndicator from "$lib/components/scroll-indicator.svelte";

  interface Props {
    questions: Question[];
    /** Original paper numbers to show when this navigator is filtered. */
    questionNumbers?: number[];
    currentIndex: number;
    answers: Map<string, string | string[]>;
    flags: Set<string>;
    expanded?: boolean;
    onNavigate: (index: number) => void;
    onToggleExpand?: () => void;
  }

  let {
    questions,
    questionNumbers = [],
    currentIndex,
    answers,
    flags,
    expanded = false,
    onNavigate,
    onToggleExpand,
  }: Props = $props();

  const navigatorTileCount = $derived(questions.length);
  const navigatorTileIndexes = $derived(
    Array.from({ length: navigatorTileCount }, (_, index) => index),
  );

  const answeredCount = $derived(answers.size);
  const unansweredCount = $derived(
    Math.max(questions.length - answers.size, 0),
  );
  const flaggedCount = $derived(flags.size);
  let navigatorScrollElement = $state<HTMLDivElement | null>(null);

  function getQuestionState(
    index: number,
  ): "current" | "answered" | "unanswered" {
    const question = questions[index];
    if (!question) return "unanswered";

    if (index === currentIndex) return "current";
    if (answers.has(question.id)) return "answered";
    return "unanswered";
  }

  function isFlagged(index: number): boolean {
    const question = questions[index];
    return question ? flags.has(question.id) : false;
  }

  function questionNumber(index: number): number {
    return questionNumbers[index] ?? index + 1;
  }

  function getIndicatorClass(
    state: "current" | "answered" | "unanswered",
    flagged = false,
  ): string {
    return `relative flex items-center justify-center rounded-none border text-sm font-black tracking-tight shadow-[var(--button-shadow-rest)] transition-[background-color,border-color,color,box-shadow,transform] active:translate-y-px active:shadow-[var(--button-shadow-pressed)]
			${
        state === "current"
          ? "border-foreground bg-foreground text-background shadow-[0_12px_24px_rgba(0,0,0,0.16)]"
          : state === "answered"
            ? "border-chart-2/30 bg-chart-2/10 text-chart-2 hover:border-chart-2/45 hover:bg-chart-2/14"
            : "border-[var(--button-border)] bg-[var(--button-surface)] text-muted-foreground hover:border-[var(--button-border-strong)] hover:bg-[var(--button-surface-hover)] hover:text-foreground"
      } ${flagged && state !== "current" ? "navigator-flagged" : ""}`;
  }
</script>

{#if expanded && onToggleExpand}
  <button
    type="button"
    class="question-navigator__backdrop fixed inset-0 z-[69]"
    aria-label="Close question navigator"
    onclick={onToggleExpand}
  ></button>
{/if}

<div class="pointer-events-none absolute inset-y-0 right-0 z-[70]">
  <div
    aria-hidden={!expanded}
    class={`question-navigator__panel flex min-h-0 w-[18.5rem] flex-col border-l border-border/60 bg-background/94 shadow-[-24px_0_40px_rgba(0,0,0,0.14)] backdrop-blur-xl 2xl:w-[20rem] ${expanded ? "question-navigator__panel--open" : ""}`}
  >
    <div class="border-b border-border/60 px-4 py-4 2xl:px-6 2xl:py-5">
      <div class="mb-4 flex items-center justify-between gap-4">
        <span
          class="text-xs font-bold uppercase tracking-[0.16em] text-muted-foreground/75"
          >Questions</span
        >
        {#if onToggleExpand}
          <Button
            variant="ghost"
            size="icon"
            class="h-9 w-9 rounded-none p-0"
            onclick={onToggleExpand}
          >
            <ChevronRight class="h-3 w-3" />
          </Button>
        {/if}
      </div>

      <div
        class="question-navigator__legend"
        aria-label="Question status legend"
      >
        <div class="question-navigator__legend-item">
          <div class="question-navigator__legend-copy">
            <div
              class={`question-navigator__legend-swatch ${getIndicatorClass("answered")}`}
              aria-hidden="true"
            ></div>
            <span
              class="text-xs font-bold uppercase tracking-[0.14em] text-foreground/92"
              >Answered</span
            >
          </div>
          <span class="question-navigator__legend-count">{answeredCount}</span>
        </div>
        <div class="question-navigator__legend-item">
          <div class="question-navigator__legend-copy">
            <div
              class={`question-navigator__legend-swatch ${getIndicatorClass("unanswered")}`}
              aria-hidden="true"
            ></div>
            <span
              class="text-xs font-bold uppercase tracking-[0.14em] text-foreground/92"
              >Unanswered</span
            >
          </div>
          <span class="question-navigator__legend-count">{unansweredCount}</span
          >
        </div>
        <div class="question-navigator__legend-item">
          <div class="question-navigator__legend-copy">
            <div
              class={`question-navigator__legend-swatch ${getIndicatorClass("unanswered", true)}`}
              aria-hidden="true"
            >
              <div
                class="navigator-flag-dot absolute right-1 top-1 h-1.5 w-1.5 rounded-full"
              ></div>
            </div>
            <span
              class="text-xs font-bold uppercase tracking-[0.14em] text-foreground/92"
              >Flagged</span
            >
          </div>
          <span class="question-navigator__legend-count">{flaggedCount}</span>
        </div>
      </div>
    </div>

    <div class="relative min-h-0 flex-1 overflow-hidden">
      <div
        bind:this={navigatorScrollElement}
        class="navigator-grid-scroll absolute inset-0 overflow-y-auto"
      >
        <div
          class="mx-auto grid w-fit grid-cols-[repeat(5,2.5rem)] gap-3 p-3 2xl:grid-cols-[repeat(5,2.75rem)] 2xl:gap-3 2xl:p-3"
        >
          {#each navigatorTileIndexes as index}
            {@const state = getQuestionState(index)}
            {@const flagged = isFlagged(index)}
            {@const isPlaceholder = index >= questions.length}
            <button
              type="button"
              class={`group h-10 w-10 shrink-0 p-0 2xl:h-11 2xl:w-11 ${
                isPlaceholder
                  ? "rounded-none border border-dashed border-border/45 bg-transparent text-muted-foreground/32"
                  : getIndicatorClass(state, flagged)
              }`}
              aria-label={`Question ${questionNumber(index)}${isPlaceholder ? ", placeholder" : flagged ? ", flagged" : ""}`}
              onclick={() => {
                if (!isPlaceholder) onNavigate(index);
              }}
              disabled={isPlaceholder}
            >
              {questionNumber(index)}
              {#if flagged && !isPlaceholder}
                <div
                  class="navigator-flag-dot absolute right-1 top-1 h-1.5 w-1.5 rounded-full"
                ></div>
              {/if}
            </button>
          {/each}
        </div>
      </div>

      <ScrollIndicator
        scroller={navigatorScrollElement}
        updateTrigger={questions}
        right={0}
        insetY={16}
      />
    </div>
  </div>
  {#if onToggleExpand}
    <div
      aria-hidden={expanded}
      class={`question-navigator__toggle ${expanded ? "question-navigator__toggle--hidden" : "question-navigator__toggle--visible"}`}
    >
      <Button
        variant="ghost"
        size="icon"
        class="h-16 w-9 rounded-none border-r-0 p-0 backdrop-blur-sm"
        onclick={onToggleExpand}
      >
        <ChevronLeft class="h-3 w-3" />
      </Button>
    </div>
  {/if}
</div>

<style>
  .question-navigator__panel {
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    opacity: 0;
    pointer-events: none;
    transform: translate3d(16px, 0, 0);
    transition:
      opacity 180ms ease,
      transform 220ms cubic-bezier(0.22, 1, 0.36, 1),
      visibility 0s linear 220ms;
    visibility: hidden;
  }

  .question-navigator__backdrop {
    background: transparent;
  }

  .question-navigator__panel--open {
    opacity: 1;
    pointer-events: auto;
    transform: translate3d(0, 0, 0);
    transition-delay: 0s;
    visibility: visible;
  }

  .question-navigator__toggle {
    position: absolute;
    inset: 0 0 0 auto;
    display: flex;
    align-items: center;
    padding-right: 0.75rem;
    transition:
      opacity 160ms ease,
      transform 180ms cubic-bezier(0.22, 1, 0.36, 1),
      visibility 0s linear 180ms;
  }

  .question-navigator__toggle--visible {
    opacity: 1;
    pointer-events: auto;
    transform: translate3d(0, 0, 0);
    visibility: visible;
  }

  .question-navigator__toggle--hidden {
    opacity: 0;
    pointer-events: none;
    transform: translate3d(10px, 0, 0);
    visibility: hidden;
  }

  .navigator-flagged {
    box-shadow:
      inset 0 0 0 1px color-mix(in oklab, var(--flag) 78%, transparent),
      0 0 0 1px color-mix(in oklab, var(--flag) 28%, transparent),
      0 0 16px color-mix(in oklab, var(--flag) 18%, transparent);
  }

  .question-navigator__legend {
    display: grid;
    border: 1px solid color-mix(in oklab, var(--border) 74%, transparent);
    background: color-mix(in oklab, var(--background) 96%, var(--card));
    padding: 0.7rem 0.75rem;
  }

  .question-navigator__legend-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
  }

  .question-navigator__legend-item + .question-navigator__legend-item {
    margin-top: 0.65rem;
    padding-top: 0.65rem;
    border-top: 1px solid color-mix(in oklab, var(--border) 58%, transparent);
  }

  .question-navigator__legend-copy {
    display: flex;
    min-width: 0;
    align-items: center;
    gap: 0.75rem;
  }

  .question-navigator__legend-count {
    min-width: 2ch;
    font-size: 0.88rem;
    font-weight: 800;
    line-height: 1;
    letter-spacing: -0.015em;
    font-variant-numeric: tabular-nums;
    color: color-mix(in oklab, var(--foreground) 92%, transparent);
  }

  .question-navigator__legend-swatch {
    height: 1.95rem;
    width: 1.95rem;
    flex-shrink: 0;
    pointer-events: none;
  }

  @media (min-width: 1536px) {
    .question-navigator__legend {
      padding: 0.75rem 0.85rem;
    }

    .question-navigator__legend-count {
      font-size: 0.92rem;
    }

    .question-navigator__legend-swatch {
      height: 2.1rem;
      width: 2.1rem;
    }
  }

  .navigator-flag-dot {
    background: var(--flag);
    box-shadow: 0 0 0 3px color-mix(in oklab, var(--flag) 18%, transparent);
  }

  .navigator-grid-scroll {
    scrollbar-width: none;
    -ms-overflow-style: none;
  }

  .navigator-grid-scroll::-webkit-scrollbar {
    display: none;
  }

  @media (prefers-reduced-motion: reduce) {
    .question-navigator__panel,
    .question-navigator__toggle {
      transition: none;
    }
  }
</style>
