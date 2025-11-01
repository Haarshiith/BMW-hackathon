import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  ArrowLeft,
  BarChart3,
  AlertCircle,
  Loader2,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import Navigation from "@/components/Navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { departmentService, lessonService } from "@/services";
import type { LessonLearned } from "@/types/api";

// Define the actual backend response structure
interface DepartmentInsightsResponse {
  department: string;
  total_lessons: number;
  recent_lessons_this_month: number;
  critical_lessons: number;
  high_severity_lessons: number;
  lessons_last_6_months: number;
  ai_summary: {
    department: string;
    total_lessons: number;
    consolidated_summary: string;
    key_patterns: string[];
    top_recommendations: string[];
    department_insights: string;
    severity_breakdown: Record<string, number>;
    unique_commodities: number;
    unique_suppliers: number;
    top_commodities: string[];
    top_suppliers: string[];
    generated_at: string;
    ai_generated: boolean;
  };
  insights: {
    severity_distribution: {
      critical: number;
      high: number;
      medium: number;
      low: number;
    };
    trend_analysis: {
      recent_activity: number;
      six_month_trend: number;
      activity_level: string;
    };
  };
  ai_analysis_available: boolean;
  generated_at: string;
}
import { toast } from "sonner";

// Function to format department names for display
const formatDepartmentName = (name: string): string => {
  // Handle special cases
  const specialCases: Record<string, string> = {
    it: "IT",
    hr: "HR",
    qa: "QA",
    "r&d": "R&D",
    crm: "CRM",
    erp: "ERP",
  };

  const lowerName = name.toLowerCase();
  if (specialCases[lowerName]) {
    return specialCases[lowerName];
  }

  // Capitalize first letter of each word
  return name
    .split(" ")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(" ");
};

const DepartmentDetails = () => {
  const { department } = useParams<{ department: string }>();
  const navigate = useNavigate();

  const [insights, setInsights] = useState<DepartmentInsightsResponse | null>(
    null
  );
  const [lessons, setLessons] = useState<LessonLearned[]>([]);
  const [loading, setLoading] = useState(true);
  const [aiRegenerating, setAiRegenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDepartmentData = async () => {
      if (!department) {
        setError("No department specified");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const [insightsData, lessonsData] = await Promise.all([
          departmentService.getDepartmentInsights(department),
          lessonService.getLessons({ department: department, limit: 50 }),
        ]);
        setInsights(insightsData);
        setLessons(lessonsData.items);
        setError(null);
      } catch (err) {
        console.error("Error fetching department data:", err);
        const errorMessage =
          err instanceof Error
            ? err.message
            : "Failed to load department details";
        setError(errorMessage);
        toast.error("Failed to load department", {
          description: errorMessage,
        });
      } finally {
        setLoading(false);
      }
    };

    fetchDepartmentData();
  }, [department]);

  const handleRegenerateAI = async () => {
    if (!department) return;

    try {
      setAiRegenerating(true);
      toast.info("Regenerating AI summary...", {
        description: "This may take a few moments",
      });

      const result = await departmentService.regenerateDepartmentSummary(
        department
      );

      // Update insights with new summary
      if (result && result.summary) {
        setInsights((prev) =>
          prev
            ? {
                ...prev,
                ai_summary: result.summary,
              }
            : null
        );
      }

      toast.success("AI summary regenerated", {
        description: "Department insights have been updated",
      });

      // Refresh the page data
      const insightsData = await departmentService.getDepartmentInsights(
        department
      );
      setInsights(insightsData);
    } catch (err) {
      console.error("Error regenerating AI summary:", err);
      toast.error("Failed to regenerate AI summary", {
        description:
          err instanceof Error ? err.message : "Please try again later",
      });
    } finally {
      setAiRegenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <div className="container mx-auto px-4 py-8 flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
            <p className="text-muted-foreground">
              Loading department details...
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !insights) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <div className="container mx-auto px-4 py-8">
          <Button
            variant="ghost"
            onClick={() => navigate("/summary")}
            className="mb-6"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Summary
          </Button>
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {error || "Department not found"}
            </AlertDescription>
          </Alert>
        </div>
      </div>
    );
  }

  const severityColors = {
    critical:
      "bg-status-critical/10 border-status-critical text-status-critical",
    high: "bg-status-high/10 border-status-high text-status-high",
    medium: "bg-status-medium/10 border-status-medium text-status-medium",
    low: "bg-status-low/10 border-status-low text-status-low",
  };

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <div className="container mx-auto px-4 py-8">
        <Button
          variant="ghost"
          onClick={() => navigate("/summary")}
          className="mb-6"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Summary
        </Button>

        <div className="mb-8 animate-fade-in">
          <h1 className="text-4xl font-bold text-foreground mb-2">
            {formatDepartmentName(insights.department)} Department
          </h1>
          <p className="text-muted-foreground">
            Detailed incident analytics and AI-powered insights
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <Card className="animate-scale-in">
            <CardHeader>
              <CardTitle>Total Incidents</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-baseline gap-2 mb-6">
                <span className="text-6xl font-bold text-foreground">
                  {insights.total_lessons}
                </span>
                <span className="text-lg text-muted-foreground">
                  {insights.total_lessons === 1 ? "incident" : "incidents"}{" "}
                  reported
                </span>
              </div>

              <div className="space-y-3">
                {insights.insights?.severity_distribution?.critical > 0 && (
                  <div className="flex items-center justify-between p-3 rounded-lg bg-status-critical/10 border border-status-critical/20">
                    <Badge
                      variant="outline"
                      className="bg-status-critical/10 border-status-critical text-status-critical"
                    >
                      Critical
                    </Badge>
                    <span className="text-xl font-bold text-foreground">
                      {insights.insights.severity_distribution.critical}
                    </span>
                  </div>
                )}

                {insights.insights?.severity_distribution?.high > 0 && (
                  <div className="flex items-center justify-between p-3 rounded-lg bg-status-high/10 border border-status-high/20">
                    <Badge
                      variant="outline"
                      className="bg-status-high/10 border-status-high text-status-high"
                    >
                      High
                    </Badge>
                    <span className="text-xl font-bold text-foreground">
                      {insights.insights.severity_distribution.high}
                    </span>
                  </div>
                )}

                {insights.insights?.severity_distribution?.medium > 0 && (
                  <div className="flex items-center justify-between p-3 rounded-lg bg-status-medium/10 border border-status-medium/20">
                    <Badge
                      variant="outline"
                      className="bg-status-medium/10 border-status-medium text-status-medium"
                    >
                      Medium
                    </Badge>
                    <span className="text-xl font-bold text-foreground">
                      {insights.insights.severity_distribution.medium}
                    </span>
                  </div>
                )}

                {insights.insights?.severity_distribution?.low > 0 && (
                  <div className="flex items-center justify-between p-3 rounded-lg bg-status-low/10 border border-status-low/20">
                    <Badge
                      variant="outline"
                      className="bg-status-low/10 border-status-low text-status-low"
                    >
                      Low
                    </Badge>
                    <span className="text-xl font-bold text-foreground">
                      {insights.insights.severity_distribution.low}
                    </span>
                  </div>
                )}

                {(!insights.insights?.severity_distribution ||
                  Object.values(
                    insights.insights.severity_distribution || {}
                  ).every((count) => count === 0)) && (
                  <div className="text-center py-4">
                    <p className="text-muted-foreground text-sm">
                      No incidents reported yet
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card
            className="lg:col-span-2 animate-scale-in"
            style={{ animationDelay: "0.1s" }}
          >
            <CardHeader className="bg-gradient-to-r from-primary/10 to-accent/10">
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-primary" />
                  Department-Level AI Insights
                </CardTitle>
                {insights.ai_summary?.consolidated_summary && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleRegenerateAI}
                    disabled={aiRegenerating}
                  >
                    {aiRegenerating ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Regenerating...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Regenerate
                      </>
                    )}
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              {aiRegenerating ? (
                <div className="flex items-center justify-center py-8">
                  <div className="text-center">
                    <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto mb-2" />
                    <p className="text-muted-foreground">
                      Regenerating AI insights...
                    </p>
                  </div>
                </div>
              ) : insights.ai_summary?.consolidated_summary ? (
                <div className="prose prose-sm max-w-none">
                  <p className="text-foreground leading-relaxed text-base">
                    {insights.ai_summary.consolidated_summary}
                  </p>
                </div>
              ) : (
                <div className="text-center py-4">
                  <p className="text-muted-foreground italic mb-4">
                    AI insights will be generated when you view this page.
                  </p>
                  <Button
                    variant="outline"
                    onClick={handleRegenerateAI}
                    disabled={aiRegenerating}
                  >
                    {aiRegenerating ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-4 w-4 mr-2" />
                        Generate AI Summary
                      </>
                    )}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="mb-4">
          <h2 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <AlertCircle className="h-6 w-6 text-primary" />
            All Incidents
          </h2>
          <p className="text-muted-foreground mt-1">
            Click on any incident to view detailed AI analysis
          </p>
        </div>

        {lessons.length === 0 ? (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              No incidents have been reported for this department yet.
            </AlertDescription>
          </Alert>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {lessons.map((incident, index) => (
              <Link
                key={incident.id}
                to={`/department/${department}/incident/${incident.id}`}
                className="block animate-scale-in hover:scale-105 transition-transform duration-200"
                style={{ animationDelay: `${0.3 + index * 0.05}s` }}
              >
                <Card className="h-full hover:shadow-xl transition-shadow cursor-pointer border-2 hover:border-primary/50">
                  <CardHeader>
                    <div className="flex items-center justify-between mb-2">
                      <CardTitle className="text-lg">
                        Incident #{incident.id}
                      </CardTitle>
                      <Badge
                        variant="outline"
                        className={severityColors[incident.severity]}
                      >
                        {incident.severity.charAt(0).toUpperCase() +
                          incident.severity.slice(1)}
                      </Badge>
                    </div>
                    <p className="text-sm font-semibold text-primary">
                      {incident.commodity}
                    </p>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                      {incident.problem_description}
                    </p>
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>{incident.reporter_name}</span>
                      <span>
                        {new Date(incident.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default DepartmentDetails;
