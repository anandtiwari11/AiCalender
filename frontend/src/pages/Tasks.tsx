import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export function TasksPage({ refreshKey }: { refreshKey: number }) {
  const [tasks, setTasks] = useState<any[]>([]);
  const [title, setTitle] = useState("");
  const [due, setDue] = useState("");
  const [minutes, setMinutes] = useState(60);
  const [priority, setPriority] = useState("high");

  const load = async () => {
    const res = await api.listTasks();
    setTasks(res.tasks);
  };

  useEffect(() => {
    load().catch(console.error);
  }, [refreshKey]);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">Tasks</h1>
        <p className="text-gray-500">
          Deadlines here feed the Chief of Staff and focus recommendations.
        </p>
      </div>

      <form
        className="rounded-xl border bg-white p-4 grid md:grid-cols-4 gap-3 shadow-sm"
        onSubmit={async (e) => {
          e.preventDefault();
          await api.createTask({
            title,
            due_date: due ? new Date(due).toISOString() : null,
            estimated_minutes: minutes,
            priority,
          });
          setTitle("");
          await load();
        }}
      >
        <label className="text-sm font-medium md:col-span-2">
          Title
          <input
            required
            className="mt-1 w-full rounded-lg border px-3 py-2"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </label>
        <label className="text-sm font-medium">
          Due
          <input
            type="datetime-local"
            className="mt-1 w-full rounded-lg border px-3 py-2"
            value={due}
            onChange={(e) => setDue(e.target.value)}
          />
        </label>
        <label className="text-sm font-medium">
          Estimate (min)
          <input
            type="number"
            className="mt-1 w-full rounded-lg border px-3 py-2"
            value={minutes}
            onChange={(e) => setMinutes(Number(e.target.value))}
          />
        </label>
        <label className="text-sm font-medium">
          Priority
          <select
            className="mt-1 w-full rounded-lg border px-3 py-2"
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </label>
        <button type="submit" className="rounded-lg bg-slate-900 text-white px-4 py-2 text-sm w-fit">
          Add task
        </button>
      </form>

      <ul className="space-y-2">
        {tasks.map((t) => (
          <li key={t.id} className="rounded-xl border bg-white p-3 flex items-start gap-3 shadow-sm">
            <button
              className="text-lg"
              onClick={async () => {
                await api.toggleTask(t.id);
                await load();
              }}
            >
              {t.status === "done" ? "●" : "○"}
            </button>
            <div className="flex-1">
              <div className={`font-medium ${t.status === "done" ? "line-through opacity-60" : ""}`}>
                {t.title}
              </div>
              <div className="text-xs text-gray-500">
                {t.priority} · {t.estimated_minutes}m
                {t.due_date ? ` · due ${t.due_date.slice(0, 10)}` : ""}
              </div>
            </div>
            <button
              className="text-xs text-gray-500"
              onClick={async () => {
                await api.deleteTask(t.id);
                await load();
              }}
            >
              Delete
            </button>
          </li>
        ))}
        {tasks.length === 0 && <li className="text-sm text-gray-500">No tasks yet.</li>}
      </ul>
    </div>
  );
}
