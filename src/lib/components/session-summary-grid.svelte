<script lang="ts">
  interface Props {
    answered: number;
    total: number;
    flagged: number;
  }

  let { answered, total, flagged }: Props = $props();
</script>

<div>
  <div class="flex items-center justify-between gap-5 px-2 py-4">
    <div class="ui-small-label text-muted-foreground/64">Answered</div>
    <div
      class="text-[1.45rem] font-black tracking-[-0.015em] tabular-nums text-foreground"
    >
      {answered} / {total}
    </div>
  </div>
  <div class="mx-2 h-px bg-border/18"></div>
  <div class="flex items-center justify-between gap-5 px-2 py-4">
    <div class="ui-small-label text-muted-foreground/64">Flagged</div>
    <div
      class="text-[1.45rem] font-black tracking-[-0.015em] tabular-nums text-foreground"
    >
      {flagged}
    </div>
  </div>
</div>
