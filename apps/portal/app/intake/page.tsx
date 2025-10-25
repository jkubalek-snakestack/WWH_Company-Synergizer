import { createCaller } from "@/server/trpc/caller";
import { IntakeWizard } from "./wizard";

export default async function IntakePage() {
  const caller = await createCaller();
  const options = await caller.companies.intakeOptions();

  return (
    <main className="mx-auto w-full max-w-4xl px-6 py-8">
      <h1 className="text-3xl font-semibold">Company Intake</h1>
      <p className="mt-1 text-muted-foreground">
        Gather baseline information, translate narratives, and save the profile to
        trigger synergy recomputation.
      </p>
      <div className="mt-8">
        <IntakeWizard options={options} />
      </div>
    </main>
  );
}
