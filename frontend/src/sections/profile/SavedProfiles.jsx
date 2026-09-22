import { useToast } from "../../components/toast-context";
import { profileTitle, formatINR } from "../../lib/format";
import { formatApiErrorMessage, toastTypeForError } from "../../lib/apiErrors";
import Icon from "../../components/Icon";

export default function SavedProfiles({ users, loading, activeId, onSelect, onRemove, refreshKey }) {
  const showToast = useToast();

  const del = async (id, e) => {
    e.stopPropagation();
    try {
      await onRemove(id);
      showToast("Profile deleted", "success");
    } catch (err) {
      const type = toastTypeForError(err) || "error";
      showToast(formatApiErrorMessage(err, "Failed to delete"), type);
    }
  };

  return (
    <div key={refreshKey} className="flex flex-col h-full min-h-0">
      <div className="flex items-center justify-between mb-md shrink-0">
        <h3 className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-medium">
          Saved profiles
        </h3>
        <span className="text-[11px] text-on-surface-variant/70 tabular-nums">
          {loading ? "…" : users.length}
        </span>
      </div>

      {loading ? (
        <p className="text-[13px] text-on-surface-variant/60">Loading…</p>
      ) : !users.length ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center px-3 py-8 border border-dashed border-outline rounded-xl">
          <Icon name="folder_open" size={28} className="text-on-surface-variant/40 mb-2" />
          <p className="text-[13px] text-on-surface-variant">No profiles yet</p>
          <p className="text-[12px] text-on-surface-variant/60 mt-1">Create one with the form</p>
        </div>
      ) : (
        <div className="flex-1 min-h-0 overflow-y-auto space-y-2 pr-0.5">
          {users.map((u) => {
            const active = activeId === u.id;
            return (
              <div
                key={u.id}
                onClick={() => onSelect(u.id, users)}
                className={[
                  "flex items-start justify-between gap-2 px-3 py-2.5 rounded-lg cursor-pointer transition-all border",
                  active
                    ? "bg-primary/10 border-primary/35"
                    : "bg-surface-container border-outline hover:border-primary/30",
                ].join(" ")}
              >
                <div className="flex-1 min-w-0">
                  <p className={`text-[13px] font-semibold truncate leading-snug ${active ? "text-primary" : "text-on-surface"}`}>
                    {profileTitle(u)}
                  </p>
                  <p className="text-[11px] text-on-surface-variant mt-1 truncate">
                    {u.age}y · {u.risk_appetite} · ₹{formatINR(u.income)}/mo
                  </p>
                </div>
                <button
                  onClick={(e) => del(u.id, e)}
                  className="shrink-0 p-1 rounded text-on-surface-variant/50 hover:text-error transition-colors"
                  title="Delete profile"
                >
                  <Icon name="delete" size={15} />
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
