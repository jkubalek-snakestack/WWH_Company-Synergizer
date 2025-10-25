import { z } from "zod";

export const visibilityEnum = z.enum(["PUBLIC", "PARTNER", "PRIVATE"]);
export const urgencyEnum = z.enum(["LOW", "MED", "HIGH"]);
export const capacityEnum = z.enum(["LOW", "MED", "HIGH"]);

const WWH_KEYS = [
  "Education",
  "Health",
  "Community Dev",
  "Energy",
  "Finance",
  "Food/Water",
  "Logistics",
  "Housing",
  "Safety",
] as const;

const WWH_KEY_ALIAS_MAP: Record<string, (typeof WWH_KEYS)[number]> = {
  education: "Education",
  learning: "Education",
  "health care": "Health",
  healthcare: "Health",
  health: "Health",
  "community development": "Community Dev",
  "community dev": "Community Dev",
  community: "Community Dev",
  "energy access": "Energy",
  energy: "Energy",
  "clean energy": "Energy",
  finance: "Finance",
  funding: "Finance",
  investment: "Finance",
  "food security": "Food/Water",
  water: "Food/Water",
  "food": "Food/Water",
  "food/water": "Food/Water",
  logistics: "Logistics",
  supply: "Logistics",
  "supply chain": "Logistics",
  housing: "Housing",
  shelter: "Housing",
  safety: "Safety",
  security: "Safety",
};

const canonicalLookup = new Map(
  WWH_KEYS.map((key) => [key.toLowerCase(), key] as const),
);

function normalizeStringList(
  values: readonly string[] | undefined,
  { lowercase }: { lowercase: boolean },
): string[] {
  if (!values?.length) {
    return [];
  }

  const seen = new Set<string>();
  const normalized: string[] = [];

  for (const raw of values) {
    const trimmed = raw?.trim();
    if (!trimmed) {
      continue;
    }

    const key = lowercase ? trimmed.toLowerCase() : trimmed;
    if (seen.has(key)) {
      continue;
    }

    seen.add(key);
    normalized.push(key);
  }

  return normalized;
}

export function normalizeTags(tags: readonly string[] | undefined): string[] {
  return normalizeStringList(tags, { lowercase: true });
}

export function normalizeCapabilities(
  capabilities: readonly string[] | undefined,
): string[] {
  return normalizeStringList(capabilities, { lowercase: true });
}

export function normalizeWwhKeys(keys: readonly string[] | undefined): string[] {
  if (!keys?.length) {
    return [];
  }

  const seen = new Set<string>();
  const normalized: string[] = [];

  for (const raw of keys) {
    const value = raw?.trim();
    if (!value) {
      continue;
    }

    const lower = value.toLowerCase();
    const canonical =
      WWH_KEY_ALIAS_MAP[lower] ?? canonicalLookup.get(lower) ?? value;
    if (seen.has(canonical)) {
      continue;
    }

    seen.add(canonical);
    normalized.push(canonical);
  }

  return normalized;
}

const contactPrivacyEnum = z.enum(["PARTNER", "PRIVATE"]);

export const needSchema = z
  .object({
    title: z.string().min(1),
    description: z.string().optional(),
    tags: z.array(z.string()).default([]),
    urgency: urgencyEnum.default("MED"),
    visibility: visibilityEnum.default("PARTNER"),
  })
  .transform((need) => ({
    ...need,
    tags: normalizeTags(need.tags),
  }));

export const offerSchema = z
  .object({
    title: z.string().min(1),
    description: z.string().optional(),
    tags: z.array(z.string()).default([]),
    capacity: capacityEnum.default("MED"),
    visibility: visibilityEnum.default("PARTNER"),
  })
  .transform((offer) => ({
    ...offer,
    tags: normalizeTags(offer.tags),
  }));

export const contactSchema = z.object({
  name: z.string().min(1),
  role: z.string().optional(),
  email: z.string().email().optional(),
  phone: z.string().optional(),
  privacyLevel: contactPrivacyEnum.optional(),
});

export const companySchema = z
  .object({
    name: z.string().min(1),
    region: z.string().optional(),
    mission: z.string().optional(),
    wwhKeys: z.array(z.string()).default([]),
    capabilities: z.array(z.string()).default([]),
  })
  .transform((company) => ({
    ...company,
    wwhKeys: normalizeWwhKeys(company.wwhKeys),
    capabilities: normalizeCapabilities(company.capabilities),
  }));

export const companyProfileSchema = z
  .object({
    company: companySchema,
    needs: z.array(needSchema).default([]),
    offers: z.array(offerSchema).default([]),
    contacts: z.array(contactSchema).default([]),
  })
  .transform((profile) => ({
    ...profile,
    needs: profile.needs ?? [],
    offers: profile.offers ?? [],
    contacts: profile.contacts ?? [],
  }));

export type CompanyProfile = z.infer<typeof companyProfileSchema>;
export type CompanyInput = z.infer<typeof companySchema>;
export type NeedInput = z.infer<typeof needSchema>;
export type OfferInput = z.infer<typeof offerSchema>;
export type ContactInput = z.infer<typeof contactSchema>;
