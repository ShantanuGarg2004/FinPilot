import { useCallback, useEffect, useMemo, useState } from "react";
import { ToastProvider } from "./components/Toast";
import { useToast } from "./components/toast-context";
import AppShell from "./components/layout/AppShell";
import useProfiles from "./hooks/useProfiles";
import { profileTitle } from "./lib/format";
import ProfilePage from "./pages/ProfilePage";
import DashboardPage from "./pages/DashboardPage";
import AdvisoryPage from "./pages/AdvisoryPage";
import ChatPage from "./pages/ChatPage";
import GoalsPage from "./pages/GoalsPage";

const FULL_BLEED = new Set(["profile", "chat"]);
const ACTIVE_USER_KEY = "finpilot.activeUserId";

function readStoredUserId() {
  try {
    const raw = sessionStorage.getItem(ACTIVE_USER_KEY);
    if (!raw) return null;
    const id = Number(raw);
    return Number.isFinite(id) ? id : null;
  } catch {
    return null;
  }
}

function writeStoredUserId(id) {
  try {
    if (id != null) sessionStorage.setItem(ACTIVE_USER_KEY, String(id));
    else sessionStorage.removeItem(ACTIVE_USER_KEY);
  } catch {
    /* private mode / blocked storage */
  }
}

function FinPilotApp() {
  const showToast = useToast();
  const profiles = useProfiles(showToast);
  const { users, remove } = profiles;

  const [activeUserId, setActiveUserId] = useState(readStoredUserId);
  const [activePage, setActivePage] = useState(() => (readStoredUserId() != null ? "dashboard" : "profile"));

  // Persist selection; ignore stale ids once the profile list has loaded.
  const activeUser = useMemo(
    () => users.find((u) => u.id === activeUserId) || null,
    [users, activeUserId]
  );
  const staleSelection = !profiles.loading && activeUserId != null && !activeUser;
  const effectiveUserId = staleSelection ? null : activeUserId;
  const effectiveUser = staleSelection ? null : activeUser;

  useEffect(() => {
    writeStoredUserId(effectiveUserId);
  }, [effectiveUserId]);

  const activeGoal = effectiveUser ? profileTitle(effectiveUser) : "";

  const navigate = useCallback((page) => setActivePage(page), []);

  const selectUser = useCallback((id, list) => {
    setActiveUserId(id);
    writeStoredUserId(id);
    if (id) {
      const found = (list || users).find((u) => u.id === id);
      setActivePage((p) => (p === "profile" ? "dashboard" : p));
      return found;
    }
  }, [users]);

  const handleCreated = useCallback(
    async (userId) => {
      await profiles.reload();
      setActiveUserId(userId);
      writeStoredUserId(userId);
      setActivePage("dashboard");
    },
    [profiles]
  );

  const handleRemove = useCallback(
    async (id) => {
      await remove(id);
      if (id === activeUserId) {
        setActiveUserId(null);
        writeStoredUserId(null);
        setActivePage("profile");
      }
    },
    [remove, activeUserId]
  );

  const newProfile = useCallback(() => setActivePage("profile"), []);

  const profilesForPage = { ...profiles, remove: handleRemove };
  const hasUser = !!effectiveUserId;
  const page = !hasUser && activePage !== "profile" ? "profile" : activePage;

  return (
    <AppShell
      activePage={page}
      onNavigate={navigate}
      hasUser={hasUser}
      activeGoal={activeGoal}
      onNewProfile={newProfile}
      fullBleed={FULL_BLEED.has(page)}
    >
      {page === "profile" && (
        <ProfilePage
          onCreated={handleCreated}
          activeUserId={effectiveUserId}
          onSelectUser={selectUser}
          profiles={profilesForPage}
        />
      )}
      {page === "dashboard" && hasUser && (
        <DashboardPage userId={effectiveUserId} user={effectiveUser} userGoal={activeGoal} onNavigate={navigate} />
      )}
      {page === "advisory" && hasUser && (
        <AdvisoryPage key={effectiveUserId} userId={effectiveUserId} userGoal={activeGoal} />
      )}
      {page === "chat" && hasUser && (
        <ChatPage key={effectiveUserId} userId={effectiveUserId} userGoal={activeGoal} />
      )}
      {page === "goals" && hasUser && (
        <GoalsPage key={effectiveUserId} userId={effectiveUserId} userGoal={activeGoal} />
      )}
    </AppShell>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <FinPilotApp />
    </ToastProvider>
  );
}
