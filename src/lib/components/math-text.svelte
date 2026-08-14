<!--
  Mixed plain text + LaTeX via KaTeX + GFM tables + markdown images.
  - (a)/(b)/(c) on separate lines
  - Simple $7$ / $16$ unwrapped to plain text (same UI font as body)
  - Markdown tables → real HTML tables
  - ![alt](src) → <img>
-->
<script lang="ts">
  import { renderMathText } from "$lib/services/math-text-parser";
  import { cn } from "$lib/utils";

  interface Props {
    text: string;
    class?: string;
  }

  let { text, class: className = "" }: Props = $props();
  let html = $derived(renderMathText(text));
</script>

<div class={cn("math-text", className)}>
  {@html html}
</div>

<style>
  :global(.math-text .katex) {
    font-size: 1.06em;
  }

  :global(.math-text .katex-display) {
    margin: 0.75em 0;
    overflow-x: auto;
    overflow-y: hidden;
    text-align: left;
  }

  :global(.math-text .katex-display > .katex) {
    text-align: left;
  }

  :global(.math-text .katex-display .base) {
    margin: 0 0.15em;
  }

  :global(.math-text .katex .mtable) {
    vertical-align: middle;
  }

  :global(.math-text) {
    display: block;
    line-height: inherit;
    font: inherit;
    color: inherit;
    letter-spacing: inherit;
  }

  :global(.math-text__line) {
    display: block;
    margin: 0 0 0.85em;
    line-height: inherit;
    font: inherit;
  }

  :global(.math-text__line--sub) {
    margin-left: 1.55em;
    margin-bottom: 0.65em;
  }

  :global(.math-text__line:first-child) {
    margin-top: 0;
  }

  :global(.math-text__line:last-child) {
    margin-bottom: 0;
  }

  :global(.math-text__img) {
    display: block;
    max-width: min(100%, 36rem);
    width: auto;
    height: auto;
    margin: 0.65em 0;
    border-radius: 0.35rem;
    background: color-mix(in oklab, var(--background) 88%, white 12%);
    border: 1px solid color-mix(in oklab, var(--border) 70%, transparent);
  }

  :global(.answer-option__text .math-text__img) {
    max-width: min(100%, 14rem);
    margin: 0.15em 0;
  }

  :global(.answer-option__text .math-text),
  :global(.answer-option__text .math-text__line) {
    font: inherit;
    letter-spacing: inherit;
    line-height: inherit;
  }

  :global(.math-text__table-wrap) {
    display: block;
    width: 100%;
    max-width: 100%;
    overflow-x: auto;
    margin: 0.75em 0 1em;
    -webkit-overflow-scrolling: touch;
  }

  :global(.math-text__table) {
    width: max-content;
    min-width: min(100%, 20rem);
    max-width: 100%;
    border-collapse: collapse;
    font: inherit;
    font-size: 0.92em;
    line-height: 1.35;
    letter-spacing: inherit;
  }

  :global(.math-text__table th),
  :global(.math-text__table td) {
    border: 1px solid color-mix(in oklab, var(--border) 80%, transparent);
    padding: 0.4em 0.7em;
    text-align: left;
    vertical-align: middle;
    white-space: nowrap;
  }

  :global(.math-text__table th) {
    font-weight: 600;
    background: color-mix(in oklab, var(--muted) 55%, transparent);
    color: var(--foreground);
  }

  :global(.math-text__table tbody tr:nth-child(even) td) {
    background: color-mix(in oklab, var(--muted) 22%, transparent);
  }
</style>
