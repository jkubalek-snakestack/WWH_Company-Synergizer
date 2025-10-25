import { cookies } from "next/headers";
import { prisma } from "./db/client";

export async function requireUser() {
  const cookieStore = cookies();
  const cookie = cookieStore.get("userId");

  if (cookie?.value) {
    const user = await prisma.user.findUnique({ where: { id: cookie.value } });
    if (user) {
      return user;
    }
  }

  const fallback = await prisma.user.findFirst({
    orderBy: { createdAt: "asc" },
  });

  if (!fallback) {
    throw new Error("No users are available. Seed the database first.");
  }

  return fallback;
}
