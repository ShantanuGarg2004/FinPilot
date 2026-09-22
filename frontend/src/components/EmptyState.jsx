import Icon from "./Icon";
import Button from "./Button";

export default function EmptyState({ icon = "insights", title, description, action }) {
  return (
    <div className="text-center py-xl px-md border border-dashed border-outline rounded-lg">
      <div className="flex justify-center mb-sm text-on-surface-variant">
        <Icon name={icon} size={36} />
      </div>
      {title && <h3 className="font-headline-md text-headline-md text-on-surface mb-1">{title}</h3>}
      {description && (
        <p className="text-[12px] text-on-surface-variant max-w-sm mx-auto mb-sm">{description}</p>
      )}
      {action && (
        <Button variant="primary" size="sm" icon={action.icon} onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  );
}
