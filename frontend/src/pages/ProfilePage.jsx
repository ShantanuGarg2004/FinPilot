import ProfileForm from "../sections/profile/ProfileForm";
import SavedProfiles from "../sections/profile/SavedProfiles";

/* Form + profiles rail with intentional breathing room. */
export default function ProfilePage({ onCreated, activeUserId, onSelectUser, profiles }) {
  return (
    <div className="flex flex-col lg:flex-row lg:h-[calc(100dvh-var(--app-bar))]">
      <section className="min-w-0 lg:flex-1 lg:overflow-y-auto">
        <div className="max-w-[760px] mx-auto px-4 sm:px-gutter py-5 lg:py-xl">
          {!profiles.loading && profiles.users.length === 0 && (
            <p className="text-[13px] text-on-surface-variant mb-4">You are signed in and have no profiles yet.</p>
          )}
          <ProfileForm onCreated={onCreated} />
        </div>
      </section>

      <aside className="lg:w-80 shrink-0 border-t lg:border-t-0 lg:border-l border-outline bg-surface">
        <div className="max-h-[46vh] lg:max-h-none lg:h-full p-4 sm:p-gutter overflow-hidden flex flex-col">
          <SavedProfiles
            users={profiles.users}
            loading={profiles.loading}
            activeId={activeUserId}
            onSelect={onSelectUser}
            onRemove={profiles.remove}
          />
        </div>
      </aside>
    </div>
  );
}
