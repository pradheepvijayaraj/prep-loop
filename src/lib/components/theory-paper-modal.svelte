<!--
  Full-screen paper viewer. Header + footer are opaque chrome; only the
  middle pane scrolls and is overflow-clipped so content never paints
  above the header or below the footer.
-->
<script lang="ts">
  import { tick } from "svelte";
  import { Button } from "$lib/components/ui/button";
  import {
    Dialog,
    DialogContent,
    DialogTitle,
  } from "$lib/components/ui/dialog";
  import LoadingProgress from "$lib/components/loading-progress.svelte";
  import MathText from "$lib/components/math-text.svelte";
  import ScrollIndicator from "$lib/components/scroll-indicator.svelte";
  import type { Question } from "$lib/types";
  import { formatMarks } from "$lib/utils";

  interface Props {
    title: string;
    subtitle?: string;
    paperCode?: string;
    questions: Question[];
    isLoading?: boolean;
    loadingComplete?: boolean;
    onLoadingComplete?: () => void;
    error?: string | null;
    open?: boolean;
  }

  let {
    title,
    subtitle = "",
    paperCode = "",
    questions,
    isLoading = false,
    loadingComplete = false,
    onLoadingComplete,
    error = null,
    open = $bindable(true),
  }: Props = $props();

  let scrollElement = $state<HTMLElement | null>(null);
  let closeButton = $state<HTMLButtonElement | null>(null);

  function handleOpenAutoFocus(event: Event) {
    event.preventDefault();
    void tick().then(() => closeButton?.focus());
  }

  type PaperSection = {
    key: string;
    label: string;
    questions: Question[];
  };

  function sectionFromTags(question: Question): string | null {
    const tag = (question.tags ?? []).find((t) =>
      /^section\s+/i.test(t.trim()),
    );
    if (!tag) return null;
    return (
      tag
        .replace(/^section\s+/i, "")
        .trim()
        .toUpperCase() || null
    );
  }

  const sections = $derived.by((): PaperSection[] => {
    const map = new Map<string, Question[]>();
    const order: string[] = [];

    for (const question of questions) {
      const key = sectionFromTags(question) ?? "_all";
      if (!map.has(key)) {
        map.set(key, []);
        order.push(key);
      }
      map.get(key)!.push(question);
    }

    order.sort((a, b) => {
      if (a === "_all") return 1;
      if (b === "_all") return -1;
      return a.localeCompare(b);
    });

    return order.map((key) => ({
      key,
      label: key === "_all" ? "Questions" : `Section ${key}`,
      questions: map.get(key) ?? [],
    }));
  });

  const isEssay = $derived(/essay/i.test(paperCode) || /essay/i.test(title));
  const isMaths = $derived(/maths?/i.test(paperCode) || /math/i.test(title));
  const isWide = $derived(!isEssay);
  const hasMultipleSections = $derived(
    sections.length > 1 ||
      (sections.length === 1 && sections[0]?.key !== "_all"),
  );

  const isEthicsPaper = $derived(
    /gs\s*4|ethics/i.test(paperCode) || /ethics/i.test(title),
  );

  function displayTags(question: Question): string[] {
    return (question.tags ?? []).filter((tag) => {
      const normalized = tag.trim();
      if (!normalized || /^section\s+/i.test(normalized)) return false;
      if (
        /^(mains|prelims)\b/i.test(normalized) ||
        normalized === "descriptive"
      )
        return false;
      if (
        isEthicsPaper &&
        /^ethics(?:, integrity & aptitude)?$/i.test(normalized)
      )
        return false;
      if (
        isMaths &&
        (/^mathematics$/i.test(normalized) ||
          /mathematics optional paper/i.test(normalized))
      )
        return false;
      return true;
    });
  }

  // One short instruction at the top only — no per-section redundant notes.
  const sectionInstruction = $derived.by(() => {
    if (isEssay && hasMultipleSections) {
      return `Write two essays, choosing one topic from each section.`;
    }
    if (isEssay && !hasMultipleSections) {
      return `Write an essay on any one of the following topics.`;
    }
    if (isMaths && hasMultipleSections) {
      return `Attempt five questions in all. Questions 1 and 5 are compulsory. Of the remaining six, attempt any three, choosing at least one from each section.`;
    }
    if (isMaths) {
      return `Attempt five questions in all.`;
    }
    return null;
  });

  function globalIndex(sIndex: number, index: number): number {
    return (
      index +
      1 +
      sections.slice(0, sIndex).reduce((n, s) => n + s.questions.length, 0)
    );
  }

  function isCompulsoryMath(sIndex: number, index: number): boolean {
    return isMaths && hasMultipleSections && index === 0;
  }
</script>

<Dialog bind:open>
  <DialogContent
    showCloseButton={false}
    onOpenAutoFocus={handleOpenAutoFocus}
    class="!fixed !inset-0 !z-[70] !h-auto !w-auto !max-w-none !translate-x-0 !translate-y-0 flex flex-col gap-0 overflow-hidden border-0 bg-background p-0"
  >
    <!-- Opaque chrome — content never paints through this -->
    <header
      class="relative z-20 flex h-14 shrink-0 items-center justify-center border-b border-border/35 bg-background px-16 sm:px-20"
    >
      <div class="min-w-0 max-w-3xl text-center">
        <DialogTitle
          class="truncate text-[1.05rem] font-semibold tracking-[-0.02em] text-foreground sm:text-[1.15rem]"
        >
          {title}
        </DialogTitle>
        {#if subtitle}
          <p class="mt-0.5 truncate text-xs text-muted-foreground/65">
            {subtitle}
          </p>
        {/if}
      </div>
    </header>

    <!-- Clipped scroll frame between header and footer -->
    <div class="relative z-0 min-h-0 flex-1 overflow-hidden">
      {#if isLoading}
        <LoadingProgress
          class="h-full bg-transparent"
          complete={loadingComplete}
          onComplete={onLoadingComplete}
        />
      {:else if error}
        <div
          class="flex h-full items-center justify-center px-6 text-center text-sm text-destructive"
        >
          {error}
        </div>
      {:else if questions.length === 0}
        <div
          class="flex h-full items-center justify-center px-6 text-sm text-muted-foreground"
        >
          No questions in this paper.
        </div>
      {:else}
        <div
          bind:this={scrollElement}
          class="absolute inset-0 overflow-x-hidden overflow-y-auto no-scrollbar"
        >
          <div
            class="mx-auto w-full px-5 py-8 sm:px-10 lg:px-12 {isWide
              ? 'max-w-4xl lg:max-w-5xl'
              : 'max-w-2xl'}"
          >
            {#if sectionInstruction}
              <p
                class="mb-10 border-l-[3px] border-foreground/35 bg-foreground/[0.04] px-4 py-3 text-[1.12rem] font-semibold leading-snug tracking-[-0.015em] text-foreground sm:text-[1.18rem]"
              >
                {sectionInstruction}
              </p>
            {/if}

            {#each sections as section, sIndex (section.key)}
              <section class="mb-14 last:mb-6">
                {#if hasMultipleSections || section.key !== "_all"}
                  <h2
                    class="mb-6 text-[0.85rem] font-bold uppercase tracking-[0.16em] text-muted-foreground/75"
                  >
                    {section.label}
                  </h2>
                {/if}

                {#if isEssay}
                  <!-- items-baseline + shared line-height keeps "1." on the first text line -->
                  <ol class="space-y-5">
                    {#each section.questions as question, index (question.id)}
                      <li
                        class="flex items-baseline gap-3 text-[1.125rem] leading-[1.55] tracking-[-0.02em] text-foreground/92"
                      >
                        <span
                          class="w-6 shrink-0 text-right tabular-nums font-semibold text-muted-foreground/60"
                        >
                          {index + 1}.
                        </span>
                        <div class="min-w-0 flex-1 font-medium">
                          <MathText text={question.question} />
                        </div>
                      </li>
                    {/each}
                  </ol>
                {:else}
                  <ol class="space-y-10">
                    {#each section.questions as question, index (question.id)}
                      {@const qNum = globalIndex(sIndex, index)}
                      {@const compulsory = isCompulsoryMath(sIndex, index)}
                      <li
                        class="flex items-start gap-3.5 text-[1.08rem] leading-[1.65] tracking-[-0.012em]"
                      >
                        <span
                          class="w-8 shrink-0 text-right tabular-nums font-semibold text-muted-foreground/55"
                        >
                          {qNum}.
                        </span>
                        <div
                          class="min-w-0 flex-1 font-medium text-foreground/90"
                        >
                          <MathText text={question.question} />
                          <div
                            class="mt-2.5 flex flex-wrap items-center gap-2 leading-none"
                          >
                            {#if question.marks > 0}
                              <span
                                class="inline-flex items-center rounded-sm border border-foreground/20 bg-foreground/8 px-1.5 py-0.5 text-[0.62rem] font-bold uppercase tracking-[0.12em] text-foreground/75"
                              >
                                {formatMarks(question.marks)}M
                              </span>
                            {/if}
                            {#if compulsory}
                              <span
                                class="inline-flex items-center rounded-sm border border-foreground/20 bg-foreground/8 px-1.5 py-0.5 text-[0.62rem] font-bold uppercase tracking-[0.12em] text-foreground/75"
                              >
                                Compulsory
                              </span>
                            {/if}
                            {#each displayTags(question) as tag}
                              <span
                                class="inline-flex items-center rounded-sm border border-foreground/20 bg-foreground/8 px-1.5 py-0.5 text-[0.62rem] font-bold uppercase tracking-[0.12em] text-foreground/75"
                                >{tag}</span
                              >
                            {/each}
                          </div>
                        </div>
                      </li>
                    {/each}
                  </ol>
                {/if}
              </section>
            {/each}
          </div>
        </div>
        <ScrollIndicator scroller={scrollElement} updateTrigger={questions} />
      {/if}
    </div>

    <footer
      class="relative z-20 flex shrink-0 items-center justify-end bg-background px-6 py-3 sm:px-8"
    >
      <Button
        bind:ref={closeButton}
        variant="outline"
        size="sm"
        class="ui-button-text h-9 min-w-[5.5rem] border-border/60 px-4"
        onclick={() => (open = false)}
      >
        CLOSE
      </Button>
    </footer>
  </DialogContent>
</Dialog>
