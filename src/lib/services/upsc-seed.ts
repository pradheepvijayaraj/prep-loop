/**
 * Seed bundled UPSC CSE papers into SQLite.
 *
 * Re-imports when catalog contentVersion is newer than what is stored
 * on existing banks (metadata.contentVersion).
 */
import {
  deleteQuestionBank,
  getQuestionBanks,
  importQuestionBank,
} from "$lib/services/question-bank";
import { logError } from "$lib/services/logger";

export interface UpscCatalogEntry {
  path: string;
  name: string;
  exam: string;
  year: number;
  stage: string;
  paper: string;
  section: string;
  totalQuestions: number;
  defaultDuration: number;
  practiceMode: "mcq" | "descriptive";
  difficulty: string;
  contentVersion?: number;
}

interface UpscCatalogFile {
  contentVersion: number;
  papers: UpscCatalogEntry[];
}

const CATALOG_URL = "/upsc/catalog.json";

/** Expected seed shape version; bump with conversion script. */
export const UPSC_CONTENT_VERSION = 45;
let seedPromise: Promise<SeedResult> | null = null;

export interface SeedResult {
  imported: number;
  failed: number;
}

function bankContentVersion(metadataJson: string): number {
  try {
    const meta = JSON.parse(metadataJson) as { contentVersion?: unknown };
    return typeof meta.contentVersion === "number" ? meta.contentVersion : 0;
  } catch {
    return 0;
  }
}

function catalogEntryKey(entry: UpscCatalogEntry): string {
  return `${entry.section}:${entry.year}:${entry.paper}`;
}

function storedBankKey(metadataJson: string): string | null {
  try {
    const meta = JSON.parse(metadataJson) as {
      section?: unknown;
      year?: unknown;
      paper?: unknown;
    };
    if (
      typeof meta.section !== "string" ||
      typeof meta.year !== "number" ||
      typeof meta.paper !== "string"
    ) {
      return null;
    }
    return `${meta.section}:${meta.year}:${meta.paper}`;
  } catch {
    return null;
  }
}

export async function loadUpscCatalog(): Promise<UpscCatalogFile> {
  const response = await fetch(CATALOG_URL);
  if (!response.ok) {
    throw new Error(`Failed to load UPSC catalog (${response.status})`);
  }
  const data = (await response.json()) as UpscCatalogFile | UpscCatalogEntry[];
  // Back-compat: old catalogs were a bare array
  if (Array.isArray(data)) {
    return { contentVersion: 1, papers: data };
  }
  return {
    contentVersion: data.contentVersion ?? 1,
    papers: data.papers ?? [],
  };
}

/**
 * Ensure DB has current bundled UPSC papers.
 * Returns number of banks imported (0 if already up to date).
 */
export function seedUpscBanksIfNeeded(): Promise<SeedResult> {
  seedPromise ??= seedUpscBanks().finally(() => {
    seedPromise = null;
  });
  return seedPromise;
}

async function seedUpscBanks(): Promise<SeedResult> {
  const catalog = await loadUpscCatalog();
  const targetVersion = catalog.contentVersion || UPSC_CONTENT_VERSION;
  const existing = await getQuestionBanks();
  const upscBanks = existing.filter((bank) => bank.exam === "UPSC CSE");
  const expectedKeys = new Set(catalog.papers.map(catalogEntryKey));
  const currentKeys = new Set<string>();
  const staleBanks = upscBanks.filter((bank) => {
    const key = storedBankKey(bank.metadata);
    const stale =
      key === null ||
      !expectedKeys.has(key) ||
      bankContentVersion(bank.metadata) < targetVersion ||
      currentKeys.has(key);
    if (!stale && key) currentKeys.add(key);
    return stale;
  });
  const missingEntries = catalog.papers.filter(
    (entry) => !currentKeys.has(catalogEntryKey(entry)),
  );

  if (staleBanks.length === 0 && missingEntries.length === 0) {
    return { imported: 0, failed: 0 };
  }

  let failed = 0;
  for (let i = 0; i < staleBanks.length; i++) {
    const bank = staleBanks[i]!;
    try {
      await deleteQuestionBank(bank.id);
    } catch (error) {
      failed += 1;
      await logError(`Failed to delete bank ${bank.id} during reseed`, error);
    }
    // Yield so the window stays responsive during large reseeds (300+ banks).
    if (i % 10 === 9) {
      await new Promise((r) => setTimeout(r, 0));
    }
  }

  let imported = 0;
  for (let i = 0; i < missingEntries.length; i++) {
    const entry = missingEntries[i]!;
    try {
      const response = await fetch(`/upsc/${entry.path}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status} for ${entry.path}`);
      }
      const bank = JSON.parse(await response.text()) as {
        metadata?: Record<string, unknown>;
      };
      if (bank.metadata) {
        // The catalog version is authoritative. Stamping it into imported
        // metadata prevents a corrected corpus from being left behind in an
        // existing installation and avoids a reseed loop when individual
        // source files still carry the previous version.
        bank.metadata.contentVersion = targetVersion;
      }
      const result = await importQuestionBank(JSON.stringify(bank));
      if (result.success) {
        imported += 1;
      } else {
        failed += 1;
        await logError(
          `Failed to import ${entry.path}`,
          result.error ?? result.validationErrors,
        );
      }
    } catch (error) {
      failed += 1;
      await logError(`Failed to seed ${entry.path}`, error);
    }
    if (i % 10 === 9) {
      await new Promise((r) => setTimeout(r, 0));
    }
  }

  return { imported, failed };
}
