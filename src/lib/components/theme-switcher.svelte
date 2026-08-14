<script lang="ts">
  import { onDestroy, onMount } from "svelte";
  import { setMode, userPrefersMode } from "mode-watcher";
  import { Button } from "$lib/components/ui/button";
  import { getTheme, updateSetting } from "$lib/stores/settings.svelte";
  import { Monitor, Moon, Sun } from "@lucide/svelte";
  import { isTypingTarget } from "$lib/services/session-keyboard";

  type ThemeMode = "system" | "light" | "dark";

  interface ThemeOption {
    value: ThemeMode;
    label: string;
    icon: typeof Monitor;
    xDown: string;
    yDown: string;
    xUp: string;
    yUp: string;
    xRight: string;
    yRight: string;
  }

  interface Props {
    direction?: "down" | "up" | "right";
  }

  let { direction = "down" }: Props = $props();

  const themeOptions: ThemeOption[] = [
    {
      value: "system",
      label: "System",
      icon: Monitor,
      xDown: "-4rem",
      yDown: "0rem",
      xUp: "-4rem",
      yUp: "0rem",
      xRight: "0rem",
      yRight: "-4rem",
    },
    {
      value: "dark",
      label: "Dark",
      icon: Moon,
      xDown: "-2.83rem",
      yDown: "2.83rem",
      xUp: "-2.83rem",
      yUp: "-2.83rem",
      xRight: "2.83rem",
      yRight: "-2.83rem",
    },
    {
      value: "light",
      label: "Light",
      icon: Sun,
      xDown: "0rem",
      yDown: "4rem",
      xUp: "0rem",
      yUp: "-4rem",
      xRight: "4rem",
      yRight: "0rem",
    },
  ];

  let showThemeMenu = $state(false);
  let themeTransitionTimeout: number | null = null;
  let preferredMode = $derived(userPrefersMode.current || "system");
  let ThemeButtonIcon = $derived(
    preferredMode === "system"
      ? Monitor
      : preferredMode === "light"
        ? Sun
        : Moon,
  );

  function triggerThemeTransition() {
    if (typeof document === "undefined") {
      return;
    }

    const root = document.documentElement;
    root.classList.remove("theme-transitioning");
    void root.offsetWidth;
    root.classList.add("theme-transitioning");

    if (themeTransitionTimeout) {
      clearTimeout(themeTransitionTimeout);
    }

    themeTransitionTimeout = window.setTimeout(() => {
      root.classList.remove("theme-transitioning");
      themeTransitionTimeout = null;
    }, 280);
  }

  async function selectTheme(next: ThemeMode, closeMenu = true) {
    // Use the document-wide CSS transition. View Transition overlays are not
    // consistently pointer-safe in the desktop WebView and can block the
    // orbit buttons while the palette changes.
    triggerThemeTransition();
    setMode(next);
    // The options stay mounted in the menu; changing data-open lets their
    // transform and opacity transitions play instead of removing them.
    if (closeMenu) showThemeMenu = false;
    await updateSetting("theme", next);
  }

  function handleThemeKeys(event: KeyboardEvent) {
    const keys = [
      "ArrowRight",
      "ArrowDown",
      "ArrowLeft",
      "ArrowUp",
      "Home",
      "End",
    ];
    if (!keys.includes(event.key)) return;
    event.preventDefault();
    const current = themeOptions.findIndex(
      (option) => option.value === preferredMode,
    );
    const nextIndex =
      event.key === "Home"
        ? 0
        : event.key === "End"
          ? themeOptions.length - 1
          : event.key === "ArrowRight" || event.key === "ArrowDown"
            ? (current + 1) % themeOptions.length
            : (current - 1 + themeOptions.length) % themeOptions.length;
    const next = themeOptions[nextIndex];
    if (!next) return;
    void selectTheme(next.value, false).then(() => {
      document
        .querySelector<HTMLElement>(`[data-theme-value="${next.value}"]`)
        ?.focus();
    });
  }

  function handleGlobalKeydown(event: KeyboardEvent) {
    if (isTypingTarget(event.target)) {
      return;
    }

    if (event.key === "Escape" && showThemeMenu) {
      event.preventDefault();
      showThemeMenu = false;
    }
  }

  function handleGlobalClick(event: MouseEvent) {
    if (!showThemeMenu) return;

    const target = event.target as HTMLElement;
    const themeOrbit = document.querySelector(".theme-orbit");

    // Check if click is outside the theme switcher
    if (themeOrbit && !themeOrbit.contains(target)) {
      showThemeMenu = false;
    }
  }

  onMount(() => {
    const savedTheme = getTheme();
    if (savedTheme && savedTheme !== userPrefersMode.current) {
      setMode(savedTheme);
    }

    window.addEventListener("keydown", handleGlobalKeydown);
    window.addEventListener("click", handleGlobalClick, true); // Use capture phase
  });

  onDestroy(() => {
    window.removeEventListener("keydown", handleGlobalKeydown);
    window.removeEventListener("click", handleGlobalClick, true);

    if (themeTransitionTimeout) {
      clearTimeout(themeTransitionTimeout);
    }

    if (typeof document !== "undefined") {
      document.documentElement.classList.remove("theme-transitioning");
    }
  });

  function getCoords(option: ThemeOption) {
    if (direction === "up") {
      return { x: option.xUp, y: option.yUp };
    } else if (direction === "right") {
      return { x: option.xRight, y: option.yRight };
    }
    return { x: option.xDown, y: option.yDown };
  }
</script>

<div class="theme-orbit relative z-[101] h-10 w-10">
  <Button
    variant="ghost"
    size="icon"
    class="relative z-[102] h-10 w-10 rounded-full border border-border text-muted-foreground transition-[transform,box-shadow,border-color,color] duration-200 hover:border-foreground hover:text-foreground {showThemeMenu
      ? 'border-foreground text-foreground'
      : ''}"
    onclick={() => {
      showThemeMenu = !showThemeMenu;
    }}
    aria-expanded={showThemeMenu}
    aria-controls="theme-options"
    title={`Theme: ${preferredMode}`}
  >
    <ThemeButtonIcon
      class={`h-4 w-4 transition-transform duration-200 ${showThemeMenu ? "scale-110" : ""}`}
    ></ThemeButtonIcon>
  </Button>

  <div
    id="theme-options"
    class="theme-orbit__menu"
    data-direction={direction}
    role="radiogroup"
    aria-label="Theme options"
    aria-hidden={!showThemeMenu}
  >
    {#each themeOptions as option}
      {@const OptionIcon = option.icon}
      {@const coords = getCoords(option)}
      <Button
        variant="ghost"
        size="icon"
        class="theme-orbit__option z-[102] h-10 w-10 rounded-full border border-border bg-background text-muted-foreground shadow-lg"
        data-open={showThemeMenu}
        data-active={preferredMode === option.value}
        data-direction={direction}
        style={`--theme-x: ${coords.x}; --theme-y: ${coords.y};`}
        onclick={() => selectTheme(option.value)}
        title={option.label}
        aria-label={option.label}
        role="radio"
        aria-checked={preferredMode === option.value}
        tabindex={showThemeMenu && preferredMode === option.value ? 0 : -1}
        data-theme-value={option.value}
        onkeydown={handleThemeKeys}
      >
        <OptionIcon class="h-4 w-4"></OptionIcon>
      </Button>
    {/each}
  </div>
</div>

<style>
  .theme-orbit__menu {
    position: absolute;
    inset: 0;
    pointer-events: none;
  }

  :global(.theme-orbit__option) {
    position: absolute;
    top: 0;
    right: 0;
    pointer-events: none;
    opacity: 0;
    transform: translate3d(0, 0, 0) scale(0.72);
    transform-origin: top right;
    transition:
      transform 220ms cubic-bezier(0.22, 1, 0.36, 1),
      opacity 160ms ease,
      background-color 180ms ease,
      border-color 180ms ease,
      color 180ms ease,
      box-shadow 180ms ease;
    will-change: transform, opacity;
  }

  :global(.theme-orbit__option[data-direction="up"]) {
    transform-origin: bottom right;
  }

  :global(.theme-orbit__option[data-direction="right"]) {
    transform-origin: bottom left;
  }

  :global(.theme-orbit__option[data-open="true"]) {
    pointer-events: auto;
    opacity: 1;
    transform: translate3d(var(--theme-x), var(--theme-y), 0) scale(1);
  }

  :global(.theme-orbit__option[data-open="true"][data-direction="down"]:hover) {
    transform: translate3d(var(--theme-x), calc(var(--theme-y) - 2px), 0)
      scale(1);
  }

  :global(.theme-orbit__option[data-open="true"][data-direction="up"]:hover) {
    transform: translate3d(var(--theme-x), calc(var(--theme-y) + 2px), 0)
      scale(1);
  }

  :global(
    .theme-orbit__option[data-open="true"][data-direction="right"]:hover
  ) {
    transform: translate3d(
        calc(var(--theme-x) + 2px),
        calc(var(--theme-y) - 2px),
        0
      )
      scale(1);
  }

  :global(.theme-orbit__option[data-open="true"]:active) {
    transform: translate3d(var(--theme-x), var(--theme-y), 0) scale(0.98);
  }

  :global(.theme-orbit__option[data-active="true"]) {
    border-color: var(--foreground);
    background: var(--foreground);
    color: var(--background);
  }

  @media (prefers-reduced-motion: reduce) {
    :global(.theme-orbit__option) {
      transition: none;
    }
  }
</style>
