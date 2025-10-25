import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import {
  compileProfile,
  type ChatCompletionsClient,
} from "@/server/llm/compileProfile";

const createMockClient = (response: unknown): ChatCompletionsClient => ({
  chat: {
    completions: {
      create: vi.fn().mockResolvedValue({
        choices: [{
          message: {
            content: JSON.stringify(response, null, 2),
          },
        }],
      }),
    },
  },
});

describe("compileProfile", () => {
  const originalModel = process.env.OPENAI_MODEL;

  beforeEach(() => {
    process.env.OPENAI_MODEL = "test-model";
  });

  afterEach(() => {
    process.env.OPENAI_MODEL = originalModel;
  });

  it("parses and redacts contact PII when privacy is missing", async () => {
    const mockResponse = {
      company: {
        name: "Aqua Aid Coalition",
        mission: "Provide sustainable water access",
        region: "East Africa",
        capabilities: ["Water Systems", "Training"],
        wwhKeys: ["food/water", "community development"],
      },
      needs: [
        {
          title: "Satellite mapping support",
          urgency: "HIGH",
        },
      ],
      offers: [
        {
          title: "Water access training",
          capacity: "MED",
          tags: ["Water", "TRAINING"],
        },
      ],
      contacts: [
        {
          name: "Maya Rivers",
          role: "Program Lead",
          email: "maya@example.org",
          phone: "+1-555-0100",
        },
      ],
    };

    const mockClient = createMockClient(mockResponse);

    const profile = await compileProfile("Sample narrative", {
      client: mockClient,
    });

    expect(mockClient.chat.completions.create).toHaveBeenCalledWith(
      expect.objectContaining({
        model: "test-model",
      }),
    );

    expect(profile.company.wwhKeys).toEqual([
      "Food/Water",
      "Community Dev",
    ]);
    expect(profile.company.capabilities).toEqual(["water systems", "training"]);
    expect(profile.contacts[0]).toEqual({
      name: "Maya Rivers",
      role: "Program Lead",
    });
  });

  it("normalizes defaults and preserves explicit privacy levels", async () => {
    const mockResponse = {
      company: {
        name: "Grid Harmony Labs",
        region: "Sub-Saharan Africa",
        mission: "Enable resilient microgrids",
        capabilities: ["Grid Analytics", "Demand Response"],
        wwhKeys: ["Energy", "Safety"],
      },
      needs: [
        {
          title: "Capital partners",
          description: "Support expansion",
          tags: ["Financing", "PARTNERS"],
        },
      ],
      offers: [
        {
          title: "Grid analytics",
          description: "Real-time load balancing",
          tags: ["Data"],
          capacity: "HIGH",
          visibility: "PUBLIC",
        },
      ],
      contacts: [
        {
          name: "Luis Chan",
          role: "CTO",
          email: "luis@gridharmony.example",
          privacyLevel: "PARTNER",
        },
      ],
    };

    const mockClient = createMockClient(mockResponse);

    const profile = await compileProfile("Another narrative", {
      client: mockClient,
    });

    expect(profile.company.wwhKeys).toEqual([
      "Energy",
      "Safety",
    ]);
    expect(profile.company.capabilities).toEqual([
      "grid analytics",
      "demand response",
    ]);
    expect(profile.needs[0]).toMatchObject({
      tags: ["financing", "partners"],
      urgency: "MED",
      visibility: "PARTNER",
    });
    expect(profile.contacts[0]).toMatchObject({
      email: "luis@gridharmony.example",
      privacyLevel: "PARTNER",
    });
  });
});
