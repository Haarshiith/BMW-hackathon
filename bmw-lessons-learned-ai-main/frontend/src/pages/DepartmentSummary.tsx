import { useEffect, useState } from "react";
import {
  AlertCircle,
  TrendingUp,
  BarChart3,
  Package,
  Users,
  Settings,
  Loader2,
} from "lucide-react";
import { Link } from "react-router-dom";
import Navigation from "@/components/Navigation";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { departmentService } from "@/services";
import { toast } from "sonner";

// Define the actual backend response structure for department insights
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

// Icon mapping for departments
const iconMap: Record<string, any> = {
  engineering: Settings,
  manufacturing: Package,
  sales: TrendingUp,
  quality: BarChart3,
  it: AlertCircle,
  hr: Users,
};

interface DepartmentData {
  name: string;
  total: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
}

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

const DepartmentSummary = () => {
  const [departments, setDepartments] = useState<string[]>([]);
  const [departmentStats, setDepartmentStats] = useState<
    Record<string, DepartmentData>
  >({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDepartments = async () => {
      try {
        setLoading(true);

        // Get list of all departments
        const deptList = await departmentService.getDepartments();
        console.log(
          "Departments received:",
          deptList,
          "Type:",
          typeof deptList,
          "Is Array:",
          Array.isArray(deptList)
        );

        // Ensure we have an array
        if (!Array.isArray(deptList)) {
          console.error("Expected array but got:", deptList);
          setDepartments([]);
          setDepartmentStats({});
        } else {
          setDepartments(deptList);

          // Fetch statistics for each department (no AI calls)
          const statsPromises = deptList.map(async (dept) => {
            try {
              const stats = await departmentService.getDepartmentStatistics(
                dept
              );
              return {
                name: dept,
                total: stats.total_lessons,
                critical: stats.severity_breakdown.critical,
                high: stats.severity_breakdown.high,
                medium: stats.severity_breakdown.medium,
                low: stats.severity_breakdown.low,
              };
            } catch (err) {
              console.error(`Error fetching stats for ${dept}:`, err);
              return {
                name: dept,
                total: 0,
                critical: 0,
                high: 0,
                medium: 0,
                low: 0,
              };
            }
          });

          const stats = await Promise.all(statsPromises);
          const statsMap: Record<string, DepartmentData> = {};
          stats.forEach((stat) => {
            statsMap[stat.name.toLowerCase()] = stat;
          });
          setDepartmentStats(statsMap);
        }
        setError(null);
      } catch (err) {
        console.error("Error fetching departments:", err);
        const errorMessage =
          err instanceof Error ? err.message : "Failed to load departments";
        setError(errorMessage);
        toast.error("Failed to load departments", {
          description: errorMessage,
        });
      } finally {
        setLoading(false);
      }
    };

    fetchDepartments();
  }, []);

  // Removed: AI summaries are now only generated when viewing department details
  // This improves initial page load performance

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <div className="container mx-auto px-4 py-8 flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
            <p className="text-muted-foreground">Loading departments...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <div className="container mx-auto px-4 py-8">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <div className="container mx-auto px-4 py-8">
        <div className="mb-8 animate-fade-in">
          <h1 className="text-3xl font-bold text-foreground mb-2">
            Department Summary Dashboard
          </h1>
          <p className="text-muted-foreground">
            AI-powered insights and incident analytics across all departments
          </p>
        </div>

        {departments.length === 0 ? (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              No departments found. Submit an incident report to create the
              first department entry.
            </AlertDescription>
          </Alert>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {departments.map((dept, index) => {
              const deptKey = dept.toLowerCase();
              const Icon = iconMap[deptKey] || Package;
              const stats = departmentStats[deptKey] || {
                name: dept,
                total: 0,
                critical: 0,
                high: 0,
                medium: 0,
                low: 0,
              };

              return (
                <Link
                  key={dept}
                  to={`/department/${deptKey}`}
                  className="bg-card rounded-lg shadow-lg border border-border overflow-hidden hover:shadow-xl hover:scale-105 transition-all duration-200 block animate-scale-in"
                  style={{ animationDelay: `${index * 0.1}s` }}
                >
                  <div className="bg-primary p-6">
                    <div className="flex items-center gap-3 text-primary-foreground">
                      <Icon className="h-8 w-8" />
                      <h2 className="text-2xl font-bold">
                        {formatDepartmentName(dept)}
                      </h2>
                    </div>
                  </div>

                  <div className="p-6">
                    <div className="mb-6">
                      <div className="flex items-baseline gap-2 mb-4">
                        <span className="text-4xl font-bold text-foreground">
                          {stats.total}
                        </span>
                        <span className="text-muted-foreground">
                          {stats.total === 1 ? "incident" : "incidents"}
                        </span>
                      </div>

                      {stats.total > 0 && (
                        <div className="grid grid-cols-2 gap-3">
                          {stats.critical > 0 && (
                            <div className="flex items-center gap-2">
                              <Badge
                                variant="outline"
                                className="bg-status-critical/10 border-status-critical text-status-critical"
                              >
                                Critical
                              </Badge>
                              <span className="font-semibold text-foreground">
                                {stats.critical}
                              </span>
                            </div>
                          )}
                          {stats.high > 0 && (
                            <div className="flex items-center gap-2">
                              <Badge
                                variant="outline"
                                className="bg-status-high/10 border-status-high text-status-high"
                              >
                                High
                              </Badge>
                              <span className="font-semibold text-foreground">
                                {stats.high}
                              </span>
                            </div>
                          )}
                          {stats.medium > 0 && (
                            <div className="flex items-center gap-2">
                              <Badge
                                variant="outline"
                                className="bg-status-medium/10 border-status-medium text-status-medium"
                              >
                                Medium
                              </Badge>
                              <span className="font-semibold text-foreground">
                                {stats.medium}
                              </span>
                            </div>
                          )}
                          {stats.low > 0 && (
                            <div className="flex items-center gap-2">
                              <Badge
                                variant="outline"
                                className="bg-status-low/10 border-status-low text-status-low"
                              >
                                Low
                              </Badge>
                              <span className="font-semibold text-foreground">
                                {stats.low}
                              </span>
                            </div>
                          )}
                        </div>
                      )}

                      {stats.total === 0 && (
                        <p className="text-sm text-muted-foreground italic">
                          No incidents reported yet
                        </p>
                      )}
                    </div>

                    <div className="border-t border-border pt-4">
                      <h3 className="font-semibold text-foreground mb-2 flex items-center gap-2">
                        <BarChart3 className="h-4 w-4 text-primary" />
                        View Details
                      </h3>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        Click to view comprehensive analytics and AI-powered
                        insights for this department
                      </p>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default DepartmentSummary;
