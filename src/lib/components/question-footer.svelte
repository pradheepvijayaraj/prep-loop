<script lang="ts">
  import type { Snippet } from "svelte";
  import { ChevronLeft, ChevronRight } from "@lucide/svelte";
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";

  interface Props {
    current: number;
    total: number;
    canPrevious: boolean;
    canNext: boolean;
    onPrevious: () => void;
    onNext: () => void;
    previousLabel?: string;
    nextLabel?: string;
    class?: string;
    actions: Snippet;
  }

  let {
    current,
    total,
    canPrevious,
    canNext,
    onPrevious,
    onNext,
    previousLabel = "Previous question",
    nextLabel = "Next question",
    class: className,
    actions,
  }: Props = $props();
</script>

<div
  class={cn(
    "grid w-full grid-cols-[1fr_auto_1fr] items-center gap-4",
    className,
  )}
>
  <div
    class="min-w-0 text-sm font-bold tracking-[0.08em] text-muted-foreground/85 tabular-nums"
  >
    <span
      class="inline-block text-right"
      style={`width: ${String(total).length}ch;`}>{current}</span
    >
    <span class="mx-1">/</span>
    <span class="inline-block" style={`width: ${String(total).length}ch;`}
      >{total}</span
    >
  </div>
  <div class="flex items-center gap-3 justify-self-center">
    <Button
      variant="outline"
      size="icon"
      class="h-11 w-11 rounded-full"
      onclick={onPrevious}
      disabled={!canPrevious}
      aria-label={previousLabel}><ChevronLeft class="h-3.5 w-3.5" /></Button
    >
    <Button
      variant="outline"
      size="icon"
      class="h-11 w-11 rounded-full"
      onclick={onNext}
      disabled={!canNext}
      aria-label={nextLabel}><ChevronRight class="h-3.5 w-3.5" /></Button
    >
  </div>
  {@render actions()}
</div>
