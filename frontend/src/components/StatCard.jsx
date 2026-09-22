import Icon from "./Icon";
import GlassPanel from "./GlassPanel";

export default function StatCard({ icon, label, value, sub, subIcon, subColor = "text-on-surface-variant", accent = false }) {
  return (
    <GlassPanel className="p-lg flex flex-col gap-2.5">
      {icon && <Icon name={icon} size={20} className="text-primary" />}
      <div>
        <p className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">{label}</p>
        <h4 className={`font-headline-md text-headline-md mt-1.5 ${accent ? "text-primary" : "text-on-surface"}`}>
          {value}
        </h4>
      </div>
      {sub && (
        <div className={`flex items-center text-[12px] ${subColor}`}>
          {subIcon && <Icon name={subIcon} size={14} className="mr-1" />}
          {sub}
        </div>
      )}
    </GlassPanel>
  );
}
