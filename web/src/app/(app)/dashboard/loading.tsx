export default function Loading() {
  return (
    <div className="space-y-6">
      <div className="h-8 w-48 rounded bg-neutral-800 animate-pulse" />
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="card h-24 animate-pulse" />
        ))}
      </div>
      <div className="card h-48 animate-pulse" />
    </div>
  );
}
