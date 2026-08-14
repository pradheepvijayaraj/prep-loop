<!-- Review page — `/results/[attemptId]/review`. Per-question review with filter tabs and answer highlighting. -->
<script lang="ts">
  import { page } from "$app/state";
  import { onMount } from "svelte";
  import LoadingProgress from "$lib/components/loading-progress.svelte";
  import { Button } from "$lib/components/ui/button";
  import QuestionFooter from "$lib/components/question-footer.svelte";
  import type { QuestionReviewItem, StoredQuestionBank } from "$lib/types";
  import { toggleFlag as toggleFlagService } from "$lib/services/test-session";
  import { loadResultContext } from "$lib/services/result-loader";
  import { getQuestionReview, filterReviewItems } from "$lib/services/scoring";
  import { logError } from "$lib/services/logger";
  import { withLoadingTimeout } from "$lib/services/loading-timeout";
  import { safeResultReturnTo } from "$lib/services/result-navigation";
  import { cn, isUuid } from "$lib/utils";
  import QuestionCard from "$lib/components/question-card.svelte";
  import QuestionNavigator from "$lib/components/question-navigator.svelte";

  type ReviewFilter = "all" | "correct" | "wrong" | "unanswered";

  const reviewFilters: Array<{ value: ReviewFilter; label: string }> = [
    { value: "all", label: "All" },
    { value: "correct", label: "Correct" },
    { value: "wrong", label: "Wrong" },
    { value: "unanswered", label: "Skipped" },
  ];

  const attemptId = $derived(page.params.attemptId || "");

  let isLoading = $state(true);
  let isLoadingComplete = $state(false);
  let loadError = $state<string | null>(null);
  let reviewItems = $state<QuestionReviewItem[]>([]);
  let bank = $state<StoredQuestionBank | null>(null);
  let currentFilter = $state<ReviewFilter>("all");
  let currentIndex = $state(0);
  let navigatorExpanded = $state(false);
  const returnTo = $derived(safeResultReturnTo(page.url.searchParams));
  const resultsHref = $derived.by(
    () => `/results/${attemptId}?returnTo=${encodeURIComponent(returnTo)}`,
  );

  const filteredItems = $derived(filterReviewItems(reviewItems, currentFilter));
  const currentItem = $derived(filteredItems[currentIndex] || null);
  const currentPaperIndex = $derived.by(() =>
    currentItem
      ? reviewItems.findIndex(
          (item) => item.question.id === currentItem.question.id,
        )
      : -1,
  );
  const reviewAnswers = $derived(
    new Map(
      reviewItems
        .filter((item) => item.userAnswer !== null)
        .map(
          (item) =>
            [item.question.id, item.userAnswer] as [string, string | string[]],
        ),
    ),
  );
  const reviewFlags = $derived(
    new Set(
      reviewItems
        .filter((item) => item.isFlagged)
        .map((item) => item.question.id),
    ),
  );

  const counts = $derived({
    all: reviewItems.length,
    correct: reviewItems.filter((i) => i.isCorrect).length,
    wrong: reviewItems.filter((i) => !i.isCorrect && i.userAnswer !== null)
      .length,
    unanswered: reviewItems.filter((i) => i.userAnswer === null).length,
  });

  onMount(() => {
    if (!attemptId || !isUuid(attemptId)) {
      loadError = "Invalid attempt ID";
      isLoading = false;
      return;
    }
    void loadReview();
  });

  async function loadReview() {
    isLoading = true;
    isLoadingComplete = false;
    loadError = null;
    let loaded = false;

    try {
      const { bank: bankInfo } = await withLoadingTimeout(
        loadResultContext(attemptId),
      );
      bank = bankInfo;
      reviewItems = await withLoadingTimeout(getQuestionReview(attemptId));
      loaded = true;
    } catch (error) {
      await logError("Failed to load review", error);
      loadError =
        error instanceof Error ? error.message : "Failed to load review";
    } finally {
      if (loaded) isLoadingComplete = true;
      else isLoading = false;
    }
  }

  function finishLoading() {
    isLoading = false;
    isLoadingComplete = false;
  }

  function handleFilterChange(filter: ReviewFilter) {
    if (currentFilter === filter) return;
    currentIndex = 0;
    currentFilter = filter;
  }

  function goToNext() {
    if (currentIndex < filteredItems.length - 1) {
      currentIndex++;
    }
  }

  function goToPrevious() {
    if (currentIndex > 0) {
      currentIndex--;
    }
  }

  function goToQuestion(index: number) {
    if (index >= 0 && index < filteredItems.length) {
      currentIndex = index;
    }
  }

  function getFilterCount(filter: ReviewFilter) {
    return counts[filter];
  }

  function toggleNavigator() {
    navigatorExpanded = !navigatorExpanded;
  }

  async function toggleReviewFlag() {
    if (!currentItem) return;
    try {
      const nextFlagged = await toggleFlagService(
        attemptId,
        currentItem.question.id,
      );
      reviewItems = reviewItems.map((item) =>
        item.question.id === currentItem.question.id
          ? { ...item, isFlagged: nextFlagged }
          : item,
      );
    } catch (error) {
      await logError("Failed to toggle review flag", error);
    }
  }
</script>

<svelte:head>
  <title>Review - PrepLoop</title>
</svelte:head>

<div class="h-full flex flex-col overflow-hidden bg-background">
  {#if isLoading}
    <LoadingProgress
      class="flex-1"
      complete={isLoadingComplete}
      onComplete={finishLoading}
    />
  {:else if loadError}
    <div class="flex flex-1 items-center justify-center">
      <div class="text-center">
        <h1 class="mb-4 text-2xl font-bold text-destructive">
          Couldn&apos;t Load Review
        </h1>
        <p class="mb-6 text-muted-foreground">{loadError}</p>
        <Button href={resultsHref}>Back to Results</Button>
      </div>
    </div>
  {:else}
    <!-- Header -->
    <div class="z-10 border-b border-border/22 bg-background">
      <div
        class="flex flex-wrap items-center justify-between gap-4 pl-6 pr-5 py-5 md:pl-9 md:pr-8 lg:pl-11 lg:pr-10 xl:pl-12 xl:pr-12 2xl:px-14"
      >
        <div
          class="text-xs font-bold uppercase tracking-[0.16em] text-muted-foreground/75"
        >
          Review
        </div>

        <div class="flex min-w-0 flex-wrap items-center justify-end gap-1.5">
          {#each reviewFilters as filter}
            <button
              type="button"
              class={cn(
                "box-border inline-flex h-7 min-w-[2.75rem] items-center justify-center rounded-none border bg-clip-padding px-3 py-0 text-[0.66rem] font-semibold leading-none uppercase tracking-[0.12em] whitespace-nowrap [font-variant-numeric:tabular-nums] transition-colors focus-visible:outline-none",
                currentFilter === filter.value
                  ? "border-white/30 bg-white text-black shadow-[inset_0_0_0_1px_rgba(24,24,27,0.16)] hover:border-white/30 hover:bg-white hover:text-black"
                  : "border-white/18 bg-transparent text-foreground/72 hover:border-white/26 hover:bg-muted/16 hover:text-foreground",
              )}
              aria-pressed={currentFilter === filter.value}
              onclick={() => handleFilterChange(filter.value)}
            >
              {filter.label} ({getFilterCount(filter.value)})
            </button>
          {/each}
          <span class="sr-only" aria-live="polite">
            {filteredItems.length} questions shown
          </span>
        </div>
      </div>
    </div>

    <!-- Question Content -->
    <div class="relative z-0 flex min-h-0 flex-1 overflow-hidden">
      <div
        class={`min-h-0 min-w-0 flex-1 overflow-hidden px-6 py-4 pr-14 transition-[padding] duration-200 lg:px-8 lg:py-6 lg:pr-18 ${navigatorExpanded ? "2xl:pr-[22rem]" : ""}`}
      >
        {#if currentItem}
          <QuestionCard
            question={currentItem.question}
            index={currentPaperIndex}
            total={reviewItems.length}
            answer={currentItem.userAnswer}
            isFlagged={currentItem.isFlagged}
            allowTextSelection={true}
            showFeedback={true}
            showTags={true}
            readOnly={true}
            onAnswer={() => {}}
            onToggleFlag={toggleReviewFlag}
          />
        {:else}
          <div class="flex h-full items-center justify-center">
            <p
              class="text-[0.82rem] font-semibold uppercase tracking-[0.12em] text-muted-foreground/74"
            >
              No items
            </p>
          </div>
        {/if}
      </div>
      <QuestionNavigator
        questions={filteredItems.map((item) => item.question)}
        questionNumbers={filteredItems.map(
          (item) =>
            reviewItems.findIndex(
              (paperItem) => paperItem.question.id === item.question.id,
            ) + 1,
        )}
        {currentIndex}
        answers={reviewAnswers}
        flags={reviewFlags}
        expanded={navigatorExpanded}
        onNavigate={goToQuestion}
        onToggleExpand={toggleNavigator}
      />
    </div>

    <!-- Footer Navigation -->
    <div
      class="border-t border-border/22 bg-background pl-6 pr-5 py-5 md:pl-9 md:pr-8 lg:pl-11 lg:pr-10 xl:pl-12 xl:pr-12 2xl:px-14"
    >
      <QuestionFooter
        current={currentPaperIndex + 1}
        total={reviewItems.length}
        canPrevious={currentIndex > 0}
        canNext={currentIndex < filteredItems.length - 1}
        onPrevious={goToPrevious}
        onNext={goToNext}
        previousLabel="Previous review question"
        nextLabel="Next review question"
        class="gap-6"
      >
        {#snippet actions()}
          <Button
            href={resultsHref}
            class="h-10 justify-self-end rounded-md px-4 text-xs font-bold uppercase tracking-[0.14em]"
            >Close</Button
          >
        {/snippet}
      </QuestionFooter>
    </div>
  {/if}
</div>
