import { appRouter } from "./router";
import { createContext } from "./context";

export async function createCaller() {
  const context = await createContext();
  return appRouter.createCaller(context);
}
