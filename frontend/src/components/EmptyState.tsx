export default function EmptyState({ icon, title, description, actionText, onAction }) {
  return (
    <div className="flex flex-col items-center justify-center h-[60vh] text-center max-w-md mx-auto">
      <div className="w-20 h-20 bg-[var(--surface-alt)] rounded-full flex items-center justify-center mb-6 border border-[var(--border-subtle)] shadow-xl">
        {icon}
      </div>
      <h2 className="text-2xl font-display mb-2 text-[var(--text-primary)]">{title}</h2>
      <p className="text-[var(--text-secondary)] mb-8 leading-relaxed">
        {description}
      </p>
      {actionText && onAction && (
        <button 
          onClick={onAction}
          className="bg-[var(--chai)] text-[var(--ink)] px-6 py-3 rounded font-medium hover:bg-opacity-90 transition-colors shadow-lg"
        >
          {actionText}
        </button>
      )}
    </div>
  );
}
