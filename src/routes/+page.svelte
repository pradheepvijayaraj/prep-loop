<!--
  UPSC CSE market-demand home — drill-down catalog.

  Home → Prelims | Mains
  Prelims → GS1 | CSAT → years → Test / Practice
  Mains → Essay | GS1–4 | Mathematics → years (dual: Paper I / Paper II) → theory modal
-->
<script lang="ts">
  import { goto, preloadCode } from "$app/navigation";
  import { onMount } from "svelte";
  import CatalogScreenContent from "$lib/components/catalog-screen-content.svelte";
  import LoadingProgress from "$lib/components/loading-progress.svelte";
  import QuestionSearch from "$lib/components/question-search.svelte";
  import ScrollIndicator from "$lib/components/scroll-indicator.svelte";
  import ShortcutsLauncher from "$lib/components/shortcuts-launcher.svelte";
  import ThemeSwitcher from "$lib/components/theme-switcher.svelte";
  import TheoryPaperModal from "$lib/components/theory-paper-modal.svelte";
  import SessionDialogPanel from "$lib/components/session-dialog-panel.svelte";
  import { Dialog } from "$lib/components/ui/dialog";
  import { ACTIVE_UPSC_SECTIONS } from "$lib/constants/upsc-catalog";
  import { SESSION_LOAD_TIMEOUT_MS } from "$lib/constants/timer";
  import {
    catalogHeading,
    catalogReturnTo,
    catalogRouteFromSearchParams,
    paperItems,
    parseBankMetadata,
    searchScope,
    type CatalogScreen,
    type PaperListItem,
  } from "$lib/services/catalog-model";
  import {
    getQuestionBankWithQuestions,
    getQuestionBanks,
  } from "$lib/services/question-bank";
  import { formatDuration } from "$lib/utils";
  import { logError } from "$lib/services/logger";
  import { withLoadingTimeout } from "$lib/services/loading-timeout";
  import { isTypingTarget } from "$lib/services/session-keyboard";
  import {
    createTestAttempt,
    listTestAttemptHistory,
  } from "$lib/services/test-session";
  import { seedUpscBanksIfNeeded } from "$lib/services/upsc-seed";
  import type {
    Question,
    StoredQuestionBank,
    TestAttemptHistoryEntry,
    TestMode,
  } from "$lib/types";
  import { ChevronLeft, History, Home } from "@lucide/svelte";
  import { toast } from "svelte-sonner";

  let banks = $state<StoredQuestionBank[]>([]);
  let isLoading = $state(true);
  let isLoadingComplete = $state(false);
  let screen = $state<CatalogScreen>({ kind: "home" });
  let screenHistory = $state<CatalogScreen[]>([]);
  let scrollElement = $state<HTMLElement | null>(null);
  let catalogLoadGen = 0;
  let searchOpen = $state(false);
  let historyEntries = $state<TestAttemptHistoryEntry[]>([]);
  let historyLoading = $state(false);
  let historyLoadingComplete = $state(false);
  let historyError = $state<string | null>(null);

  // Prelims start session
  let startDialogOpen = $state(false);
  let selectedBank = $state<StoredQuestionBank | null>(null);
  let selectedMode = $state<TestMode>("practice");
  let isStarting = $state(false);

  // Theory view modal
  let theoryOpen = $state(false);
  let theoryTitle = $state("");
  let theorySubtitle = $state("");
  let theoryPaperCode = $state("");
  let theoryQuestions = $state<Question[]>([]);
  let theoryLoading = $state(false);
  let theoryLoadingComplete = $state(false);
  let theoryError = $state<string | null>(null);

  onMount(() => {
    const handleCatalogBackKey = (event: KeyboardEvent) => {
      if (event.defaultPrevented) return;
      if (
        (event.key !== "Backspace" && event.key !== "Delete") ||
        event.metaKey ||
        event.ctrlKey ||
        event.altKey ||
        isTypingTarget(event.target)
      ) {
        return;
      }

      if (theoryOpen) {
        event.preventDefault();
        theoryOpen = false;
        return;
      }

      if (startDialogOpen) {
        event.preventDefault();
        startDialogOpen = false;
        return;
      }

      if (searchOpen) {
        event.preventDefault();
        return;
      }

      if (screen.kind !== "home") {
        event.preventDefault();
        goBack();
      }
    };

    window.addEventListener("keydown", handleCatalogBackKey);
    void preloadCode("/test/preload");
    void preloadCode("/practice/preload");
    void loadCatalog();
    const restoredRoute = catalogRouteFromSearchParams(
      new URLSearchParams(window.location.search),
    );
    if (restoredRoute) {
      screen = restoredRoute.screen;
      screenHistory = restoredRoute.history;
      if (screen.kind === "prelims-history") void openHistory(false);
    }

    return () => {
      window.removeEventListener("keydown", handleCatalogBackKey);
    };
  });

  async function loadCatalog() {
    const gen = ++catalogLoadGen;
    isLoading = true;
    isLoadingComplete = false;
    let loaded = false;
    try {
      const seedResult = await withLoadingTimeout(seedUpscBanksIfNeeded());
      if (gen !== catalogLoadGen) return;
      if (seedResult.failed > 0) {
        toast.error(`${seedResult.failed} UPSC paper updates failed`);
      }
      banks = (await withLoadingTimeout(getQuestionBanks())).filter((bank) =>
        ACTIVE_UPSC_SECTIONS.has(parseBankMetadata(bank).section),
      );
      if (gen !== catalogLoadGen) return;
      if (banks.length === 0) {
        toast.error("Failed. Try again. Restart if it keeps failing.");
      } else {
        loaded = true;
      }
    } catch (error) {
      if (gen !== catalogLoadGen) return;
      await logError("Failed to load UPSC catalog", error);
      toast.error("Failed. Try again. Restart if it keeps failing.");
    } finally {
      if (gen === catalogLoadGen) {
        if (loaded) isLoadingComplete = true;
        else isLoading = false;
      }
    }
  }

  function finishCatalogLoading() {
    isLoading = false;
    isLoadingComplete = false;
  }

  const totalCatalogQuestions = $derived(
    banks.reduce((total, bank) => total + bank.totalQuestions, 0),
  );
  const prelimsCatalogPaperCount = $derived(
    banks.filter((bank) =>
      parseBankMetadata(bank).section.startsWith("prelims-"),
    ).length,
  );
  const mainsCatalogPaperCount = $derived(
    banks.filter((bank) => parseBankMetadata(bank).section.startsWith("mains-"))
      .length,
  );
  const currentSearchScope = $derived(searchScope(screen));
  const searchSections = $derived(currentSearchScope.sections);
  const searchScopeLabel = $derived(currentSearchScope.label);
  const prelimsPapers = $derived.by((): PaperListItem[] => {
    if (screen.kind !== "prelims-paper") return [];
    return paperItems(banks, [screen.paper.section], "prelims");
  });

  const isDualPaper = $derived(
    screen.kind === "mains-paper" && Boolean(screen.paper.dualPaper),
  );

  const mainsListItems = $derived.by((): PaperListItem[] => {
    if (screen.kind !== "mains-paper") return [];
    if (screen.paper.dualPaper) return [];
    return paperItems(banks, screen.paper.sections, "theory");
  });

  /** Dual-paper optionals: year tiles under separate Paper I / Paper II headings */
  const dualPaper1Items = $derived.by((): PaperListItem[] => {
    if (!isDualPaper || screen.kind !== "mains-paper") return [];
    const section = screen.paper.sections[0];
    if (!section) return [];
    return paperItems(banks, [section], "theory");
  });

  const dualPaper2Items = $derived.by((): PaperListItem[] => {
    if (!isDualPaper || screen.kind !== "mains-paper") return [];
    const section = screen.paper.sections[1];
    if (!section) return [];
    return paperItems(banks, [section], "theory");
  });

  function goHome() {
    screen = { kind: "home" };
    screenHistory = [];
  }

  function navigateTo(next: CatalogScreen) {
    screenHistory = [...screenHistory, screen];
    screen = next;
  }

  function goBack() {
    const previous = screenHistory.at(-1);
    if (!previous) return goHome();
    screen = previous;
    screenHistory = screenHistory.slice(0, -1);
  }

  async function openHistory(push = true) {
    if (push) navigateTo({ kind: "prelims-history" });
    historyEntries = [];
    historyLoading = true;
    historyLoadingComplete = false;
    historyError = null;
    let loaded = false;
    try {
      historyEntries = await withLoadingTimeout(listTestAttemptHistory());
      loaded = true;
    } catch (error) {
      await logError("Failed to load test history", error);
      historyError =
        error instanceof Error ? error.message : "Failed to load test history";
    } finally {
      if (loaded) historyLoadingComplete = true;
      else historyLoading = false;
    }
  }

  function finishHistoryLoading() {
    historyLoading = false;
    historyLoadingComplete = false;
  }

  function openPrelimPicker(bank: StoredQuestionBank) {
    selectedBank = bank;
    selectedMode = "practice";
    startDialogOpen = true;
  }

  async function startSelectedMode(mode: TestMode) {
    if (!selectedBank || isStarting) return;
    selectedMode = mode;
    isStarting = true;
    try {
      const bankId = selectedBank.id;
      const attemptId = await Promise.race([
        createTestAttempt(bankId, mode),
        new Promise<never>((_, reject) => {
          window.setTimeout(() => {
            reject(
              new Error(
                "Timed out starting session. Restart the app if UPSC papers are still seeding.",
              ),
            );
          }, SESSION_LOAD_TIMEOUT_MS);
        }),
      ]);
      startDialogOpen = false;
      const returnTo = catalogReturnTo({ history: screenHistory, screen });
      await goto(
        `/${mode}/${attemptId}?returnTo=${encodeURIComponent(returnTo)}`,
      );
    } catch (error) {
      await logError("Failed to start session", error);
      toast.error(
        error instanceof Error
          ? error.message.toUpperCase()
          : "FAILED TO START",
      );
    } finally {
      isStarting = false;
    }
  }

  function paperCodeFromBank(bank: StoredQuestionBank): string {
    try {
      const meta = JSON.parse(bank.metadata) as Record<string, unknown>;
      if (typeof meta.paper === "string") return meta.paper;
      if (typeof meta.section === "string") return meta.section;
    } catch {
      /* ignore */
    }
    return bank.name;
  }

  function formatTheoryTitle(
    bank: StoredQuestionBank,
    meta: Record<string, unknown>,
  ): string {
    const year =
      typeof meta.year === "number" ? meta.year : parseBankMetadata(bank).year;
    const paper =
      typeof meta.paper === "string" ? meta.paper.toUpperCase() : "";

    if (paper === "ESSAY") return `Mains Essay · ${year}`;
    if (/^GS[1-4]$/.test(paper)) return `Mains ${paper} · ${year}`;

    const optionalTitles: Record<string, [string, string]> = {
      MATHS1: ["Mathematics", "I"],
      MATHS2: ["Mathematics", "II"],
    };
    const opt = optionalTitles[paper];
    if (opt) return `${opt[0]} Optional · Paper ${opt[1]} · ${year}`;

    // Fallback: clean stored name
    return bank.name;
  }

  async function openTheoryPaper(item: PaperListItem) {
    theoryTitle = item.bank.name;
    theorySubtitle = "";
    theoryPaperCode = paperCodeFromBank(item.bank);
    theoryQuestions = [];
    theoryError = null;
    theoryLoading = true;
    theoryLoadingComplete = false;
    theoryOpen = true;
    let loaded = false;

    try {
      const payload = await withLoadingTimeout(
        getQuestionBankWithQuestions(item.bank.id),
      );
      if (!payload) {
        theoryError = "Could not load this paper.";
        return;
      }
      theoryQuestions = payload.questions;
      try {
        const meta = JSON.parse(payload.metadata) as Record<string, unknown>;
        if (typeof meta.paper === "string") theoryPaperCode = meta.paper;
        theoryTitle = formatTheoryTitle(item.bank, meta);
      } catch {
        theoryTitle = payload.name;
      }
      theorySubtitle = "";
      loaded = true;
    } catch (error) {
      await logError("Failed to load theory paper", error);
      theoryError =
        error instanceof Error ? error.message : "Failed to load paper";
    } finally {
      if (loaded) theoryLoadingComplete = true;
      else theoryLoading = false;
    }
  }

  function finishTheoryLoading() {
    theoryLoading = false;
    theoryLoadingComplete = false;
  }

  const heading = $derived(catalogHeading(screen));
  const pageTitle = $derived(heading.title);
  const pageTrail = $derived(heading.trail);

  const screenAnimationKey = $derived.by(() => {
    if (screen.kind === "prelims-paper")
      return `${screen.kind}-${screen.paper.id}`;
    if (screen.kind === "mains-paper")
      return `${screen.kind}-${screen.paper.id}`;
    return screen.kind;
  });
</script>

<svelte:head>
  <title>UPSC CSE · PrepLoop</title>
</svelte:head>

{#if isLoading}
  <LoadingProgress
    class="h-full bg-background"
    complete={isLoadingComplete}
    onComplete={finishCatalogLoading}
  />
{:else}
  <!--
    Shell:
    - Nav chrome always present (same title Y on home + nested)
    - Fixed masthead
    - Tile pane is the only scroller; frame ends above footer so
      ScrollIndicator never runs into bottom chrome
  -->
  <div
    class="relative flex h-full flex-col overflow-hidden bg-background"
    style="--library-footer-height: clamp(5rem, 10vh, 6rem); --app-header-height: clamp(4.25rem, 8vh, 5rem);"
  >
    <header
      class="relative z-20 flex h-[var(--app-header-height)] shrink-0 items-center bg-background px-[clamp(1.5rem,2.5vw,3rem)]"
    >
      <button
        type="button"
        class={`app-chrome-control flex h-9 w-9 items-center justify-center rounded-full border border-border/75 text-muted-foreground transition-[opacity,transform,border-color,color] duration-200 hover:border-foreground/45 hover:text-foreground ${screen.kind !== "home" ? "app-chrome-control--visible" : ""}`}
        aria-label="Back"
        title="Back"
        aria-hidden={screen.kind === "home"}
        tabindex={screen.kind === "home" ? -1 : 0}
        onclick={goBack}
      >
        <ChevronLeft class="h-4 w-4" />
      </button>
      <div class="ml-auto flex items-center gap-2">
        <button
          type="button"
          class={`app-chrome-control flex h-9 w-9 items-center justify-center rounded-full border border-border/75 text-muted-foreground transition-[opacity,transform,border-color,color] duration-200 hover:border-foreground/45 hover:text-foreground ${screen.kind === "prelims" || screen.kind === "prelims-paper" || screen.kind === "prelims-history" ? "app-chrome-control--visible" : ""}`}
          aria-label="Test history"
          title="Test history"
          aria-hidden={screen.kind !== "prelims" &&
            screen.kind !== "prelims-paper" &&
            screen.kind !== "prelims-history"}
          tabindex={screen.kind === "prelims" ||
          screen.kind === "prelims-paper" ||
          screen.kind === "prelims-history"
            ? 0
            : -1}
          onclick={() => void openHistory()}
        >
          <History class="h-4 w-4" />
        </button>
        <button
          type="button"
          class={`app-chrome-control flex h-9 w-9 items-center justify-center rounded-full border border-border/75 text-muted-foreground transition-[opacity,transform,border-color,color] duration-200 hover:border-foreground/45 hover:text-foreground ${screen.kind !== "home" ? "app-chrome-control--visible" : ""}`}
          aria-label="Home"
          title="Home"
          aria-hidden={screen.kind === "home"}
          tabindex={screen.kind === "home" ? -1 : 0}
          onclick={goHome}
        >
          <Home class="h-4 w-4" />
        </button>
        <QuestionSearch
          bind:open={searchOpen}
          sections={searchSections}
          scopeLabel={searchScopeLabel}
          enabled={!theoryOpen && !startDialogOpen}
        />
      </div>
    </header>

    <!-- Content column stops above footer — scrollbar stays in this box -->
    <div
      class="relative z-0 flex min-h-0 flex-1 flex-col overflow-hidden pb-[var(--library-footer-height)]"
    >
      <!-- Fixed masthead shared by every catalog view -->
      <div class="shrink-0 px-5 pt-8 sm:px-8 sm:pt-10">
        <div class="mx-auto w-full max-w-6xl">
          <div
            class="mb-6 flex min-h-14 items-end justify-center text-center sm:mb-7"
          >
            {#key screenAnimationKey}
              <div class="catalog-view-enter text-center">
                {#if pageTrail}
                  <p
                    class="mb-2 text-[0.7rem] font-bold uppercase tracking-[0.18em] text-muted-foreground/50"
                  >
                    {pageTrail}
                  </p>
                {/if}
                <h1
                  class="text-[1.85rem] font-semibold tracking-[-0.035em] text-foreground sm:text-[2.15rem]"
                >
                  {pageTitle}
                </h1>
              </div>
            {/key}
          </div>
        </div>
      </div>

      <!-- Scrollable tiles only -->
      <div class="relative min-h-0 flex-1 overflow-hidden">
        <div
          bind:this={scrollElement}
          class={`absolute inset-0 overflow-x-hidden px-5 pb-6 sm:px-8 ${screen.kind === "home" ? "overflow-hidden" : "overflow-y-auto no-scrollbar"}`}
        >
          {#key screenAnimationKey}
            <div class="catalog-view-enter mx-auto h-full w-full max-w-6xl">
              <CatalogScreenContent
                {screen}
                {banks}
                totalQuestions={totalCatalogQuestions}
                prelimsCount={prelimsCatalogPaperCount}
                mainsCount={mainsCatalogPaperCount}
                {prelimsPapers}
                mainsPapers={mainsListItems}
                dualPaper1={dualPaper1Items}
                dualPaper2={dualPaper2Items}
                {isDualPaper}
                {historyEntries}
                {historyLoading}
                {historyLoadingComplete}
                {historyError}
                onHistoryLoadingComplete={finishHistoryLoading}
                onScreenChange={navigateTo}
                onOpenHistory={() => void openHistory()}
                onOpenResult={(id) =>
                  void goto(
                    `/results/${id}?returnTo=${encodeURIComponent(
                      catalogReturnTo({ history: screenHistory, screen }),
                    )}`,
                  )}
                onOpenPrelim={openPrelimPicker}
                onOpenTheory={(item) => void openTheoryPaper(item)}
              />
            </div>
          {/key}
        </div>
        <ScrollIndicator
          scroller={scrollElement}
          updateTrigger={screen}
          trackInsetTop="clamp(0.75rem, 2vh, 1.5rem)"
          trackInsetBottom="clamp(0.75rem, 2vh, 1.5rem)"
        />
      </div>
    </div>

    <footer
      class="pointer-events-none absolute inset-x-0 bottom-0 z-20 flex h-[var(--library-footer-height)] items-end px-[clamp(1.5rem,2.5vw,3rem)] py-[clamp(1.25rem,2.5vh,2rem)]"
    >
      <div class="pointer-events-auto flex items-center gap-2">
        <ShortcutsLauncher variant="circle" />
        <ThemeSwitcher direction="right" />
      </div>
    </footer>
  </div>
{/if}

<!-- Prelims: pick Test or Practice after clicking a year row -->
<Dialog bind:open={startDialogOpen}>
  <SessionDialogPanel
    title="READY ?"
    primaryLabel={isStarting && selectedMode === "test"
      ? "STARTING..."
      : "TEST"}
    secondaryActionLabel={isStarting && selectedMode === "practice"
      ? "STARTING..."
      : "PRACTICE"}
    onPrimary={() => void startSelectedMode("test")}
    onSecondaryAction={() => void startSelectedMode("practice")}
    onSecondary={() => (startDialogOpen = false)}
    primaryDisabled={isStarting}
    secondaryDisabled={isStarting}
    contentClass="max-w-[27.5rem]"
    bodyClass="space-y-2 px-6 pt-5 pb-3"
    footerClass="px-6 pt-2 pb-5"
  >
    {#if selectedBank}
      <div
        class="text-[1.08rem] font-medium leading-[1.35] tracking-[-0.015em] text-foreground"
      >
        {selectedBank.name}
      </div>
      <div
        class="ui-small-label flex items-center gap-3.5 text-muted-foreground/64"
      >
        <span>{selectedBank.totalQuestions}Q</span>
        <span aria-hidden="true">·</span>
        <span>{formatDuration(selectedBank.defaultDuration)}</span>
      </div>
    {/if}
  </SessionDialogPanel>
</Dialog>

<!-- Mains / theory: full-screen paper viewer (not a dialog) -->
{#if theoryOpen}
  <TheoryPaperModal
    bind:open={theoryOpen}
    title={theoryTitle}
    subtitle={theorySubtitle}
    paperCode={theoryPaperCode}
    questions={theoryQuestions}
    isLoading={theoryLoading}
    loadingComplete={theoryLoadingComplete}
    onLoadingComplete={finishTheoryLoading}
    error={theoryError}
  />
{/if}
