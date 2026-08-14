<!--
  Root layout — UPSC market-demand shell.
  Init DB + settings, seed is handled on the home page.
-->
<script lang="ts">
  import "../app.css";
  import { page } from "$app/state";
  import { ModeWatcher } from "mode-watcher";
  import { Toaster } from "$lib/components/ui/sonner";
  import { onMount } from "svelte";
  import LoadingProgress from "$lib/components/loading-progress.svelte";
  import { warmQuestionSearch } from "$lib/services/question-search";
  import { initSettings } from "$lib/stores/settings.svelte";
  import { logError } from "$lib/services/logger";
  import { withLoadingTimeout } from "$lib/services/loading-timeout";
  import { isTypingTarget } from "$lib/services/session-keyboard";

  let { children } = $props();

  let isInitialized = $state(false);
  let initializationComplete = $state(false);
  let initError = $state<string | null>(null);

  let isHomePage = $derived(page.url.pathname === "/");

  let toastOffset = $derived(
    isHomePage
      ? { top: "4rem", right: "2rem", left: "1rem" }
      : { top: "1.25rem", right: "1.25rem", left: "1rem" },
  );

  onMount(() => {
    const handleContextMenu = (event: MouseEvent) => {
      event.preventDefault();
    };

    const handleRefreshShortcut = (event: KeyboardEvent) => {
      const key = event.key.toLowerCase();
      if ((event.metaKey || event.ctrlKey) && key === "r") {
        event.preventDefault();
        window.location.reload();
        return;
      }

      if (event.key === "F5" && !isTypingTarget(event.target)) {
        event.preventDefault();
        window.location.reload();
      }
    };

    window.addEventListener("contextmenu", handleContextMenu);
    window.addEventListener("keydown", handleRefreshShortcut);

    void (async () => {
      try {
        // Start loading the local semantic model while the app shell opens.
        // This keeps the first user search from paying the model startup cost.
        void warmQuestionSearch().catch((error) => {
          void logError("Failed to warm question search", error);
        });
        await withLoadingTimeout(initSettings());
        initializationComplete = true;
      } catch (error) {
        await logError("Failed to initialize app", error);
        initError =
          error instanceof Error ? error.message : "Unknown error occurred";
      }
    })();

    return () => {
      window.removeEventListener("contextmenu", handleContextMenu);
      window.removeEventListener("keydown", handleRefreshShortcut);
    };
  });

  function finishInitialization() {
    isInitialized = true;
    initializationComplete = false;
  }
</script>

<ModeWatcher defaultMode="system" />

{#if initError}
  <div class="flex h-screen items-center justify-center bg-background">
    <div class="max-w-md text-center">
      <h1 class="mb-4 text-2xl font-bold text-destructive">
        Initialization Error
      </h1>
      <p class="mb-4 text-muted-foreground">{initError}</p>
      <p class="text-sm text-muted-foreground">
        Please try restarting the application.
      </p>
    </div>
  </div>
{:else if !isInitialized}
  <LoadingProgress
    class="h-screen bg-background"
    complete={initializationComplete}
    onComplete={finishInitialization}
  />
{:else}
  <div class="h-dvh overflow-hidden bg-background">
    <main class="h-full overflow-hidden bg-background">
      {#key page.url.pathname}
        <div class="app-route-enter h-full">
          {@render children()}
        </div>
      {/key}
    </main>
  </div>
{/if}

<Toaster
  closeButton
  position="top-right"
  duration={2200}
  visibleToasts={1}
  gap={8}
  offset={toastOffset}
  mobileOffset={toastOffset}
  closeButtonAriaLabel="Dismiss notification"
/>
