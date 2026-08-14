<script lang="ts">
  import { onDestroy, onMount } from "svelte";
  import { Button } from "$lib/components/ui/button";
  import {
    Dialog,
    DialogContent,
    DialogTitle,
  } from "$lib/components/ui/dialog";
  import { Keyboard, X } from "@lucide/svelte";
  import { isTypingTarget } from "$lib/services/session-keyboard";

  interface Props {
    variant?: "default" | "circle";
  }

  let { variant = "default" }: Props = $props();

  let open = $state(false);
  let usesCommandKey = $state(false);

  let modKey = $derived(usesCommandKey ? "⌘" : "Ctrl");

  function detectCommandKey(): boolean {
    const navigatorWithPlatformData = navigator as Navigator & {
      userAgentData?: { platform?: string };
    };
    const platform = [
      navigatorWithPlatformData.userAgentData?.platform,
      navigator.platform,
      navigator.userAgent,
    ]
      .filter(Boolean)
      .join(" ");

    return /mac|iphone|ipad|ipod/i.test(platform);
  }

  function handleGlobalKeydown(event: KeyboardEvent) {
    if (isTypingTarget(event.target)) {
      return;
    }

    if ((event.key === "?" || (event.key === "/" && event.shiftKey)) && !open) {
      event.preventDefault();
      open = true;
      return;
    }

    if (event.key === "Escape" && open) {
      event.preventDefault();
      open = false;
    }
  }

  onMount(() => {
    usesCommandKey = detectCommandKey();
    window.addEventListener("keydown", handleGlobalKeydown);
  });

  onDestroy(() => {
    window.removeEventListener("keydown", handleGlobalKeydown);
  });

  const shortcuts = $derived([
    { label: "Search Questions", keys: [modKey, "K"] },
    { label: "Next", keys: ["Right"] },
    { label: "Previous", keys: ["Left"] },
    { label: "Flag", keys: ["F"] },
    { label: "Pause / Resume", keys: ["Space"] },
    { label: "Select Answer", keys: ["1–9"] },
    { label: "Submit", keys: [modKey, "Enter"] },
  ]);
</script>

{#if variant === "circle"}
  <Button
    variant="ghost"
    size="icon"
    class="h-10 w-10 rounded-full border border-border text-muted-foreground transition-colors hover:border-foreground hover:text-foreground"
    onclick={() => (open = !open)}
    title="Keyboard shortcuts"
    aria-label="Keyboard shortcuts"
  >
    <Keyboard class="h-4 w-4" />
  </Button>
{:else}
  <Button
    variant="ghost"
    size="icon"
    class="h-10 w-10 rounded-full border-black/14 shadow-[0_8px_20px_rgba(0,0,0,0.16)] backdrop-blur-md dark:border-white/18 dark:hover:border-white/30 hover:border-black/20"
    onclick={() => (open = !open)}
    title="Keyboard shortcuts"
    aria-label="Keyboard shortcuts"
  >
    <Keyboard class="h-4 w-4" />
  </Button>
{/if}

<Dialog bind:open>
  <DialogContent
    closeOnInteractOutside={true}
    showCloseButton={false}
    class="max-w-sm gap-0 p-0"
  >
    <div
      data-testid="shortcut-dialog-header"
      class="flex h-14 items-center justify-between gap-3 px-5"
    >
      <DialogTitle class="dialog-title-text">SHORTCUTS</DialogTitle>
      <Button
        variant="ghost"
        size="icon-sm"
        class="rounded-full border border-transparent text-muted-foreground/70 transition-colors hover:border-border hover:text-foreground"
        aria-label="Close shortcuts"
        onclick={() => (open = false)}
      >
        <X class="h-4 w-4" />
      </Button>
    </div>

    <div class="mx-5 border-t border-border/70"></div>

    <div class="divide-y divide-border/30 px-5 py-4">
      {#each shortcuts as shortcut}
        <div
          class="ui-small-label grid grid-cols-[minmax(0,1fr)_auto] items-center gap-4 py-2.5 text-muted-foreground/78"
        >
          <span>{shortcut.label}</span>
          <div class="flex items-center gap-2">
            {#each shortcut.keys as key, index}
              {#if index > 0}
                <span
                  class="text-[0.65rem] font-semibold text-muted-foreground/35"
                  aria-hidden="true">+</span
                >
              {/if}
              <kbd
                class="min-w-7 border border-border/55 bg-muted/45 px-2 py-1 text-center font-bold text-foreground"
                >{key}</kbd
              >
            {/each}
          </div>
        </div>
      {/each}
    </div>
  </DialogContent>
</Dialog>
