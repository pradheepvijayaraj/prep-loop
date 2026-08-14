<!-- Results page — `/results/[attemptId]`. Shows score, stats, category breakdown, and action buttons (Review/Retake/Done). -->
<script lang="ts">
  import { page } from "$app/state";
  import { goto } from "$app/navigation";
  import { onMount } from "svelte";
  import { Button } from "$lib/components/ui/button";
  import LoadingProgress from "$lib/components/loading-progress.svelte";
  import { toast } from "svelte-sonner";
  import type { TestMode, TestResult, StoredQuestionBank } from "$lib/types";
  import { createTestAttempt } from "$lib/services/test-session";
  import { loadResultContext } from "$lib/services/result-loader";
  import { calculateTestResult } from "$lib/services/scoring";
  import { logError } from "$lib/services/logger";
  import { withLoadingTimeout } from "$lib/services/loading-timeout";
  import { safeResultReturnTo } from "$lib/services/result-navigation";
  import {
    formatMarks,
    formatSignedMarks,
    formatTime,
    isUuid,
  } from "$lib/utils";
  import ScrollIndicator from "$lib/components/scroll-indicator.svelte";

  const attemptId = $derived(page.params.attemptId || "");

  let isLoading = $state(true);
  let isLoadingComplete = $state(false);
  let loadError = $state<string | null>(null);
  let result = $state<TestResult | null>(null);
  let bank = $state<StoredQuestionBank | null>(null);
  let mode = $state<TestMode>("test");
  let resultsScrollElement = $state<HTMLElement | null>(null);
  let isRetaking = $state(false);
  const returnTo = $derived(safeResultReturnTo(page.url.searchParams));
  const reviewHref = $derived.by(
    () =>
      `/results/${attemptId}/review?returnTo=${encodeURIComponent(returnTo)}`,
  );

  onMount(() => {
    if (!attemptId || !isUuid(attemptId)) {
      loadError = "Invalid attempt ID";
      isLoading = false;
      return;
    }
    void loadResults();
  });

  async function loadResults() {
    isLoading = true;
    isLoadingComplete = false;
    loadError = null;
    let loaded = false;

    try {
      const { attempt, bank: bankInfo } = await withLoadingTimeout(
        loadResultContext(attemptId),
      );
      mode = attempt.mode;
      bank = bankInfo;
      result = await withLoadingTimeout(calculateTestResult(attempt.id));
      loaded = true;
    } catch (error) {
      await logError("Failed to load results", error);
      loadError =
        error instanceof Error ? error.message : "Failed to load results";
    } finally {
      if (loaded) isLoadingComplete = true;
      else isLoading = false;
    }
  }

  function finishLoading() {
    isLoading = false;
    isLoadingComplete = false;
  }

  async function handleRetake() {
    if (!bank || isRetaking) return;

    isRetaking = true;
    try {
      const newAttemptId = await createTestAttempt(bank.id, mode);
      goto(
        mode === "practice"
          ? `/practice/${newAttemptId}`
          : `/test/${newAttemptId}`,
      );
    } catch (error) {
      await logError("Failed to retake test", error);
      toast.error("Failed to start retake");
      isRetaking = false;
    }
  }
</script>

<svelte:head>
  <title>Results - PrepLoop</title>
</svelte:head>

{#if isLoading}
  <LoadingProgress
    class="mx-auto h-full max-w-4xl px-6 py-8"
    complete={isLoadingComplete}
    onComplete={finishLoading}
  />
{:else if loadError}
  <div
    class="mx-auto flex h-full max-w-4xl items-center justify-center px-6 py-8"
  >
    <div class="text-center">
      <h1 class="mb-4 text-2xl font-bold text-destructive">
        Couldn&apos;t Load Results
      </h1>
      <p class="mb-6 text-muted-foreground">{loadError}</p>
      <Button href="/">Back Home</Button>
    </div>
  </div>
{:else if result}
  <div
    class="mx-auto flex h-full max-w-[54rem] flex-col overflow-hidden px-6 py-[1.875rem]"
  >
    <!-- Header -->
    <div
      class="app-surface-enter mb-9 space-y-3 text-center"
      style="--enter-delay: 30ms;"
    >
      {#if bank}
        <div
          class="text-[0.96rem] font-semibold tracking-[0.06em] text-muted-foreground/78"
        >
          {bank.name}
        </div>
      {/if}
      <div
        class={`text-[clamp(4rem,6vw,5rem)] font-black leading-none tabular-nums ${
          result.score < 0 ? "tracking-normal" : "tracking-[-0.035em]"
        }`}
      >
        {formatMarks(result.score)}
      </div>
      <div
        class="text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground/75"
      >
        OUT OF {formatMarks(result.maxScore)} MARKS
      </div>
    </div>

    <!-- Simple Stats Row -->
    <div
      class="app-surface-enter grid grid-cols-2 gap-6 border-y border-muted/30 py-7 md:grid-cols-4"
      style="--enter-delay: 75ms;"
    >
      <div class="text-center space-y-1">
        <div class="text-[1.65rem] font-bold tracking-[-0.02em]">
          {result.correct}
        </div>
        <div
          class="text-[0.69rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground/70"
        >
          Correct
        </div>
      </div>

      <div class="text-center space-y-1">
        <div class="text-[1.65rem] font-bold tracking-[-0.02em]">
          {result.wrong}
        </div>
        <div
          class="text-[0.69rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground/70"
        >
          Wrong
        </div>
      </div>

      <div class="text-center space-y-1">
        <div class="text-[1.65rem] font-bold tracking-[-0.02em]">
          {result.unanswered}
        </div>
        <div
          class="text-[0.69rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground/70"
        >
          Skipped
        </div>
      </div>

      <div class="text-center space-y-1">
        <div class="text-[1.65rem] font-bold tracking-[-0.02em]">
          {formatTime(result.timeTaken)}
        </div>
        <div
          class="text-[0.69rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground/70"
        >
          Time
        </div>
      </div>
    </div>

    <!-- Category Breakdown -->
    <div
      class="app-surface-enter min-h-0 flex-1 py-7"
      style="--enter-delay: 115ms;"
    >
      {#if result.categoryBreakdown && result.categoryBreakdown.length > 0}
        <div class="mx-auto flex h-full max-w-[36.25rem] flex-col gap-5">
          <div
            class="mr-9 grid grid-cols-[minmax(0,1fr)_3.1rem_3.1rem] items-center gap-3 border-b border-muted/30 pb-3 text-[0.69rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground/75"
          >
            <span>Breakdown</span>
            <span class="justify-self-end text-right text-chart-2">+</span>
            <span class="justify-self-end text-right text-destructive">-</span>
          </div>
          <div class="relative min-h-0 flex-1 overflow-hidden">
            <div
              bind:this={resultsScrollElement}
              class="absolute inset-0 overflow-y-auto pr-9 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
            >
              <div class="divide-y divide-muted/30">
                {#each result.categoryBreakdown as category}
                  <div
                    class="grid grid-cols-[minmax(0,1fr)_3.1rem_3.1rem] items-center gap-3 py-[0.92rem]"
                  >
                    <span
                      class="min-w-0 text-[0.96rem] font-medium tracking-[0.01em] text-foreground/92"
                    >
                      {category.category}
                    </span>
                    <span
                      class="justify-self-end text-right text-[0.96rem] font-semibold tabular-nums text-chart-2"
                    >
                      {formatSignedMarks(category.positiveMarks, "+")}
                    </span>
                    <span
                      class="justify-self-end text-right text-[0.96rem] font-semibold tabular-nums text-destructive"
                    >
                      {formatSignedMarks(category.negativeMarks, "-")}
                    </span>
                  </div>
                {/each}
              </div>
            </div>
            <ScrollIndicator
              scroller={resultsScrollElement}
              right={11}
              updateTrigger={result?.categoryBreakdown}
            />
          </div>
        </div>
      {:else}
        <div class="flex h-full items-center justify-center">
          <div class="space-y-3 text-center">
            <div class="ui-small-label text-muted-foreground/75">Marks</div>
            <div
              class="text-[2.85rem] font-black tracking-[-0.03em] tabular-nums text-foreground"
            >
              {formatMarks(result.score)} / {formatMarks(result.maxScore)}
            </div>
          </div>
        </div>
      {/if}
    </div>

    <!-- Action Buttons -->
    <div
      class="app-surface-enter flex flex-col items-center justify-center gap-3 pt-[1.375rem] sm:flex-row"
      style="--enter-delay: 150ms;"
    >
      <Button
        href={reviewHref}
        size="sm"
        class="ui-button-text h-10 w-full rounded-none px-4 sm:w-[8.75rem]"
      >
        Review
      </Button>
      {#if bank}
        <Button
          onclick={handleRetake}
          disabled={isRetaking}
          variant="outline"
          size="sm"
          class="ui-button-text h-10 w-full rounded-none border-border/45 px-4 sm:w-[8.75rem]"
        >
          {isRetaking ? "Starting..." : "Retake"}
        </Button>
      {/if}
      <Button
        href={returnTo}
        variant="outline"
        size="sm"
        class="ui-button-text h-10 w-full rounded-none border-border/45 px-4 sm:w-[8.75rem]"
      >
        Done
      </Button>
    </div>
  </div>
{/if}
