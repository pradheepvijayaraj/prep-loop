// @vitest-environment jsdom

import { render } from "@testing-library/svelte";
import { describe, expect, it } from "vitest";
import MathText from "$lib/components/math-text.svelte";
import maths2013 from "../../../static/upsc/mains-maths1/2013.json";

describe("MathText", () => {
  it("renders mixed prose and matrix LaTeX instead of falling back to raw text", () => {
    const source = maths2013.questions[0]!.question;
    const { container } = render(MathText, { props: { text: source } });

    expect(container.querySelectorAll(".katex").length).toBeGreaterThan(10);
    expect(container.querySelector(".mtable")).not.toBeNull();
    expect(container.textContent).not.toContain("$A=\\begin{pmatrix}");
  });

  it("renders several inline expressions and an integral in one question", () => {
    const source = String.raw`Let $A^{*}$ be the adjoint. Show $AA^{*}$ is real. Evaluate $\displaystyle\int_{0}^{1}\left(2x\sin\frac{1}{x}-\cos\frac{1}{x}\right)\,dx$.`;
    const { container } = render(MathText, { props: { text: source } });

    expect(container.querySelectorAll(".katex")).toHaveLength(3);
    expect(container.textContent).not.toContain("\\displaystyle");
    expect(container.textContent).not.toContain("$AA^{*}$");
  });

  it("keeps ordinary prose intact while removing a bare figure-list marker", () => {
    const source = "Question text\n1. ![Diagram](/upsc/assets/figure.png)";
    const { container } = render(MathText, { props: { text: source } });

    expect(container.textContent).toContain("Question text");
    expect(container.textContent).not.toContain("1.");
    expect(container.querySelector("img")?.getAttribute("src")).toBe(
      "/upsc/assets/figure.png",
    );
  });

  it("keeps labelled statement equations on the same rendered line", () => {
    const source = String.raw`For two distinct real numbers $x$ and $y$, which is bigger?
Statement I :
$x^2 < y < 1$
Statement II :
$y < \sqrt{x} < 1$`;
    const { container } = render(MathText, { props: { text: source } });
    const lines = Array.from(
      container.querySelectorAll<HTMLElement>(".math-text__line"),
    );
    const statementOne = lines.find((line) =>
      line.textContent?.startsWith("Statement I :"),
    );
    const statementTwo = lines.find((line) =>
      line.textContent?.startsWith("Statement II :"),
    );

    expect(lines).toHaveLength(3);
    expect(statementOne?.querySelector(".katex")).not.toBeNull();
    expect(statementTwo?.querySelector(".katex")).not.toBeNull();
  });

  it("does not merge plural list headings with their first item", () => {
    const source = "Statements:\n1. Some men are great.\n2. Some men are wise.";
    const { container } = render(MathText, { props: { text: source } });
    const lines = Array.from(
      container.querySelectorAll<HTMLElement>(".math-text__line"),
    );

    expect(lines).toHaveLength(3);
    expect(lines[0]?.textContent).toBe("Statements:");
    expect(lines[1]?.textContent).toBe("1. Some men are great.");
  });
});
