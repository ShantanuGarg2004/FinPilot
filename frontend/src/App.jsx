import { useCallback, useMemo, useState } from "react";
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

function FinPilotApp() {
  const showToast = useToast();
  const profiles = useProfiles(showToast);
  const { users, remove } = profiles;

  const [activePage, setActivePage] = useState("profile");
  const [activeUserId, setActiveUserId] = useState(null);

  const activeUser = useMemo(
    () => users.find((u) => u.id === activeUserId) || null,
    [users, activeUserId]
  );
  const activeGoal = activeUser ? profileTitle(activeUser) : "";

  const navigate = useCallback((page) => setActivePage(page), []);

  const selectUser = useCallback((id, list) => {
    setActiveUserId(id);
    if (id) {
      const found = (list || users).find((u) => u.id === id);
      // Jump straight to the dashboard when a profile becomes active.
      setActivePage((p) => (p === "profile" ? "dashboard" : p));
      return found;
    }
  }, [users]);

  const handleCreated = useCallback(
    async (userId) => {
      await profiles.reload();
      setActiveUserId(userId);
      setActivePage("dashboard");
    },
    [profiles]
  );

  const handleRemove = useCallback(
    async (id) => {
      await remove(id);
      if (id === activeUserId) {
        setActiveUserId(null);
        setActivePage("profile");
      }
    },
    [remove, activeUserId]
  );

  const newProfile = useCallback(() => setActivePage("profile"), []);

  const profilesForPage = { ...profiles, remove: handleRemove };
  const hasUser = !!activeUserId;
  // Guard: never render a user-scoped page without an active profile.
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
          activeUserId={activeUserId}
          onSelectUser={selectUser}
          profiles={profilesForPage}
        />
      )}
      {page === "dashboard" && hasUser && (
        <DashboardPage userId={activeUserId} user={activeUser} userGoal={activeGoal} onNavigate={navigate} />
      )}
      {page === "advisory" && hasUser && (
        <AdvisoryPage key={activeUserId} userId={activeUserId} userGoal={activeGoal} />
      )}
      {page === "chat" && hasUser && (
        <ChatPage key={activeUserId} userId={activeUserId} userGoal={activeGoal} />
      )}
      {page === "goals" && hasUser && (
        <GoalsPage key={activeUserId} userId={activeUserId} userGoal={activeGoal} />
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
