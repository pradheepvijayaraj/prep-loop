<script lang="ts">
  import type { Snippet } from "svelte";
  import type { Question, TestSessionState } from "$lib/types";
  import { Button } from "$lib/components/ui/button";
  import QuestionCard from "$lib/components/question-card.svelte";
  import QuestionFooter from "$lib/components/question-footer.svelte";
  import QuestionNavigator from "$lib/components/question-navigator.svelte";
  import { X } from "@lucide/svelte";

  interface Props {
    modeLabel: string;
    exitLabel: string;
    session: TestSessionState;
    question: Question | null;
    answer: string | string[] | null;
    flagged: boolean;
    navigation: { canNext: boolean; canPrevious: boolean };
    progress: { total: number };
    navigatorExpanded: boolean;
    showFeedback?: boolean;
    allowTextSelection?: boolean;
    showTags?: boolean;
    onAnswer: (answer: string | string[] | null) => void;
    onToggleFlag: () => void;
    onNavigate: (index: number) => void;
    onToggleNavigator: () => void;
    onPrevious: () => void;
    onNext: () => void;
    onSubmit: () => void;
    onResume?: () => void;
    headerCenter: Snippet;
  }

  let {
    modeLabel,
    exitLabel,
    session,
    question,
    answer,
    flagged,
    navigation,
    progress,
    navigatorExpanded,
    showFeedback = false,
    allowTextSelection = false,
    showTags = false,
    onAnswer,
    onToggleFlag,
    onNavigate,
    onToggleNavigator,
    onPrevious,
    onNext,
    onSubmit,
    onResume,
    headerCenter,
  }: Props = $props();
</script>

<div
  class="fixed inset-0 z-[60] flex h-dvh max-h-dvh flex-col overflow-hidden bg-background"
>
  <header
    class="relative flex h-14 shrink-0 items-center justify-between border-b px-6"
  >
    <div
      class="text-xs font-bold uppercase tracking-[0.16em] text-muted-foreground/75"
    >
      {modeLabel}
    </div>
    <div class="absolute left-1/2 -translate-x-1/2">
      {@render headerCenter()}
    </div>
    <Button
      variant="ghost"
      size="icon-sm"
      class="rounded-full border border-transparent text-muted-foreground/70 transition-colors hover:border-border hover:text-foreground"
      onclick={onSubmit}
      aria-label={exitLabel}
      title={exitLabel}
    >
      <X class="h-4 w-4" />
    </Button>
  </header>

  <div class="relative min-h-0 flex-1">
    <div class="flex h-full min-h-0 flex-col">
      <div
        class="relative flex min-h-0 flex-1 overflow-hidden transition-[filter,opacity] duration-200 {session.isPaused
          ? 'pointer-events-none select-none blur-sm opacity-35'
          : ''}"
      >
        <div
          class={`min-h-0 min-w-0 flex-1 overflow-hidden px-6 py-4 pr-14 transition-[padding] duration-200 lg:px-8 lg:py-6 lg:pr-18 ${navigatorExpanded ? "2xl:pr-[22rem]" : ""}`}
        >
          {#if question}
            <QuestionCard
              {question}
              index={session.currentIndex}
              total={session.questions.length}
              {answer}
              isFlagged={flagged}
              {showFeedback}
              {allowTextSelection}
              {showTags}
              {onAnswer}
              {onToggleFlag}
            />
          {/if}
        </div>
        <QuestionNavigator
          questions={session.questions}
          currentIndex={session.currentIndex}
          answers={session.answers}
          flags={session.flags}
          expanded={navigatorExpanded}
          {onNavigate}
          onToggleExpand={onToggleNavigator}
        />
      </div>

      <footer
        class="shrink-0 border-t bg-background/95 px-4 py-4 backdrop-blur-xl transition-[filter,opacity] duration-200 {session.isPaused
          ? 'pointer-events-none select-none blur-sm opacity-35'
          : ''}"
      >
        <QuestionFooter
          current={session.currentIndex + 1}
          total={progress.total}
          canPrevious={navigation.canPrevious && !session.isPaused}
          canNext={navigation.canNext && !session.isPaused}
          {onPrevious}
          {onNext}
        >
          {#snippet actions()}<Button
              variant="default"
              class="h-10 justify-self-end rounded-md px-4 text-xs font-bold uppercase tracking-[0.14em]"
              onclick={onSubmit}
              disabled={session.isPaused}>Submit</Button
            >{/snippet}
        </QuestionFooter>
      </footer>
    </div>

    {#if session.isPaused && onResume}
      <div
        class="absolute inset-0 z-[80] flex items-center justify-center bg-background/55 backdrop-blur-sm"
      >
        <div
          class="app-surface-enter relative flex h-40 w-40 items-center justify-center text-center"
          style="--enter-delay: 20ms;"
        >
          <h2
            class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-[5.1rem] whitespace-nowrap text-[0.95rem] font-bold uppercase tracking-[0.2em] leading-none text-foreground/90"
          >
            Test Paused
          </h2>
          <Button
            variant="outline"
            size="icon"
            class="h-[4.25rem] w-[4.25rem] rounded-full"
            onclick={onResume}
            aria-label="Resume test"
            title="Resume test"
          >
            <span
              class="block h-9 w-9 translate-x-[2px] bg-current"
              style="clip-path: polygon(18% 10%, 18% 90%, 88% 50%);"
              aria-hidden="true"
            ></span>
          </Button>
        </div>
      </div>
    {/if}
  </div>
</div>
