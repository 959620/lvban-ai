import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AuthProvider } from "./context/AuthContext";
import { AppLayout } from "./layouts/AppLayout";
import { AiPage } from "./pages/AiPage";
import { CourseDetailPage } from "./pages/CourseDetailPage";
import { CourseEditPage } from "./pages/CourseEditPage";
import { CourseNewPage } from "./pages/CourseNewPage";
import { CoursesPage } from "./pages/CoursesPage";
import { DashboardPage } from "./pages/DashboardPage";
import { FollowUpsPage } from "./pages/FollowUpsPage";
import { LoginPage } from "./pages/LoginPage";
import { MatchPage } from "./pages/MatchPage";
import { RegisterPage } from "./pages/RegisterPage";
import { SchedulePage } from "./pages/SchedulePage";
import { StudentDetailPage } from "./pages/StudentDetailPage";
import { StudentEditPage } from "./pages/StudentEditPage";
import { StudentNewPage } from "./pages/StudentNewPage";
import { StudentsPage } from "./pages/StudentsPage";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route index element={<DashboardPage />} />
              <Route path="students" element={<StudentsPage />} />
              <Route path="students/new" element={<StudentNewPage />} />
              <Route path="students/:id" element={<StudentDetailPage />} />
              <Route path="students/:id/edit" element={<StudentEditPage />} />
              <Route path="schedule" element={<SchedulePage />} />
              <Route path="courses" element={<CoursesPage />} />
              <Route path="courses/new" element={<CourseNewPage />} />
              <Route path="courses/:id" element={<CourseDetailPage />} />
              <Route path="courses/:id/edit" element={<CourseEditPage />} />
              <Route path="match" element={<MatchPage />} />
              <Route path="follow-ups" element={<FollowUpsPage />} />
              <Route path="ai" element={<AiPage />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
