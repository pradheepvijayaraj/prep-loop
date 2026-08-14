/**
 * Fixed UPSC CSE navigation for the market-demand build.
 * Content is bundled under /static/upsc and seeded on first launch.
 */

/** Mains paper-type picker. Dual-paper optionals group Paper I + Paper II. */
export interface MainsPaperType {
  id: string;
  /** Short tile label */
  label: string;
  /** Short catalog description. */
  description: string;
  /** Section ids used in bank metadata / static paths. */
  sections: string[];
  /** When true, year list splits into Paper I / Paper II (sections[0]/[1]). */
  dualPaper?: boolean;
  /** Theory optional (vs Essay / GS). */
  optional?: boolean;
}

export const MAINS_PAPER_TYPES: MainsPaperType[] = [
  {
    id: "essay",
    label: "Essay",
    description: "Long-Form Argument and Expression",
    sections: ["mains-essay"],
  },
  {
    id: "gs1",
    label: "GS 1",
    description: "Culture, History, Society and Geography",
    sections: ["mains-gs1"],
  },
  {
    id: "gs2",
    label: "GS 2",
    description: "Governance, Polity and International Relations",
    sections: ["mains-gs2"],
  },
  {
    id: "gs3",
    label: "GS 3",
    description: "Economy, Environment, Technology and Security",
    sections: ["mains-gs3"],
  },
  {
    id: "gs4",
    label: "GS 4",
    description: "Ethics, Integrity and Aptitude",
    sections: ["mains-gs4"],
  },
  {
    id: "math",
    label: "Mathematics",
    description: "Optional Paper I and Paper II",
    sections: ["mains-maths1", "mains-maths2"],
    dualPaper: true,
    optional: true,
  },
];

export interface PrelimsPaperType {
  id: string;
  label: string;
  description: string;
  section: string;
}

export const PRELIMS_PAPER_TYPES: PrelimsPaperType[] = [
  {
    id: "gs1",
    label: "GS 1",
    description: "General Studies",
    section: "prelims-gs1",
  },
  {
    id: "csat",
    label: "CSAT",
    description: "Aptitude and Reasoning",
    section: "prelims-csat",
  },
];

export const ACTIVE_UPSC_SECTIONS = new Set([
  ...PRELIMS_PAPER_TYPES.map((paper) => paper.section),
  ...MAINS_PAPER_TYPES.flatMap((paper) => paper.sections),
]);
