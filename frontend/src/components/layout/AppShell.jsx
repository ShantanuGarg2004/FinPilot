import { useCallback, useState } from "react";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";
import { PAGE_TITLES } from "./nav";

export default function AppShell({ activePage, onNavigate, hasUser, activeGoal, onNewProfile, fullBleed = false, children }) {
  const [open, setOpen] = useState(false);

  const navigate = useCallback(
    (page) => {
      onNavigate(page);
      setOpen(false);
    },
    [onNavigate]
  );

  return (
    <div className="min-h-screen bg-background text-on-surface">
      <Sidebar activePage={activePage} onNavigate={navigate} hasUser={hasUser} open={open} onClose={() => setOpen(false)} />
      <TopBar
        title={PAGE_TITLES[activePage]}
        activeGoal={activeGoal}
        onNewProfile={onNewProfile}
        onMenu={() => setOpen(true)}
      />

      {fullBleed ? (
        <main className="lg:ml-56 pt-14 h-screen overflow-hidden">{children}</main>
      ) : (
        <main className="lg:ml-56 pt-14 min-h-screen px-gutter py-xl md:px-lg">
          <div className="max-w-container-max mx-auto animate-fadeUp space-y-lg">{children}</div>
        </main>
      )}
    </div>
  );
}
