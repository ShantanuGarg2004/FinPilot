import { resetChatStore } from "./chatStore";
import { resetGoalStore } from "./goalStore";
import { resetReportStore } from "./reportStore";

/** Drop profile data kept in memory across page changes. */
export function clearPrivateCaches() {
  resetReportStore();
  resetChatStore();
  resetGoalStore();
}
