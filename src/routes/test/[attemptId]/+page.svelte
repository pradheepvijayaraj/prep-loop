<!--
  Test session page — `/test/[attemptId]`.

  Full-screen timed exam UI. Renders the question card, navigator,
  timer, and submit dialog. Uses the test-session store for all state.
  Auto-submits when the timer expires (if enabled in settings).
  Keyboard shortcuts are attached on mount and cleaned up on destroy.
-->
<script lang="ts">
  import { page } from "$app/state";
  import { goto } from "$app/navigation";
  import { onMount, onDestroy } from "svelte";
  import { Button } from "$lib/components/ui/button";
  import { Dialog } from "$lib/components/ui/dialog";
  import LoadingProgress from "$lib/components/loading-progress.svelte";
  import SessionDialogPanel from "$lib/components/session-dialog-panel.svelte";
  import { toast } from "svelte-sonner";
  import { logError } from "$lib/services/logger";
  import { safeResultReturnTo } from "$lib/services/result-navigation";
  import {
    createSessionKeyboardHandler,
    getShortcutAnswer,
  } from "$lib/services/session-keyboard";
  import { loadSessionWithTimeout } from "$lib/services/session-loader";
  import { submitTest as submitTestService } from "$lib/services/test-session";
  import {
    getTestSessionState,
    goToQuestion,
    nextQuestion,
    previousQuestion,
    saveAnswer,
    toggleCurrentFlag,
    pause,
    resume,
    clearTestSession,
    getNavigationInfo,
    getProgress,
    isTimerExpired,
    setSubmitting,
    flushPendingSaves,
    getCurrentQuestion,
    getAnswer,
    isFlagged,
    initTestSession,
  } from "$lib/stores/test-session.svelte";
  import { getSettings, updateSetting } from "$lib/stores/settings.svelte";
  import SessionWorkspace from "$lib/components/session-workspace.svelte";
  import SessionSummaryGrid from "$lib/components/session-summary-grid.svelte";
  import Timer from "$lib/components/timer.svelte";
  import { isUuid } from "$lib/utils";

  const attemptId = $derived(page.params.attemptId || "");
  const returnTo = $derived(safeResultReturnTo(page.url.searchParams));

  let isLoading = $state(true);
  let isLoadingComplete = $state(false);
  let loadError = $state<string | null>(null);
  let showSubmitDialog = $state(false);
  let navigatorExpanded = $state(false);
  /** Bumped to ignore late load results after cancel / unmount. */
  let loadGeneration = 0;

  // Reactive state from store
  let sessionState = $derived(getTestSessionState());
  let currentQuestion = $derived(getCurrentQuestion());
  let navigation = $derived(getNavigationInfo());
  let progress = $derived(getProgress());
  let settings = $derived(getSettings());

  const handleKeydown = createSessionKeyboardHandler({
    mode: "test",
    isPaused: () => getTestSessionState().isPaused,
    isDialogOpen: () => showSubmitDialog,
    getCurrentQuestion: () => getCurrentQuestion(),
    onNext: nextQuestion,
    onPrevious: previousQuestion,
    onToggleFlag: handleToggleFlag,
    onOpenSubmit: () => {
      showSubmitDialog = true;
    },
    onOptionShortcut: handleOptionShortcut,
    onPause: () => handlePauseChange(pause, "pause"),
    onResume: () => handlePauseChange(resume, "resume"),
  });

  onMount(() => {
    const id = page.params.attemptId || "";
    if (!id || !isUuid(id)) {
      loadError = "Invalid attempt ID";
      isLoading = false;
      return;
    }

    navigatorExpanded = settings.navigatorExpanded;
    void loadTestSession(id);
    window.addEventListener("keydown", handleKeydown);

    return () => {
      window.removeEventListener("keydown", handleKeydown);
    };
  });

  onDestroy(() => {
    loadGeneration += 1;
    // Trigger any in-flight saves to complete. We cannot await in onDestroy,
    // but the promises have captured their own attemptId/questionId closures
    // so they write to the correct place even after state is cleared.
    void flushPendingSaves().catch(() => {});
    clearTestSession();
  });

  async function loadTestSession(id: string) {
    const gen = ++loadGeneration;
    isLoading = true;
    isLoadingComplete = false;
    loadError = null;
    let loaded = false;

    try {
      const result = await loadSessionWithTimeout(id, "test");
      if (gen !== loadGeneration) return;
      if (result.redirectTo) {
        await goto(
          `${result.redirectTo}?returnTo=${encodeURIComponent(returnTo)}`,
        );
        return;
      }

      if (result.error) {
        loadError = result.error;
        return;
      }
      if (result.data) {
        const { attempt, questions, answers, flags } = result.data;
        initTestSession(
          id,
          attempt.bankId,
          "test",
          questions,
          attempt.duration,
          attempt.timeRemaining,
          answers,
          flags,
        );
        loaded = true;
      }
    } catch (error) {
      if (gen !== loadGeneration) return;
      await logError("Failed to load test session", error);
      loadError =
        error instanceof Error ? error.message : "Failed to load test session";
    } finally {
      if (gen === loadGeneration) {
        if (loaded) isLoadingComplete = true;
        else isLoading = false;
      }
    }
  }

  function finishLoading() {
    isLoading = false;
    isLoadingComplete = false;
  }

  async function handleAnswer(answer: string | string[] | null) {
    try {
      await saveAnswer(answer);
    } catch {
      toast.error(
        "Answer could not be saved. Your previous answer was restored.",
      );
    }
  }

  function handleOptionShortcut(optionId: string) {
    if (!currentQuestion) return;
    void handleAnswer(
      getShortcutAnswer(
        currentQuestion,
        getAnswer(currentQuestion.id),
        optionId,
      ),
    );
  }

  async function handleToggleFlag() {
    try {
      await toggleCurrentFlag();
    } catch {
      toast.error("Flag could not be updated.");
    }
  }

  async function handlePauseChange(action: () => Promise<void>, label: string) {
    try {
      await action();
    } catch {
      toast.error(`Could not ${label} the test.`);
    }
  }

  async function handleSubmit() {
    // Guard against double-submit (from button click + timer expiry race)
    if (!sessionState.attemptId || sessionState.isSubmitting) return;

    const submittedAttemptId = sessionState.attemptId;
    setSubmitting(true);
    showSubmitDialog = false;

    try {
      await flushPendingSaves();
      await submitTestService(submittedAttemptId);
      clearTestSession(false);
      toast.success("Test submitted successfully!");
      goto(
        `/results/${submittedAttemptId}?returnTo=${encodeURIComponent(returnTo)}`,
      );
    } catch (error) {
      await logError("Failed to submit test", error);
      toast.error("Failed to submit test");
      setSubmitting(false);
    }
  }

  function toggleNavigator() {
    navigatorExpanded = !navigatorExpanded;
    updateSetting("navigatorExpanded", navigatorExpanded);
  }

  // Auto-submit when timer expires.
  // autoSubmitTriggered prevents: (a) duplicate fires across reactive re-evaluations
  // while timeRemaining ticks at 0, and (b) an infinite retry loop when submit
  // fails and isSubmitting resets to false.
  let autoSubmitTriggered = false;
  $effect(() => {
    if (
      isTimerExpired() &&
      settings.autoSubmitOnTimerEnd &&
      !sessionState.isSubmitting &&
      !autoSubmitTriggered
    ) {
      autoSubmitTriggered = true;
      void handleSubmit();
    }
  });
</script>

<svelte:head>
  <title>Test in Progress - PrepLoop</title>
</svelte:head>

{#if isLoading}
  <LoadingProgress
    class="h-full bg-background"
    complete={isLoadingComplete}
    onComplete={finishLoading}
  />
{:else if loadError}
  <div class="flex h-full items-center justify-center">
    <div class="text-center">
      <h1 class="text-2xl font-bold text-destructive mb-4">Error</h1>
      <p class="text-muted-foreground mb-4">{loadError}</p>
      <div class="flex items-center justify-center gap-3">
        <Button href="/">Back to Dashboard</Button>
        <Button
          variant="outline"
          onclick={() => {
            const id = page.params.attemptId || "";
            if (id && isUuid(id)) void loadTestSession(id);
          }}
        >
          Retry
        </Button>
      </div>
    </div>
  </div>
{:else if sessionState.attemptId}
  <SessionWorkspace
    modeLabel="Test"
    exitLabel="Exit test"
    session={sessionState}
    question={currentQuestion}
    answer={currentQuestion ? getAnswer(currentQuestion.id) : null}
    flagged={currentQuestion ? isFlagged(currentQuestion.id) : false}
    {navigation}
    {progress}
    {navigatorExpanded}
    onAnswer={(answer) => void handleAnswer(answer)}
    onToggleFlag={() => void handleToggleFlag()}
    onNavigate={goToQuestion}
    onToggleNavigator={toggleNavigator}
    onPrevious={previousQuestion}
    onNext={nextQuestion}
    onSubmit={() => (showSubmitDialog = true)}
    onResume={() => void handlePauseChange(resume, "resume")}
  >
    {#snippet headerCenter()}
      <Timer
        timeRemaining={sessionState.timeRemaining}
        totalDuration={sessionState.duration}
        isPaused={sessionState.isPaused}
        onPause={() => void handlePauseChange(pause, "pause")}
        onResume={() => void handlePauseChange(resume, "resume")}
      />
    {/snippet}
  </SessionWorkspace>

  <!-- Submit Confirmation Dialog -->
  <Dialog bind:open={showSubmitDialog}>
    <SessionDialogPanel
      title="SUBMIT ?"
      primaryLabel={sessionState.isSubmitting ? "SUBMITTING..." : "SUBMIT"}
      initialFocus="primary"
      onPrimary={handleSubmit}
      onSecondary={() => (showSubmitDialog = false)}
      primaryDisabled={sessionState.isSubmitting}
      contentClass="max-w-[25rem]"
      headerClass="h-16 px-6"
      dividerClass="mx-6"
      bodyClass="px-6 pt-5 pb-3"
      footerClass="px-6 pt-2 pb-5"
    >
      <SessionSummaryGrid
        answered={progress.answered}
        total={progress.total}
        flagged={progress.flagged}
      />
    </SessionDialogPanel>
  </Dialog>
{/if}
