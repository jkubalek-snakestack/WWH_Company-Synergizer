"use client";

import { useMemo, useState, useTransition } from "react";
import { useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Table, TableBody, TableCell, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import type { CreateCompanyInput } from "@/server/actions/company";
import { compileProfileAction } from "@/server/actions/compileProfile";
import { createCompanyAction } from "@/server/actions/company";

const steps = ["Basics", "Capabilities", "Needs & Offers", "Narrative", "Review"] as const;

type Step = (typeof steps)[number];

type NeedDraft = {
  title: string;
  description: string;
  tags: string;
  urgency: "LOW" | "MED" | "HIGH";
  visibility: "PUBLIC" | "PARTNER" | "PRIVATE";
};

type OfferDraft = {
  title: string;
  description: string;
  tags: string;
  capacity: "LOW" | "MED" | "HIGH";
  visibility: "PUBLIC" | "PARTNER" | "PRIVATE";
};

type ContactDraft = {
  name: string;
  role: string;
  email: string;
  phone: string;
  privacyLevel: "PARTNER" | "PRIVATE";
};

type IntakeOptions = {
  capabilityTags: { id: string; name: string }[];
  wwhKeys: string[];
};

type IntakeWizardProps = {
  options: IntakeOptions;
};

function splitTags(value: string): string[] {
  return value
    .split(",")
    .map((entry) => entry.trim())
    .filter(Boolean);
}

export function IntakeWizard({ options }: IntakeWizardProps) {
  const router = useRouter();
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [companyName, setCompanyName] = useState("");
  const [region, setRegion] = useState("");
  const [mission, setMission] = useState("");
  const [wwhKeys, setWwhKeys] = useState<string[]>([]);
  const [capabilities, setCapabilities] = useState<string[]>([]);
  const [customCapability, setCustomCapability] = useState("");
  const [needs, setNeeds] = useState<NeedDraft[]>([
    {
      title: "",
      description: "",
      tags: "",
      urgency: "MED",
      visibility: "PARTNER",
    },
  ]);
  const [offers, setOffers] = useState<OfferDraft[]>([
    {
      title: "",
      description: "",
      tags: "",
      capacity: "MED",
      visibility: "PARTNER",
    },
  ]);
  const [contact, setContact] = useState<ContactDraft>({
    name: "",
    role: "",
    email: "",
    phone: "",
    privacyLevel: "PRIVATE",
  });
  const [narrative, setNarrative] = useState("");
  const [compiledProfile, setCompiledProfile] = useState<CreateCompanyInput | null>(
    null,
  );
  const [compileError, setCompileError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isCompiling, startCompileTransition] = useTransition();
  const [isSaving, startSaveTransition] = useTransition();

  const currentStep: Step = steps[currentStepIndex];

  function toggleWwhKey(key: string) {
    setWwhKeys((prev) =>
      prev.includes(key) ? prev.filter((value) => value !== key) : [...prev, key],
    );
  }

  function toggleCapability(capability: string) {
    const normalized = capability.toLowerCase();
    setCapabilities((prev) =>
      prev.includes(normalized)
        ? prev.filter((value) => value !== normalized)
        : [...prev, normalized],
    );
  }

  function addNeed() {
    setNeeds((items) => [
      ...items,
      { title: "", description: "", tags: "", urgency: "MED", visibility: "PARTNER" },
    ]);
  }

  function addOffer() {
    setOffers((items) => [
      ...items,
      { title: "", description: "", tags: "", capacity: "MED", visibility: "PARTNER" },
    ]);
  }

  function updateNeed(index: number, patch: Partial<NeedDraft>) {
    setNeeds((items) =>
      items.map((item, idx) => (idx === index ? { ...item, ...patch } : item)),
    );
  }

  function updateOffer(index: number, patch: Partial<OfferDraft>) {
    setOffers((items) =>
      items.map((item, idx) => (idx === index ? { ...item, ...patch } : item)),
    );
  }

  function buildManualProfile(): CreateCompanyInput {
    const normalizedCapabilities = Array.from(new Set(capabilities));

    return {
      company: {
        name: companyName,
        region: region || undefined,
        mission: mission || undefined,
        wwhKeys,
        capabilities: normalizedCapabilities,
      },
      needs: needs
        .filter((need) => need.title.trim())
        .map((need) => ({
          title: need.title,
          description: need.description || undefined,
          tags: splitTags(need.tags),
          urgency: need.urgency,
          visibility: need.visibility,
        })),
      offers: offers
        .filter((offer) => offer.title.trim())
        .map((offer) => ({
          title: offer.title,
          description: offer.description || undefined,
          tags: splitTags(offer.tags),
          capacity: offer.capacity,
          visibility: offer.visibility,
        })),
      contacts: contact.name
        ? [
            {
              name: contact.name,
              role: contact.role || undefined,
              email: contact.email || undefined,
              phone: contact.phone || undefined,
              privacyLevel: contact.privacyLevel,
            },
          ]
        : [],
    };
  }

  function mergeProfiles(manual: CreateCompanyInput, compiled: CreateCompanyInput) {
    const mergedCapabilities = Array.from(
      new Set([...compiled.company.capabilities, ...manual.company.capabilities]),
    );
    const mergedKeys = Array.from(
      new Set([...compiled.company.wwhKeys, ...manual.company.wwhKeys]),
    );

    return {
      company: {
        name: manual.company.name || compiled.company.name,
        region: manual.company.region ?? compiled.company.region,
        mission: manual.company.mission ?? compiled.company.mission,
        wwhKeys: mergedKeys,
        capabilities: mergedCapabilities,
      },
      needs: manual.needs.length ? manual.needs : compiled.needs,
      offers: manual.offers.length ? manual.offers : compiled.offers,
      contacts: manual.contacts.length ? manual.contacts : compiled.contacts,
      narrative: (compiled as { narrative?: string }).narrative,
    } satisfies CreateCompanyInput;
  }

  const manualProfile = useMemo(() => buildManualProfile(), [
    capabilities,
    companyName,
    contact,
    customCapability,
    mission,
    needs,
    offers,
    region,
    wwhKeys,
  ]);

  const reviewProfile: CreateCompanyInput = useMemo(() => {
    if (compiledProfile) {
      return mergeProfiles(manualProfile, compiledProfile);
    }
    return manualProfile;
  }, [compiledProfile, manualProfile]);

  function nextStep() {
    setCurrentStepIndex((index) => Math.min(index + 1, steps.length - 1));
  }

  function previousStep() {
    setCurrentStepIndex((index) => Math.max(index - 1, 0));
  }

  function handleAddCapability() {
    if (!customCapability.trim()) return;
    const value = customCapability.trim().toLowerCase();
    if (!capabilities.includes(value)) {
      setCapabilities((prev) => [...prev, value]);
    }
    setCustomCapability("");
  }

  function renderStep() {
    switch (currentStep) {
      case "Basics":
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="company-name">Company name</Label>
              <Input
                id="company-name"
                value={companyName}
                onChange={(event) => setCompanyName(event.target.value)}
                placeholder="Acme Impact Cooperative"
              />
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="region">Region</Label>
                <Input
                  id="region"
                  value={region}
                  onChange={(event) => setRegion(event.target.value)}
                  placeholder="West Africa"
                />
              </div>
              <div className="space-y-2">
                <Label>WWH Keys</Label>
                <div className="flex flex-wrap gap-2">
                  {options.wwhKeys.map((key) => {
                    const selected = wwhKeys.includes(key);
                    return (
                      <Button
                        key={key}
                        type="button"
                        variant={selected ? "secondary" : "outline"}
                        size="sm"
                        onClick={() => toggleWwhKey(key)}
                      >
                        {key}
                      </Button>
                    );
                  })}
                </div>
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="mission">Mission statement</Label>
              <Textarea
                id="mission"
                value={mission}
                onChange={(event) => setMission(event.target.value)}
                placeholder="Describe the focus, beneficiaries, and outcomes."
              />
            </div>
          </div>
        );
      case "Capabilities":
        return (
          <div className="space-y-4">
            <div>
              <h2 className="text-lg font-semibold">Core capabilities</h2>
              <p className="text-sm text-muted-foreground">
                Select existing tags or add new focus areas to enrich the profile.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {options.capabilityTags.map((tag) => {
                const normalized = tag.name.toLowerCase();
                const selected = capabilities.includes(normalized);
                return (
                  <Button
                    key={tag.id}
                    type="button"
                    variant={selected ? "secondary" : "outline"}
                    size="sm"
                    onClick={() => toggleCapability(tag.name)}
                  >
                    {tag.name}
                  </Button>
                );
              })}
              {!options.capabilityTags.length && (
                <p className="text-sm text-muted-foreground">
                  No capabilities have been tagged yet—add your own below.
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="custom-capability">Add custom capability</Label>
              <div className="flex gap-2">
                <Input
                  id="custom-capability"
                  value={customCapability}
                  onChange={(event) => setCustomCapability(event.target.value)}
                  placeholder="Sustainable logistics"
                />
                <Button type="button" onClick={handleAddCapability}>
                  Add
                </Button>
              </div>
              {capabilities.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {capabilities.map((capability) => (
                    <Badge key={capability} variant="outline">
                      {capability}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </div>
        );
      case "Needs & Offers":
        return (
          <div className="space-y-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">Needs</h2>
                <Button type="button" variant="outline" size="sm" onClick={addNeed}>
                  Add need
                </Button>
              </div>
              {needs.map((need, index) => (
                <Card key={`need-${index}`}>
                  <CardHeader>
                    <CardTitle className="text-base font-semibold">
                      Need #{index + 1}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="space-y-2">
                      <Label>Title</Label>
                      <Input
                        value={need.title}
                        onChange={(event) => updateNeed(index, { title: event.target.value })}
                        placeholder="Community Wi-Fi expansion"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Description</Label>
                      <Textarea
                        value={need.description}
                        onChange={(event) =>
                          updateNeed(index, { description: event.target.value })
                        }
                      />
                    </div>
                    <div className="grid gap-4 md:grid-cols-3">
                      <div className="space-y-2">
                        <Label>Urgency</Label>
                        <select
                          className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                          value={need.urgency}
                          onChange={(event) =>
                            updateNeed(index, {
                              urgency: event.target.value as NeedDraft["urgency"],
                            })
                          }
                        >
                          <option value="LOW">Low</option>
                          <option value="MED">Medium</option>
                          <option value="HIGH">High</option>
                        </select>
                      </div>
                      <div className="space-y-2">
                        <Label>Visibility</Label>
                        <select
                          className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                          value={need.visibility}
                          onChange={(event) =>
                            updateNeed(index, {
                              visibility: event.target.value as NeedDraft["visibility"],
                            })
                          }
                        >
                          <option value="PUBLIC">Public</option>
                          <option value="PARTNER">Partner</option>
                          <option value="PRIVATE">Private</option>
                        </select>
                      </div>
                      <div className="space-y-2">
                        <Label>Tags</Label>
                        <Input
                          value={need.tags}
                          onChange={(event) => updateNeed(index, { tags: event.target.value })}
                          placeholder="water, training"
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">Offers</h2>
                <Button type="button" variant="outline" size="sm" onClick={addOffer}>
                  Add offer
                </Button>
              </div>
              {offers.map((offer, index) => (
                <Card key={`offer-${index}`}>
                  <CardHeader>
                    <CardTitle className="text-base font-semibold">
                      Offer #{index + 1}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="space-y-2">
                      <Label>Title</Label>
                      <Input
                        value={offer.title}
                        onChange={(event) =>
                          updateOffer(index, { title: event.target.value })
                        }
                        placeholder="STEM bootcamp"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Description</Label>
                      <Textarea
                        value={offer.description}
                        onChange={(event) =>
                          updateOffer(index, { description: event.target.value })
                        }
                      />
                    </div>
                    <div className="grid gap-4 md:grid-cols-3">
                      <div className="space-y-2">
                        <Label>Capacity</Label>
                        <select
                          className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                          value={offer.capacity}
                          onChange={(event) =>
                            updateOffer(index, {
                              capacity: event.target.value as OfferDraft["capacity"],
                            })
                          }
                        >
                          <option value="LOW">Low</option>
                          <option value="MED">Medium</option>
                          <option value="HIGH">High</option>
                        </select>
                      </div>
                      <div className="space-y-2">
                        <Label>Visibility</Label>
                        <select
                          className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                          value={offer.visibility}
                          onChange={(event) =>
                            updateOffer(index, {
                              visibility: event.target.value as OfferDraft["visibility"],
                            })
                          }
                        >
                          <option value="PUBLIC">Public</option>
                          <option value="PARTNER">Partner</option>
                          <option value="PRIVATE">Private</option>
                        </select>
                      </div>
                      <div className="space-y-2">
                        <Label>Tags</Label>
                        <Input
                          value={offer.tags}
                          onChange={(event) => updateOffer(index, { tags: event.target.value })}
                          placeholder="solar, analytics"
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="text-base font-semibold">Primary contact</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label>Name</Label>
                  <Input
                    value={contact.name}
                    onChange={(event) => setContact((current) => ({ ...current, name: event.target.value }))}
                    placeholder="Jordan Okoye"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Role</Label>
                  <Input
                    value={contact.role}
                    onChange={(event) => setContact((current) => ({ ...current, role: event.target.value }))}
                    placeholder="Director of Partnerships"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Email</Label>
                  <Input
                    type="email"
                    value={contact.email}
                    onChange={(event) => setContact((current) => ({ ...current, email: event.target.value }))}
                    placeholder="partnerships@example.org"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Phone</Label>
                  <Input
                    value={contact.phone}
                    onChange={(event) => setContact((current) => ({ ...current, phone: event.target.value }))}
                    placeholder="+1 555-123-4567"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Privacy level</Label>
                  <select
                    className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                    value={contact.privacyLevel}
                    onChange={(event) =>
                      setContact((current) => ({
                        ...current,
                        privacyLevel: event.target.value as ContactDraft["privacyLevel"],
                      }))
                    }
                  >
                    <option value="PRIVATE">Private</option>
                    <option value="PARTNER">Partner</option>
                  </select>
                </div>
              </CardContent>
            </Card>
          </div>
        );
      case "Narrative":
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="narrative">Narrative</Label>
              <Textarea
                id="narrative"
                value={narrative}
                onChange={(event) => setNarrative(event.target.value)}
                placeholder="Share the company story, goals, partnerships, and current focus."
              />
            </div>
            {compileError && (
              <p className="text-sm text-destructive">{compileError}</p>
            )}
            <Button
              type="button"
              onClick={() => {
                setCompileError(null);
                startCompileTransition(async () => {
                  try {
                    const result = await compileProfileAction({ narrative });
                    setCompiledProfile(result);
                    setCurrentStepIndex(steps.indexOf("Review"));
                  } catch (error) {
                    setCompileError(
                      error instanceof Error
                        ? error.message
                        : "Unable to compile the narrative. Check API credentials.",
                    );
                  }
                });
              }}
              disabled={isCompiling || narrative.trim().length < 10}
            >
              {isCompiling ? "Compiling…" : "Compile narrative"}
            </Button>
          </div>
        );
      case "Review":
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-semibold">Review profile</h2>
              <p className="text-sm text-muted-foreground">
                Confirm the generated structure before saving. Adjust earlier steps if
                needed.
              </p>
            </div>
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-semibold">Company</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p>
                  <span className="font-medium">Name:</span> {reviewProfile.company.name}
                </p>
                <p>
                  <span className="font-medium">Region:</span> {reviewProfile.company.region ?? "Unspecified"}
                </p>
                <p>
                  <span className="font-medium">Mission:</span> {reviewProfile.company.mission ?? "—"}
                </p>
                <p>
                  <span className="font-medium">WWH Keys:</span> {reviewProfile.company.wwhKeys.join(", ") || "—"}
                </p>
                <p>
                  <span className="font-medium">Capabilities:</span> {reviewProfile.company.capabilities.join(", ") || "—"}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-semibold">Needs</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableBody>
                    {reviewProfile.needs.map((need, index) => (
                      <TableRow key={`review-need-${index}`} className="text-sm">
                        <TableCell className="font-medium">{need.title}</TableCell>
                        <TableCell>{need.urgency}</TableCell>
                        <TableCell>{need.tags.join(", ") || "—"}</TableCell>
                      </TableRow>
                    ))}
                    {reviewProfile.needs.length === 0 && (
                      <TableRow>
                        <TableCell className="text-sm text-muted-foreground">
                          No needs captured.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-semibold">Offers</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableBody>
                    {reviewProfile.offers.map((offer, index) => (
                      <TableRow key={`review-offer-${index}`} className="text-sm">
                        <TableCell className="font-medium">{offer.title}</TableCell>
                        <TableCell>{offer.capacity}</TableCell>
                        <TableCell>{offer.tags.join(", ") || "—"}</TableCell>
                      </TableRow>
                    ))}
                    {reviewProfile.offers.length === 0 && (
                      <TableRow>
                        <TableCell className="text-sm text-muted-foreground">
                          No offers captured.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-semibold">Contacts</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableBody>
                    {reviewProfile.contacts.map((item, index) => (
                      <TableRow key={`review-contact-${index}`} className="text-sm">
                        <TableCell className="font-medium">{item.name}</TableCell>
                        <TableCell>{item.role ?? "—"}</TableCell>
                        <TableCell>{item.privacyLevel}</TableCell>
                      </TableRow>
                    ))}
                    {reviewProfile.contacts.length === 0 && (
                      <TableRow>
                        <TableCell className="text-sm text-muted-foreground">
                          No contacts provided.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
            {saveError && <p className="text-sm text-destructive">{saveError}</p>}
            <div className="flex items-center justify-end gap-2">
              <Button type="button" variant="outline" onClick={previousStep}>
                Back
              </Button>
              <Button
                type="button"
                disabled={isSaving || !reviewProfile.company.name}
                onClick={() => {
                  setSaveError(null);
                  startSaveTransition(async () => {
                    try {
                      const result = await createCompanyAction(reviewProfile);
                      router.push(`/companies/${result.id}`);
                      router.refresh();
                    } catch (error) {
                      setSaveError(
                        error instanceof Error
                          ? error.message
                          : "Unable to save the company. Check logs for details.",
                      );
                    }
                  });
                }}
              >
                {isSaving ? "Saving…" : "Save company"}
              </Button>
            </div>
          </div>
        );
    }
  }

  return (
    <div className="rounded-lg border border-border bg-card">
      <div className="flex flex-wrap gap-2 border-b border-border px-6 py-4">
        {steps.map((step, index) => {
          const isActive = index === currentStepIndex;
          return (
            <span
              key={step}
              className={`text-sm font-medium ${
                isActive ? "text-primary" : "text-muted-foreground"
              }`}
            >
              {index + 1}. {step}
            </span>
          );
        })}
      </div>
      <div className="space-y-6 px-6 py-6">
        {renderStep()}
        <Separator />
        <div className="flex justify-between">
          <Button
            type="button"
            variant="ghost"
            onClick={previousStep}
            disabled={currentStepIndex === 0}
          >
            Previous
          </Button>
          {currentStep !== "Review" && (
            <Button type="button" onClick={nextStep}>
              Next
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
