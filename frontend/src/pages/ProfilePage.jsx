import ProfileForm from "../sections/profile/ProfileForm";
import SavedProfiles from "../sections/profile/SavedProfiles";

/* Form + profiles rail with intentional breathing room. */
export default function ProfilePage({ onCreated, activeUserId, onSelectUser, profiles }) {
  return (
    <div className="h-[calc(100vh-56px)] flex flex-col lg:flex-row">
      <section className="flex-1 min-w-0 overflow-y-auto">
        <div className="h-full max-w-[760px] mx-auto px-gutter py-lg lg:py-xl">
          <ProfileForm onCreated={onCreated} />
        </div>
      </section>

      <aside className="lg:w-80 shrink-0 border-t lg:border-t-0 lg:border-l border-outline bg-surface">
        <div className="h-full max-h-[42vh] lg:max-h-none lg:h-full p-gutter overflow-hidden flex flex-col">
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
