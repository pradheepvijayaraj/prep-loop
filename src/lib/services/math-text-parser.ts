import katex from "katex";

const MATH_CHUNK = /(\$\$[\s\S]+?\$\$|\$[^$]+\$)/;

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function mapOutsideMath(input: string, fn: (plain: string) => string): string {
  return input
    .split(MATH_CHUNK)
    .map((chunk, i) => (i % 2 === 1 ? chunk : fn(chunk)))
    .join("");
}

/** $7$ $16$ $48.1$ → plain digits so options match body font. */
function unwrapSimpleMath(input: string): string {
  return input.replace(/\$([+-]?\d+(?:\.\d+)?)\$/g, "$1");
}

/**
 * Drop spurious list markers left when SuperKalam used "1. ![fig]"
 * or when a converter left a bare "1." line above a figure.
 * (RegExp ctor — TS misparses /(?=!\[)/ literals.)
 */
function stripFigureListMarkers(input: string): string {
  let s = input;
  s = s.replace(new RegExp(String.raw`^\s*\d+\.\s*(?=!\[)`, "gm"), "");
  s = s.replace(new RegExp(String.raw`^\s*\d+\.\s*\n(?=\s*!\[)`, "gm"), "");
  s = s.replace(new RegExp(String.raw`^\s*\d+\.\s*(?=\u0000IMG)`, "gm"), "");
  s = s.replace(
    new RegExp(String.raw`^\s*\d+\.\s*$\n(?=\s*\u0000IMG)`, "gm"),
    "",
  );
  return s;
}

function isDisplayEnv(tex: string): boolean {
  return /\\begin\{(p?matrix|b?matrix|vmatrix|Vmatrix|cases|aligned|align\*?|array|gather\*?)/.test(
    tex,
  );
}

function isContinuationLabel(line: string): boolean {
  return /^(?:(?:statement|conclusion)\s*(?:[- ]\s*(?:[ivxlcdm]+|\d+))?|question)\s*:\s*$/i.test(
    line,
  );
}

function isStandaloneDisplayMath(line: string): boolean {
  const displayMatch = line.match(/^\$\$([\s\S]+)\$\$$/);
  const inlineMatch = line.match(/^\$([^$]+)\$$/);
  const tex = displayMatch?.[1] ?? inlineMatch?.[1] ?? "";
  return Boolean(tex && isDisplayEnv(tex));
}

/**
 * OCR and PDF extraction often place a labelled statement's content on the
 * next line. Rejoin that continuation so "Statement I: $x < y$" renders as
 * one semantic line. Keep matrix-like display expressions on their own row.
 */
function mergeLabelContinuations(lines: string[]): string[] {
  const merged: string[] = [];

  for (let index = 0; index < lines.length; index++) {
    const line = lines[index]!;
    const next = lines[index + 1];
    if (next && isContinuationLabel(line) && !isStandaloneDisplayMath(next)) {
      merged.push(`${line} ${next}`);
      index += 1;
    } else {
      merged.push(line);
    }
  }

  return merged;
}

function shouldDisplay(
  tex: string,
  fullLine: string,
  matchStart: number,
  matchEnd: number,
  explicitDisplay: boolean,
): boolean {
  if (explicitDisplay) return true;
  if (!isDisplayEnv(tex)) return false;

  const before = fullLine
    .slice(0, matchStart)
    .replace(/^\s*(\([a-e]\)|\((?:i{1,3}|iv|v|I{1,3}|IV|V)\))\s*/i, "")
    .trim();
  const after = fullLine
    .slice(matchEnd)
    .replace(/^\s*[.,;:…]*\s*$/u, "")
    .trim();

  return !before && !after;
}

function renderMath(tex: string, display: boolean): string {
  try {
    return katex.renderToString(tex, {
      displayMode: display,
      throwOnError: false,
      strict: "ignore",
      trust: false,
      output: "html",
      fleqn: false,
    });
  } catch {
    return escapeHtml(`$${tex}$`);
  }
}

function extractMarkdownImages(input: string): {
  text: string;
  images: string[];
} {
  const images: string[] = [];
  const text = input.replace(
    /!\[([^\]]*)\]\(([^)\s]+)\)/g,
    (_full, alt: string, src: string) => {
      const i = images.length;
      const safeSrc = escapeHtml(String(src || "").trim());
      const safeAlt = escapeHtml(String(alt || "Figure").trim() || "Figure");
      images.push(
        `<img class="math-text__img" src="${safeSrc}" alt="${safeAlt}" loading="lazy" decoding="async" />`,
      );
      return `\u0000IMG${i}\u0000`;
    },
  );
  return { text, images };
}

function restoreImagePlaceholders(html: string, images: string[]): string {
  return html.replace(/\u0000IMG(\d+)\u0000/g, (_m, idx: string) => {
    return images[Number(idx)] ?? "";
  });
}

function renderSegment(input: string): string {
  // Re-run bold in a safer way: extract ** before escape
  if (!input) return "";
  const boldParts: string[] = [];
  const withBoldPlaceholders = input.replace(
    /\*\*([^*]+)\*\*/g,
    (_m, inner: string) => {
      const i = boldParts.length;
      boldParts.push(inner);
      return `\u0000BOLD${i}\u0000`;
    },
  );
  const { text: withoutImgs, images } =
    extractMarkdownImages(withBoldPlaceholders);
  let work = stripFigureListMarkers(withoutImgs);

  const parts: string[] = [];
  const re = /\$\$([\s\S]+?)\$\$|\$((?:\\.|[^$])+?)\$/g;
  let last = 0;
  let match: RegExpExecArray | null;

  while ((match = re.exec(work)) !== null) {
    if (match.index > last) {
      parts.push(escapeHtml(work.slice(last, match.index)));
    }
    const explicitDisplay = match[1] != null;
    const tex = (explicitDisplay ? match[1] : match[2]) ?? "";
    const end = match.index + match[0].length;
    const display = shouldDisplay(tex, work, match.index, end, explicitDisplay);
    parts.push(renderMath(tex, display));
    last = end;
  }

  if (last < work.length) {
    parts.push(escapeHtml(work.slice(last)));
  }

  let html = restoreImagePlaceholders(parts.join(""), images);
  html = html.replace(/\u0000BOLD(\d+)\u0000/g, (_m, idx: string) => {
    return `<strong>${escapeHtml(boldParts[Number(idx)] ?? "")}</strong>`;
  });
  return html;
}

function splitParts(raw: string): string[] {
  let s = (raw ?? "").replace(/\r\n/g, "\n").trim();
  if (!s) return [];

  s = mapOutsideMath(s, (plain) =>
    plain.replace(/(\([a-e]\))\s*(\(i\))/gi, "$1 $2"),
  );
  s = mapOutsideMath(s, (plain) =>
    plain.replace(/(\([a-e]\))\s*(\((?:ii|iii|iv|II|III|IV)\))/g, "\n$2"),
  );
  s = mapOutsideMath(s, (plain) =>
    plain.replace(/(?<!\n)\s+(\([a-e]\))\s+/g, "\n$1 "),
  );
  s = mapOutsideMath(s, (plain) =>
    plain.replace(/\s+(\((?:ii|iii|iv|II|III|IV)\))\s+/g, "\n$1 "),
  );
  s = mapOutsideMath(s, (plain) =>
    plain.replace(/;\s*(\([IVX]+\))\s*/g, "\n$1 "),
  );
  s = mapOutsideMath(s, (plain) =>
    plain.replace(/;?\s+\b(?:and|or)\s*(?=\n\()/gi, ""),
  );

  let lines = mergeLabelContinuations(
    s
      .split(/\n+/)
      .map((line) => line.trim())
      .filter(Boolean),
  );

  const peeled: string[] = [];
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]!;
    const next = lines[i + 1] ?? "";
    const nextIsIi = /^\(ii\)/i.test(next);
    const isPartI = /^\([a-e]\)\s+\(i\)\s+/i.test(line);
    const isBareI = /^\(i\)\s+/i.test(line);

    if (nextIsIi && !isPartI && !isBareI && /\(i\)\s+/.test(line)) {
      const m = line.match(/^(.*?)(\s+)(\(i\)\s+[\s\S]+)$/i);
      if (m && (m[1] ?? "").trim().length > 0) {
        peeled.push((m[1] ?? "").trim());
        peeled.push((m[3] ?? "").trim());
        continue;
      }
    }
    peeled.push(line);
  }

  return peeled;
}

function isRomanSubLine(line: string): boolean {
  return (
    /^\((?:i{1,3}|iv|v|I{1,3}|IV|V)\)/.test(line) && !/^\([a-e]\)/.test(line)
  );
}

function isTableSepLine(line: string): boolean {
  const t = line.trim();
  if (!t.includes("-")) return false;
  // GFM separator: |---|:---:| or ---|---
  return /^[:\s|.-]+$/.test(t);
}

function isTableRowLine(line: string): boolean {
  const t = line.trim();
  if (!t.includes("|")) return false;
  // At least two cells worth of pipes
  const pipes = (t.match(/\|/g) ?? []).length;
  if (pipes < 1) return false;
  // Avoid treating prose "a | b" mid-sentence as a table alone
  return t.startsWith("|") || t.endsWith("|") || pipes >= 2;
}

function parseCells(line: string): string[] {
  let t = line.trim();
  if (t.startsWith("|")) t = t.slice(1);
  if (t.endsWith("|")) t = t.slice(0, -1);
  return t.split("|").map((c) => c.trim());
}

function renderTable(blockLines: string[]): string {
  // Drop separator rows; first row is header if a sep exists anywhere
  const hasSep = blockLines.some(isTableSepLine);
  const dataLines = blockLines.filter((l) => !isTableSepLine(l));
  if (dataLines.length === 0) return "";

  const rows = dataLines.map(parseCells);
  const colCount = Math.max(...rows.map((r) => r.length), 1);
  const normalized = rows.map((r) => {
    const copy = [...r];
    while (copy.length < colCount) copy.push("");
    return copy.slice(0, colCount);
  });

  const head = hasSep ? normalized[0] : null;
  const body = hasSep ? normalized.slice(1) : normalized;

  let html = `<div class="math-text__table-wrap"><table class="math-text__table">`;
  if (head) {
    html += "<thead><tr>";
    for (const cell of head) {
      html += `<th>${renderSegment(cell)}</th>`;
    }
    html += "</tr></thead>";
  }
  html += "<tbody>";
  for (const row of body) {
    html += "<tr>";
    for (const cell of row) {
      html += `<td>${renderSegment(cell)}</td>`;
    }
    html += "</tr>";
  }
  html += "</tbody></table></div>";
  return html;
}

function renderLine(line: string): string {
  const cls = isRomanSubLine(line)
    ? "math-text__line math-text__line--sub"
    : "math-text__line";
  return `<p class="${cls}">${renderSegment(line)}</p>`;
}

export function renderMathText(text: string): string {
  try {
    let raw = unwrapSimpleMath(text ?? "");
    raw = stripFigureListMarkers(raw);
    const lines = splitParts(raw);
    if (lines.length === 0) return "";

    const out: string[] = [];
    let i = 0;
    let guard = 0;
    const maxSteps = Math.max(lines.length * 4, 64);
    while (i < lines.length) {
      guard++;
      if (guard > maxSteps) break;
      const line = lines[i]!;
      // Start of a markdown table: row followed by sep or another row
      if (
        isTableRowLine(line) &&
        i + 1 < lines.length &&
        (isTableSepLine(lines[i + 1]!) || isTableRowLine(lines[i + 1]!))
      ) {
        const block: string[] = [];
        while (
          i < lines.length &&
          (isTableRowLine(lines[i]!) || isTableSepLine(lines[i]!))
        ) {
          guard++;
          if (guard > maxSteps) break;
          block.push(lines[i]!);
          i++;
        }
        out.push(renderTable(block));
        continue;
      }
      // Drop bare numbered stubs ("1.") that are not real content
      if (/^\d+\.\s*$/.test(line)) {
        i++;
        continue;
      }
      out.push(renderLine(line));
      i++;
    }
    return out.join("");
  } catch {
    // Never block the practice session on a render edge-case
    return escapeHtml(text ?? "");
  }
}
