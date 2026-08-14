<script lang="ts">
  import { Progress } from "$lib/components/ui/progress";
  import { Button } from "$lib/components/ui/button";
  import { Pause, Play } from "@lucide/svelte";
  import { TIMER_THRESHOLDS, type TimerState } from "$lib/types";
  import { formatTime } from "$lib/utils";

  interface Props {
    timeRemaining: number;
    totalDuration: number;
    isPaused: boolean;
    onPause: () => void;
    onResume: () => void;
  }

  let { timeRemaining, totalDuration, isPaused, onPause, onResume }: Props =
    $props();

  const timerState = $derived<TimerState>(
    timeRemaining <= TIMER_THRESHOLDS.CRITICAL
      ? "critical"
      : timeRemaining <= TIMER_THRESHOLDS.WARNING
        ? "warning"
        : "normal",
  );

  const progressPercentage = $derived(
    totalDuration > 0 ? (timeRemaining / totalDuration) * 100 : 0,
  );

  const formattedTime = $derived(formatTime(timeRemaining));

  function getProgressClass(): string {
    switch (timerState) {
      case "critical":
        return "[&>div]:bg-destructive";
      case "warning":
        return "[&>div]:bg-chart-4";
      default:
        return "[&>div]:bg-chart-1";
    }
  }

  function getTextClass(): string {
    switch (timerState) {
      case "critical":
        return "text-destructive";
      case "warning":
        return "text-chart-4";
      default:
        return "text-foreground";
    }
  }
</script>

<div class="grid grid-cols-[auto_2rem] items-center gap-4">
  <span
    class="inline-block min-w-[7.5ch] text-right text-xl font-bold tracking-[-0.025em] tabular-nums {getTextClass()} {timerState ===
    'critical'
      ? 'animate-pulse'
      : ''} {isPaused ? 'opacity-50' : ''}"
  >
    {formattedTime}
  </span>

  {#if !isPaused}
    <Button
      variant="outline"
      size="icon"
      class="h-8 w-8 rounded-full"
      onclick={onPause}
    >
      <Pause class="h-3 w-3 fill-current" />
    </Button>
  {:else}
    <div class="h-8 w-8" aria-hidden="true"></div>
  {/if}
</div>
