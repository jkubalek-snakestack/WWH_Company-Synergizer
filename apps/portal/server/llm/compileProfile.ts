"use server";

import OpenAI from "openai";

import { companyProfileSchema, type CompanyProfile } from "@/lib/schema";

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

type CompileProfileOptions = {
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

function redactContacts(profile: CompanyProfile): CompanyProfile {
  const contacts = profile.contacts.map((contact) => {
    if (contact.privacyLevel) {
      return contact;
    }

    const { email, phone, ...rest } = contact;
    return rest;
  });

  return { ...profile, contacts };
}

export async function compileProfile(
  narrative: string,
  options: CompileProfileOptions = {},
): Promise<CompanyProfile> {
  if (!narrative || !narrative.trim()) {
    throw new Error("Narrative is required");
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
          "You convert company narratives into JSON that conforms exactly to the provided schema. Do not invent PII. Normalize tags. Derive wwhKeys using the provided mapping. Output JSON only.",
      },
      {
        role: "user",
        content: `${narrative.trim()}\n\nSchema:\n{\n  "company": {\n    "name": "string",\n    "region": "string?",\n    "mission": "string?",\n    "wwhKeys": ["string"],\n    "capabilities": ["string"]\n  },\n  "needs": [{\n    "title": "string",\n    "description": "string?",\n    "tags": ["string"],\n    "urgency": "LOW|MED|HIGH",\n    "visibility": "PUBLIC|PARTNER|PRIVATE"\n  }],\n  "offers": [{\n    "title": "string",\n    "description": "string?",\n    "tags": ["string"],\n    "capacity": "LOW|MED|HIGH",\n    "visibility": "PUBLIC|PARTNER|PRIVATE"\n  }],\n  "contacts": [{\n    "name": "string",\n    "role": "string?",\n    "email": "string?",\n    "phone": "string?",\n    "privacyLevel": "PARTNER|PRIVATE"\n  }]\n}\n\nWWH mapping:\nKey1: "Education"\nKey2: "Health"\nKey3: "Community Dev"\nKey4: "Energy"\nKey5: "Finance"\nKey6: "Food/Water"\nKey7: "Logistics"\nKey8: "Housing"\nKey9: "Safety"`,
      },
    ],
  });

  const content = completion.choices[0]?.message?.content;
  if (!content) {
    throw new Error("OpenAI response did not include content");
  }

  const parsed = extractJsonPayload(content);
  const profile = companyProfileSchema.parse(parsed);
  return redactContacts(profile);
}

export type CompileProfileResult = Awaited<ReturnType<typeof compileProfile>>;
