import { useState } from "react";
import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { TodayPage } from "./pages/Today";
import { CalendarPage } from "./pages/Calendar";
import { PlannerPage } from "./pages/Planner";
import { InsightsPage } from "./pages/Insights";
import { TasksPage } from "./pages/Tasks";
import { WorkspacePage } from "./pages/Workspace";

export default function App() {
  const [refreshKey, setRefreshKey] = useState(0);
  const bump = () => setRefreshKey((k) => k + 1);

  return (
    <Routes>
      <Route element={<Layout onRefreshKey={bump} refreshKey={refreshKey} />}>
        <Route index element={<TodayPage refreshKey={refreshKey} />} />
        <Route path="calendar" element={<CalendarPage refreshKey={refreshKey} />} />
        <Route
          path="workspace"
          element={<WorkspacePage refreshKey={refreshKey} onApplied={bump} />}
        />
        <Route path="tasks" element={<TasksPage refreshKey={refreshKey} />} />
        <Route
          path="planner"
          element={<PlannerPage refreshKey={refreshKey} onApplied={bump} />}
        />
        <Route path="insights" element={<InsightsPage refreshKey={refreshKey} />} />
      </Route>
    </Routes>
  );
}
