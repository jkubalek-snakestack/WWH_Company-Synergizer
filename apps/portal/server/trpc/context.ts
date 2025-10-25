import { initTRPC } from "@trpc/server";
import superjson from "superjson";
import { requireUser } from "../auth";
import { prisma } from "../db/client";

export async function createContext() {
  const user = await requireUser();
  return { prisma, user };
}

export type Context = Awaited<ReturnType<typeof createContext>>;

const t = initTRPC.context<Context>().create({
  transformer: superjson,
});

export const createTRPCRouter = t.router;
export const protectedProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.user) {
    throw new Error("Unauthorized");
  }

  return next({ ctx });
});
