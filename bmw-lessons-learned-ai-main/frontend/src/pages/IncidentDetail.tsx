import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  AlertCircle,
  Calendar,
  User,
  FileText,
  Sparkles,
  CheckCircle2,
  ShieldCheck,
  Loader2,
  Download,
  Image as ImageIcon,
} from "lucide-react";
import Navigation from "@/components/Navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { lessonService, fileService } from "@/services";
import type { LessonLearned } from "@/types/api";
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

const IncidentDetail = () => {
  const { department, incidentId } = useParams<{
    department: string;
    incidentId: string;
  }>();
  const navigate = useNavigate();

  const [lesson, setLesson] = useState<LessonLearned | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchLesson = async () => {
      if (!incidentId) {
        setError("No incident ID provided");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const data = await lessonService.getLessonById(incidentId);
        setLesson(data);
        setError(null);
      } catch (err) {
        console.error("Error fetching lesson:", err);
        setError(
          err instanceof Error ? err.message : "Failed to load incident details"
        );
        toast.error("Failed to load incident", {
          description:
            err instanceof Error ? err.message : "Please try again later",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchLesson();
  }, [incidentId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <div className="container mx-auto px-4 py-8 flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
            <p className="text-muted-foreground">Loading incident details...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !lesson) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <div className="container mx-auto px-4 py-8">
          <Button
            variant="ghost"
            onClick={() =>
              navigate(`/department/${department || "engineering"}`)
            }
            className="mb-6"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Department
          </Button>
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error || "Incident not found"}</AlertDescription>
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <div className="container mx-auto px-4 py-8">
        <Button
          variant="ghost"
          onClick={() =>
            navigate(
              `/department/${department || lesson.department.toLowerCase()}`
            )
          }
          className="mb-6"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to {formatDepartmentName(lesson.department)} Department
        </Button>

        <div className="mb-8 animate-fade-in">
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-4xl font-bold text-foreground">
              Incident #{lesson.id}
            </h1>
            <Badge
              variant="outline"
              className={severityColors[lesson.severity]}
            >
              {lesson.severity.charAt(0).toUpperCase() +
                lesson.severity.slice(1)}
            </Badge>
          </div>
          <p className="text-xl text-muted-foreground">{lesson.commodity}</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            {/* Incident Details Card */}
            <Card className="animate-scale-in hover:shadow-lg transition-shadow">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-primary" />
                  Incident Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h3 className="font-semibold text-foreground mb-2">
                    Problem Description
                  </h3>
                  <p className="text-muted-foreground leading-relaxed">
                    {lesson.problem_description}
                  </p>
                </div>

                {lesson.part_number && (
                  <div>
                    <h3 className="font-semibold text-foreground mb-2">
                      Part Number
                    </h3>
                    <p className="text-muted-foreground font-mono">
                      {lesson.part_number}
                    </p>
                  </div>
                )}

                {lesson.supplier && (
                  <div>
                    <h3 className="font-semibold text-foreground mb-2">
                      Supplier
                    </h3>
                    <p className="text-muted-foreground">{lesson.supplier}</p>
                  </div>
                )}

                <div>
                  <h3 className="font-semibold text-foreground mb-2">
                    Error Location
                  </h3>
                  <p className="text-muted-foreground leading-relaxed">
                    {lesson.error_location}
                  </p>
                </div>

                <div>
                  <h3 className="font-semibold text-foreground mb-2">
                    Missed Detection
                  </h3>
                  <p className="text-muted-foreground leading-relaxed">
                    {lesson.missed_detection}
                  </p>
                </div>

                <div>
                  <h3 className="font-semibold text-foreground mb-2">
                    Provided Solution
                  </h3>
                  <p className="text-muted-foreground leading-relaxed">
                    {lesson.provided_solution}
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* AI Analysis Card */}
            {lesson.ai_analysis && (
              <Card
                className="animate-scale-in hover:shadow-lg transition-shadow border-primary/20"
                style={{ animationDelay: "0.1s" }}
              >
                <CardHeader className="bg-gradient-to-r from-primary/10 to-accent/10">
                  <CardTitle className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-primary" />
                    AI-Powered Analysis
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-6 space-y-6">
                  {/* Lesson Summary */}
                  <div>
                    <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
                      <AlertCircle className="h-4 w-4 text-primary" />
                      Summary
                    </h3>
                    <p className="text-foreground leading-relaxed bg-muted/50 p-4 rounded-lg">
                      {lesson.ai_analysis.lesson_summary}
                    </p>
                  </div>

                  {/* Detailed Analysis */}
                  <div>
                    <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
                      <FileText className="h-4 w-4 text-primary" />
                      Detailed Analysis
                    </h3>
                    <p className="text-muted-foreground leading-relaxed">
                      {lesson.ai_analysis.lesson_detailed}
                    </p>
                  </div>

                  {/* Best Practices */}
                  {lesson.ai_analysis.best_practice &&
                    lesson.ai_analysis.best_practice.length > 0 && (
                      <div>
                        <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
                          <CheckCircle2 className="h-4 w-4 text-green-600" />
                          Best Practices
                        </h3>
                        <ul className="space-y-2">
                          {lesson.ai_analysis.best_practice.map(
                            (practice, index) => (
                              <li
                                key={index}
                                className="flex items-start gap-3 p-3 rounded-lg bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-900"
                              >
                                <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                                <span className="text-sm text-foreground">
                                  {practice}
                                </span>
                              </li>
                            )
                          )}
                        </ul>
                      </div>
                    )}

                  {/* Preventive Actions */}
                  {lesson.ai_analysis.preventive_actions &&
                    lesson.ai_analysis.preventive_actions.length > 0 && (
                      <div>
                        <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
                          <ShieldCheck className="h-4 w-4 text-blue-600" />
                          Preventive Actions
                        </h3>
                        <ul className="space-y-2">
                          {lesson.ai_analysis.preventive_actions.map(
                            (action, index) => (
                              <li
                                key={index}
                                className="flex items-start gap-3 p-3 rounded-lg bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900"
                              >
                                <ShieldCheck className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
                                <span className="text-sm text-foreground">
                                  {action}
                                </span>
                              </li>
                            )
                          )}
                        </ul>
                      </div>
                    )}
                </CardContent>
              </Card>
            )}

            {/* Attachments Card */}
            {lesson.attachments && lesson.attachments.length > 0 && (
              <Card
                className="animate-scale-in hover:shadow-lg transition-shadow"
                style={{ animationDelay: "0.2s" }}
              >
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <ImageIcon className="h-5 w-5 text-primary" />
                    Attachments ({lesson.attachments.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {lesson.attachments.map((filename, index) => {
                      const fileUrl = fileService.getFileUrl(filename);
                      const isPdf = filename.toLowerCase().endsWith(".pdf");

                      return (
                        <div
                          key={index}
                          className="group relative aspect-square rounded-lg overflow-hidden border border-border hover:border-primary transition-colors"
                        >
                          {isPdf ? (
                            <div className="flex flex-col items-center justify-center h-full bg-muted p-4">
                              <FileText className="h-12 w-12 text-muted-foreground mb-2" />
                              <span className="text-xs text-center text-muted-foreground truncate w-full px-2">
                                {filename}
                              </span>
                            </div>
                          ) : (
                            <img
                              src={fileUrl}
                              alt={`Attachment ${index + 1}`}
                              className="w-full h-full object-cover"
                            />
                          )}
                          <a
                            href={fileUrl}
                            download={filename}
                            className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
                          >
                            <Download className="h-8 w-8 text-white" />
                          </a>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <Card
              className="animate-scale-in"
              style={{ animationDelay: "0.3s" }}
            >
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-primary" />
                  Metadata
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                  <Calendar className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="text-xs text-muted-foreground">
                      Reported Date
                    </p>
                    <p className="font-semibold text-foreground text-sm">
                      {formatDate(lesson.created_at)}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                  <User className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="text-xs text-muted-foreground">Reporter</p>
                    <p className="font-semibold text-foreground">
                      {lesson.reporter_name}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                  <FileText className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="text-xs text-muted-foreground">Department</p>
                    <p className="font-semibold text-foreground">
                      {formatDepartmentName(lesson.department)}
                    </p>
                  </div>
                </div>

                {lesson.updated_at !== lesson.created_at && (
                  <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                    <Calendar className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">
                        Last Updated
                      </p>
                      <p className="font-semibold text-foreground text-sm">
                        {formatDate(lesson.updated_at)}
                      </p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IncidentDetail;
