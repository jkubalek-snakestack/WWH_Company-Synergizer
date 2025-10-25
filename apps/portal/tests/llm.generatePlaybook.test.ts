import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import policy from "../config/policy.default.json";
import {
  generatePlaybook,
  type ChatCompletionsClient,
} from "@/server/llm/generatePlaybook";

const opportunity = {
  id: "opp-1",
  name: "Water + Energy village expansion",
  summary: "Extend water access and solar microgrids to partner villages",
  participants: ["aqua-aid-coalition", "grid-harmony-labs"],
  breakdown: {
    rationale: ["Shared infrastructure reduces per-site costs by 35%"],
    supporting_matches: [
      {
        source: "aqua-aid-coalition",
        target: "grid-harmony-labs",
        description: "Water distribution network ready for energy sensors",
      },
    ],
  },
  wwhKeys: ["Key6", "Key4"],
  score: 0.82,
};

const contacts = [
  {
    companyId: "company-a",
    name: "Maya Rivers",
    role: "Program Lead",
    email: "maya@example.org",
  },
  {
    companyId: "company-b",
    name: "Luis Chan",
    role: "CTO",
  },
];

const createMockClient = (response: unknown): ChatCompletionsClient => ({
  chat: {
    completions: {
      create: vi.fn().mockResolvedValue({
        choices: [
          {
            message: {
              content: JSON.stringify(response, null, 2),
            },
          },
        ],
      }),
    },
  },
});

describe("generatePlaybook", () => {
  const originalModel = process.env.OPENAI_MODEL;

  beforeEach(() => {
    process.env.OPENAI_MODEL = "test-model";
  });

  afterEach(() => {
    process.env.OPENAI_MODEL = originalModel;
  });

  it("parses responses and applies adjustments", async () => {
    const mockResponse = {
      summary: "Deploy a combined water-energy package across priority villages",
      actors: [
        { name: "Aqua Aid Coalition", role: "Operations" },
        { name: "Grid Harmony Labs", role: "Engineering" },
      ],
      angles: ["Joint infrastructure upgrade", "Community impact storytelling"],
      steps: [
        {
          order: 1,
          title: "Confirm shared deployment targets",
          details: "Validate top 5 villages leveraging policy weights for urgency.",
          key: "Key6",
        },
        {
          order: 2,
          title: "Bundle financing narrative",
          details: "Shape partner messaging around alignment bonus for Key1.",
          key: "Key1",
        },
      ],
      timeline: [
        {
          phase: "Week 1",
          goals: ["Finalize target list", "Assign joint leads"],
        },
      ],
      risks: [
        {
          risk: "Delays in customs clearance",
          mitigation: "Use warm contacts to expedite paperwork.",
        },
      ],
      collateral: ["intro email", "impact one-pager"],
      wwh_alignment: [
        { key: "Key6", why: "Secures water resilience" },
        { key: "Key4", why: "Delivers clean energy stability" },
      ],
    };

    const adjustments = {
      summary: "Launch integrated water + energy pilots",
      steps: [
        {
          order: 2,
          title: "Deploy microgrid hardware",
          details: "Install controllers in tandem with new pumps.",
          key: "Key4",
        },
        {
          order: 1,
          title: "Village readiness alignment",
          details: "Confirm local operator training schedules.",
          key: "Key6",
        },
      ],
    };

    const client = createMockClient(mockResponse);

    const playbook = await generatePlaybook(
      { opportunity, policy, contacts, adjustments },
      { client },
    );

    expect(client.chat.completions.create).toHaveBeenCalledWith(
      expect.objectContaining({
        model: "test-model",
      }),
    );

    expect(playbook.summary).toBe(adjustments.summary);
    expect(playbook.steps).toEqual([
      {
        order: 1,
        title: "Village readiness alignment",
        details: "Confirm local operator training schedules.",
        key: "Key6",
      },
      {
        order: 2,
        title: "Deploy microgrid hardware",
        details: "Install controllers in tandem with new pumps.",
        key: "Key4",
      },
    ]);
    expect(playbook.timeline).toEqual(mockResponse.timeline);
    expect(playbook.angles).toEqual(mockResponse.angles);
  });

  it("returns the model output when no adjustments supplied", async () => {
    const mockResponse = {
      summary: "Coordinate rapid deployment of water and energy stack",
      actors: [{ name: "Aqua Aid Coalition", role: "Field Ops" }],
      angles: ["Scale proven combo"],
      steps: [
        {
          order: 1,
          title: "Map overlap of urgent villages",
          details: "Prioritize based on policy urgency weight.",
          key: "Key6",
        },
      ],
      timeline: [
        {
          phase: "Week 2",
          goals: ["Secure financing", "Schedule transport"],
        },
      ],
      risks: [
        { risk: "Limited hardware stock", mitigation: "Pre-stage reserve inventory." },
      ],
      collateral: ["partner brief"],
      wwh_alignment: [{ key: "Key6", why: "Water reliability" }],
    };

    const client = createMockClient(mockResponse);

    const playbook = await generatePlaybook(
      { opportunity, policy, contacts, adjustments: null },
      { client },
    );

    expect(playbook).toEqual(mockResponse);
  });
});
