"use server";

import OpenAI from "openai";
import { z } from "zod";

const DEFAULT_MODEL = "gpt-4o-mini";

export type ChatCompletionsClient = {
  chat: {
    completions: {
      create: (args: {
        model: string;
        messages: { role: "system" | "user" | "assistant"; content: string }[];
        temperature?: number;
      }) => Promise<{
        choices: {
          message?: {
            content?: string | null;
          };
        }[];
      }>;
    };
  };
};

const actorSchema = z.object({
  name: z.string().min(1),
  role: z.string().optional(),
  companyId: z.string().optional(),
  orgId: z.string().optional(),
  visibility: z.string().optional(),
});

const stepSchema = z.object({
  order: z.number().int().min(1),
  title: z.string().min(1),
  details: z.string().min(1),
  key: z.string().regex(/^Key[1-9]$/, {
    message: "Steps must reference WWH keys as Key1-Key9",
  }),
});

const timelineSchema = z.object({
  phase: z.string().min(1),
  goals: z.array(z.string().min(1)).default([]),
});

const riskSchema = z.object({
  risk: z.string().min(1),
  mitigation: z.string().min(1),
});

const alignmentSchema = z.object({
  key: z.string().regex(/^Key[1-9]$/, {
    message: "Alignment entries must reference WWH keys as Key1-Key9",
  }),
  why: z.string().min(1),
});

const playbookSchema = z.object({
  summary: z.string().min(1),
  actors: z.array(actorSchema).default([]),
  angles: z.array(z.string().min(1)).default([]),
  steps: z.array(stepSchema).min(1),
  timeline: z.array(timelineSchema).default([]),
  risks: z.array(riskSchema).default([]),
  collateral: z.array(z.string().min(1)).default([]),
  wwh_alignment: z.array(alignmentSchema).default([]),
});

const adjustmentsSchema = playbookSchema.partial();

export type Playbook = z.infer<typeof playbookSchema>;
export type PlaybookAdjustments = z.infer<typeof adjustmentsSchema>;

export type GeneratePlaybookInput = {
  opportunity: Record<string, unknown>;
  policy: Record<string, unknown>;
  contacts: Array<Record<string, unknown>>;
  adjustments?: PlaybookAdjustments | null;
};

export type GeneratePlaybookOptions = {
  client?: ChatCompletionsClient;
  model?: string;
};

function createClient(): ChatCompletionsClient {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    throw new Error("Missing OPENAI_API_KEY environment variable");
  }

  return new OpenAI({
    apiKey,
    baseURL: process.env.OPENAI_BASE_URL,
  });
}

function extractJsonPayload(content: string): unknown {
  let trimmed = content.trim();

  if (trimmed.startsWith("```")) {
    trimmed = trimmed.replace(/^```(?:json)?\s*/i, "");
    const fenceIndex = trimmed.lastIndexOf("```");
    if (fenceIndex !== -1) {
      trimmed = trimmed.slice(0, fenceIndex);
    }
  }

  return JSON.parse(trimmed);
}

function applyAdjustments(base: Playbook, adjustments: PlaybookAdjustments | null | undefined): Playbook {
  if (!adjustments) {
    return base;
  }

  const parsed = adjustmentsSchema.parse(adjustments);
  const merged: Playbook = { ...base };

  (Object.keys(parsed) as (keyof PlaybookAdjustments)[]).forEach((key) => {
    const value = parsed[key];
    if (value !== undefined) {
      (merged as Record<string, unknown>)[key] = value as unknown;
    }
  });

  if (merged.steps.length > 1) {
    merged.steps = [...merged.steps].sort((a, b) => a.order - b.order);
  }

  return merged;
}

export async function generatePlaybook(
  input: GeneratePlaybookInput,
  options: GeneratePlaybookOptions = {},
): Promise<Playbook> {
  const { opportunity, policy, contacts, adjustments } = input;
  if (!opportunity) {
    throw new Error("Opportunity is required");
  }
  if (!policy) {
    throw new Error("Policy configuration is required");
  }

  const client = options.client ?? createClient();
  const model = options.model ?? process.env.OPENAI_MODEL ?? DEFAULT_MODEL;

  const completion = await client.chat.completions.create({
    model,
    temperature: 0.2,
    messages: [
      {
        role: "system",
        content:
          "You are a synergy playbook generator. Produce operator-ready action plans. Output JSON only and conform to the schema.",
      },
      {
        role: "user",
        content: [
          "Context:",
          `Opportunity: ${JSON.stringify(opportunity, null, 2)}`,
          `Policy: ${JSON.stringify(policy, null, 2)}`,
          `Contacts: ${JSON.stringify(contacts, null, 2)}`,
          `Adjustments: ${JSON.stringify(adjustments ?? {}, null, 2)}`,
          "Schema:",
          JSON.stringify(
            {
              summary: "string",
              actors: [
                {
                  name: "string",
                  role: "string?",
                  companyId: "string?",
                  orgId: "string?",
                  visibility: "string?",
                },
              ],
              angles: ["string"],
              steps: [
                {
                  order: 1,
                  title: "string",
                  details: "string",
                  key: "Key1..Key9",
                },
              ],
              timeline: [
                {
                  phase: "string",
                  goals: ["string"],
                },
              ],
              risks: [
                {
                  risk: "string",
                  mitigation: "string",
                },
              ],
              collateral: ["string"],
              wwh_alignment: [
                {
                  key: "Key1..Key9",
                  why: "string",
                },
              ],
            },
            null,
            2,
          ),
          "WWH mapping:",
          "Key1: Education, Key2: Health, Key3: Community Dev, Key4: Energy, Key5: Finance, Key6: Food/Water, Key7: Logistics, Key8: Housing, Key9: Safety",
          "Instructions:",
          "- Reflect the policy weights in the rationale for steps and priorities.",
          "- Reference contacts only by provided fields; do not invent new personal details.",
          "- Ensure each step includes an order and the most relevant WWH key (Key1-Key9).",
          "- Keep responses concise and actionable.",
          "Return JSON only.",
        ].join("\n\n"),
      },
    ],
  });

  const content = completion.choices[0]?.message?.content;
  if (!content) {
    throw new Error("OpenAI response did not include content");
  }

  const parsed = extractJsonPayload(content);
  const playbook = playbookSchema.parse(parsed);
  return applyAdjustments(playbook, adjustments);
}

export type GeneratePlaybookResult = Awaited<ReturnType<typeof generatePlaybook>>;
