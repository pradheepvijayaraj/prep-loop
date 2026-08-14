<!-- Practice session page — `/practice/[attemptId]`. Untimed session with optional immediate answer feedback. -->
<script lang="ts">
  import { page } from "$app/state";
  import { goto } from "$app/navigation";
  import { onMount, onDestroy } from "svelte";
  import { Button } from "$lib/components/ui/button";
  import { Dialog } from "$lib/components/ui/dialog";
  import LoadingProgress from "$lib/components/loading-progress.svelte";
  import SessionDialogPanel from "$lib/components/session-dialog-panel.svelte";
  import { Switch } from "$lib/components/ui/switch";
  import { Label } from "$lib/components/ui/label";
  import { toast } from "svelte-sonner";
  import { submitTest as submitTestService } from "$lib/services/test-session";
  import { logError } from "$lib/services/logger";
  import { safeResultReturnTo } from "$lib/services/result-navigation";
  import {
    createSessionKeyboardHandler,
    getShortcutAnswer,
  } from "$lib/services/session-keyboard";
  import { loadSessionWithTimeout } from "$lib/services/session-loader";
  import {
    getTestSessionState,
    goToQuestion,
    nextQuestion,
    previousQuestion,
    saveAnswer,
    toggleCurrentFlag,
    clearTestSession,
    getNavigationInfo,
    getProgress,
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
  import { isUuid } from "$lib/utils";

  const attemptId = $derived(page.params.attemptId || "");
  const returnTo = $derived(safeResultReturnTo(page.url.searchParams));

  let isLoading = $state(true);
  let isLoadingComplete = $state(false);
  let loadError = $state<string | null>(null);
  let showSubmitDialog = $state(false);
  let navigatorExpanded = $state(false);
  let showFeedback = $state(true);
  /** Bumped to ignore late load results after cancel / unmount. */
  let loadGeneration = 0;

  // Reactive state from store
  let sessionState = $derived(getTestSessionState());
  let currentQuestion = $derived(getCurrentQuestion());
  let navigation = $derived(getNavigationInfo());
  let progress = $derived(getProgress());
  let settings = $derived(getSettings());

  const handleKeydown = createSessionKeyboardHandler({
    mode: "practice",
    isDialogOpen: () => showSubmitDialog,
    getCurrentQuestion: () => getCurrentQuestion(),
    onNext: nextQuestion,
    onPrevious: previousQuestion,
    onToggleFlag: handleToggleFlag,
    onOpenSubmit: () => {
      showSubmitDialog = true;
    },
    onOptionShortcut: handleOptionShortcut,
  });

  onMount(() => {
    // Read params from the live page store (not a stale $derived capture).
    const id = page.params.attemptId || "";
    if (!id || !isUuid(id)) {
      loadError = "Invalid attempt ID";
      isLoading = false;
      return;
    }

    navigatorExpanded = settings.navigatorExpanded;
    showFeedback = settings.practiceShowImmediateFeedback;
    void loadPracticeSession(id);
    window.addEventListener("keydown", handleKeydown);

    return () => {
      window.removeEventListener("keydown", handleKeydown);
    };
  });

  onDestroy(() => {
    loadGeneration += 1;
    clearTestSession();
  });

  async function loadPracticeSession(id: string) {
    const gen = ++loadGeneration;
    isLoading = true;
    isLoadingComplete = false;
    loadError = null;
    let loaded = false;

    try {
      const result = await loadSessionWithTimeout(id, "practice");
      if (gen !== loadGeneration) return;
      if (result.redirectTo) {
        void goto(
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
          "practice",
          questions,
          attempt.duration,
          0,
          answers,
          flags,
        );
        loaded = true;
      }
    } catch (error) {
      if (gen !== loadGeneration) return;
      await logError("Failed to load practice session", error);
      loadError =
        error instanceof Error
          ? error.message
          : "Failed to load practice session";
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

  async function handleSubmit() {
    // Guard against double-submit
    if (!sessionState.attemptId || sessionState.isSubmitting) return;

    const submittedAttemptId = sessionState.attemptId;
    setSubmitting(true);
    showSubmitDialog = false;

    try {
      await flushPendingSaves();
      await submitTestService(submittedAttemptId);
      clearTestSession(false);
      toast.success("Practice session completed!");
      goto(
        `/results/${submittedAttemptId}?returnTo=${encodeURIComponent(returnTo)}`,
      );
    } catch (error) {
      await logError("Failed to submit practice session", error);
      toast.error("Failed to finish practice session");
      setSubmitting(false);
    }
  }

  function toggleNavigator() {
    navigatorExpanded = !navigatorExpanded;
    updateSetting("navigatorExpanded", navigatorExpanded);
  }

  function toggleFeedback() {
    showFeedback = !showFeedback;
    updateSetting("practiceShowImmediateFeedback", showFeedback);
  }
</script>

<svelte:head>
  <title>Practice - PrepLoop</title>
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
            if (id && isUuid(id)) void loadPracticeSession(id);
          }}
        >
          Retry
        </Button>
      </div>
    </div>
  </div>
{:else if sessionState.attemptId}
  <SessionWorkspace
    modeLabel="Practice"
    exitLabel="Exit practice"
    session={sessionState}
    question={currentQuestion}
    answer={currentQuestion ? getAnswer(currentQuestion.id) : null}
    flagged={currentQuestion ? isFlagged(currentQuestion.id) : false}
    {navigation}
    {progress}
    {navigatorExpanded}
    {showFeedback}
    allowTextSelection={true}
    showTags={true}
    onAnswer={(answer) => void handleAnswer(answer)}
    onToggleFlag={() => void handleToggleFlag()}
    onNavigate={goToQuestion}
    onToggleNavigator={toggleNavigator}
    onPrevious={previousQuestion}
    onNext={nextQuestion}
    onSubmit={() => (showSubmitDialog = true)}
  >
    {#snippet headerCenter()}
      <div class="flex items-center gap-2">
        <Label
          for="feedback-toggle"
          class="cursor-pointer text-xs font-bold uppercase tracking-widest text-muted-foreground/75"
        >
          {showFeedback ? "Answers On" : "Answers Off"}
        </Label>
        <Switch
          id="feedback-toggle"
          checked={showFeedback}
          onCheckedChange={toggleFeedback}
          class="scale-75"
        />
      </div>
    {/snippet}
  </SessionWorkspace>

  <!-- Finish Confirmation Dialog -->
  <Dialog bind:open={showSubmitDialog}>
    <SessionDialogPanel
      title="SUBMIT PRACTICE"
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
