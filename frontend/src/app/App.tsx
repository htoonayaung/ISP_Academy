import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "../components/layout/AppLayout";
import { ProtectedRoute } from "../components/layout/ProtectedRoute";
import { RoleRoute } from "../components/layout/RoleRoute";
import { AiLabBuilderPage } from "../features/aiLabBuilder/AiLabBuilderPage";
import { AiLabBuilderPreviewDetailPage } from "../features/aiLabBuilder/AiLabBuilderPreviewDetailPage";
import { AiLabBuilderPreviewsPage } from "../features/aiLabBuilder/AiLabBuilderPreviewsPage";
import { AttemptDetailPage } from "../features/attempts/AttemptDetailPage";
import { MyAttemptsPage } from "../features/attempts/MyAttemptsPage";
import { LoginPage } from "../features/auth/LoginPage";
import { DashboardPage } from "../features/dashboard/DashboardPage";
import { NotFoundPage } from "../features/dashboard/NotFoundPage";
import { UnauthorizedPage } from "../features/dashboard/UnauthorizedPage";
import { LabTemplateDetailPage } from "../features/labTemplates/LabTemplateDetailPage";
import { LabTemplatesPage } from "../features/labTemplates/LabTemplatesPage";
import { LabDetailPage } from "../features/labs/LabDetailPage";
import { MyLabsPage } from "../features/labs/MyLabsPage";
import { TicketDetailPage } from "../features/tickets/TicketDetailPage";
import { TicketsPage } from "../features/tickets/TicketsPage";
import { UsersPage } from "../features/users/UsersPage";
import { VerificationRulesPage } from "../features/verification/VerificationRulesPage";
import { VerificationRulesIndexPage } from "../features/verification/VerificationRulesIndexPage";
import { VerificationRunPage } from "../features/verification/VerificationRunPage";

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/unauthorized" element={<UnauthorizedPage />} />
          <Route element={<RoleRoute roles={["ADMIN"]} />}>
            <Route path="/users" element={<UsersPage />} />
          </Route>
          <Route element={<RoleRoute roles={["ADMIN", "INSTRUCTOR"]} />}>
            <Route path="/ai-lab-builder" element={<AiLabBuilderPage />} />
            <Route path="/ai-lab-builder/previews" element={<AiLabBuilderPreviewsPage />} />
            <Route path="/ai-lab-builder/previews/:id" element={<AiLabBuilderPreviewDetailPage />} />
            <Route path="/lab-templates" element={<LabTemplatesPage />} />
            <Route path="/lab-templates/:id" element={<LabTemplateDetailPage />} />
            <Route path="/verification-rules" element={<VerificationRulesIndexPage />} />
            <Route path="/tickets/:id/verification-rules" element={<VerificationRulesPage />} />
          </Route>
          <Route path="/labs" element={<MyLabsPage />} />
          <Route path="/labs/:id" element={<LabDetailPage />} />
          <Route path="/tickets" element={<TicketsPage />} />
          <Route path="/tickets/:id" element={<TicketDetailPage />} />
          <Route element={<RoleRoute roles={["ADMIN", "STUDENT"]} />}>
            <Route path="/attempts" element={<MyAttemptsPage />} />
          </Route>
          <Route element={<RoleRoute roles={["STUDENT"]} />}>
            <Route path="/attempts/:id" element={<AttemptDetailPage />} />
            <Route path="/verification-runs/:id" element={<VerificationRunPage />} />
          </Route>
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Route>
    </Routes>
  );
}
