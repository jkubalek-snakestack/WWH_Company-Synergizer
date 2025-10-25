"use server";

import { z } from "zod";

import { companyProfileSchema } from "@/lib/schema";
import { compileProfile } from "../llm/compileProfile";

const narrativeSchema = z.object({
  narrative: z.string().min(10, "Narrative must be at least 10 characters"),
});

export async function compileProfileAction(input: z.infer<typeof narrativeSchema>) {
  const { narrative } = narrativeSchema.parse(input);
  const compiled = await compileProfile(narrative);
  return companyProfileSchema.parse(compiled);
}
