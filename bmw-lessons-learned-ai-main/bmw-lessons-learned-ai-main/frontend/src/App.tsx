import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import IncidentReport from "./pages/IncidentReport";
import SolutionSearch from "./pages/SolutionSearch";
import DepartmentSummary from "./pages/DepartmentSummary";
import DepartmentDetails from "./pages/DepartmentDetails";
import IncidentDetail from "./pages/IncidentDetail";
import AIProcessing from "./pages/AIProcessing";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<IncidentReport />} />
          <Route path="/solution-search" element={<SolutionSearch />} />
          <Route path="/summary" element={<DepartmentSummary />} />
          <Route
            path="/department/:department"
            element={<DepartmentDetails />}
          />
          <Route
            path="/department/:department/incident/:incidentId"
            element={<IncidentDetail />}
          />
          <Route path="/ai-processing/:lessonId" element={<AIProcessing />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
