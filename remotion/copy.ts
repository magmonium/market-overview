import BN from './copy.bn.json';
import EN from './copy.en.json';

/**
 * The label tables.
 *
 * ⚠️ **A label table is not part of the facts bundle, and must not become part of it.** Ticket 20's
 * parity rule rests on both editions reading the *same immutable bundle* — that is what makes it
 * impossible for the two to disagree about a number. The language therefore travels as a render prop
 * alongside the bundle, never inside it.
 */

export type Language = 'bn' | 'en';

export type Copy = {
  indexes: Record<string, string>;
  windows: Record<string, string>;
  blocks: Record<string, string>;
  sectors: Record<string, string>;
  sectors_columns: Record<string, string>;
  leaders: Record<string, string>;
  most_active: Record<string, string>;
  breadth: Record<string, string>;
  dma: Record<string, string>;
  flows: Record<string, string>;
  dependencies: Record<string, string>;
  kinds: Record<string, string>;
  calendar: Record<string, string>;
  furniture: Record<string, string>;
  disclosure: string;
};

export const TABLES: Record<Language, Copy> = {
  bn: BN as Copy,
  en: EN as Copy,
};

export const tableFor = (lang: Language): Copy => TABLES[lang] ?? TABLES.bn;
