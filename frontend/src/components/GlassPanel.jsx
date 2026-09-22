export default function GlassPanel({ as = "div", className = "", children, ...rest }) {
  const Tag = as;
  return (
    <Tag className={`glass-panel rounded-xl shadow-panel ${className}`} {...rest}>
      {children}
    </Tag>
  );
}
