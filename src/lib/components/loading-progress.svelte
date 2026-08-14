<script lang="ts">
  import { onMount } from "svelte";
  import { cn } from "$lib/utils";

  interface Props {
    class?: string;
    complete?: boolean;
    onComplete?: () => void;
    delayMs?: number;
  }

  let {
    class: className,
    complete = false,
    onComplete,
    delayMs = 180,
  }: Props = $props();
  let progress = $state(0);
  let visible = $state(false);
  let showTimer: ReturnType<typeof setTimeout> | null = null;
  let completionTimer: ReturnType<typeof setTimeout> | null = null;

  onMount(() => {
    showTimer = setTimeout(() => {
      showTimer = null;
      visible = true;
      requestAnimationFrame(() => {
        progress = 82;
      });
    }, delayMs);
    return () => {
      if (showTimer !== null) clearTimeout(showTimer);
      if (completionTimer !== null) clearTimeout(completionTimer);
    };
  });

  $effect(() => {
    if (!complete || completionTimer !== null) return;
    if (!visible) {
      if (showTimer !== null) clearTimeout(showTimer);
      showTimer = null;
      onComplete?.();
      return;
    }
    progress = 100;
    completionTimer = setTimeout(() => {
      completionTimer = null;
      onComplete?.();
    }, 280);
  });
</script>

{#if visible}
  <div
    class={cn("flex items-center justify-center", className)}
    role="status"
    aria-label="Loading"
  >
    <div class="loading-progress" aria-hidden="true">
      <div
        class="loading-progress-indicator"
        style:transform={`scaleX(${progress / 100})`}
      ></div>
    </div>
  </div>
{/if}

<style>
  .loading-progress {
    width: min(12rem, 60vw);
    height: 0.25rem;
    overflow: hidden;
    border-radius: 9999px;
    background: var(--muted);
  }

  .loading-progress-indicator {
    width: 100%;
    height: 100%;
    border-radius: inherit;
    background: var(--primary);
    transform-origin: left center;
    transition: transform 900ms cubic-bezier(0.2, 0.8, 0.2, 1);
  }

  @media (prefers-reduced-motion: reduce) {
    .loading-progress-indicator {
      transition: none;
    }
  }
</style>
