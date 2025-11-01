import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Loader2,
  CheckCircle,
  AlertCircle,
  Sparkles,
  CheckCircle2,
  ShieldCheck,
  FileText,
} from "lucide-react";
import Navigation from "@/components/Navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { lessonService } from "@/services";
import type { LessonLearned } from "@/types/api";
import { toast } from "sonner";

// Function to format department names for display
const formatDepartmentName = (name: string): string => {
  // Handle special cases
  const specialCases: Record<string, string> = {
    it: "IT",
    hr: "HR",
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

const AIProcessing = () => {
  const { lessonId } = useParams<{ lessonId: string }>();
  const navigate = useNavigate();

  const [lesson, setLesson] = useState<LessonLearned | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [processingTime, setProcessingTime] = useState(0);

  useEffect(() => {
    if (!lessonId) {
      setError("No lesson ID provided");
      setLoading(false);
      return;
    }

    const startTime = Date.now();
    const interval = setInterval(async () => {
      try {
        const lessonData = await lessonService.getLessonById(lessonId);
        setProcessingTime(Math.floor((Date.now() - startTime) / 1000));

        // Check if AI analysis is complete
        if (lessonData.ai_analysis && lessonData.ai_analysis.lesson_summary) {
          setLesson(lessonData);
          setLoading(false);
          clearInterval(interval);
          toast.success("AI analysis completed!", {
            description: "Your incident report has been analyzed successfully.",
          });
        }
      } catch (err) {
        console.error("Error fetching lesson:", err);
        setError(err instanceof Error ? err.message : "Failed to load lesson");
        setLoading(false);
        clearInterval(interval);
      }
    }, 2000); // Poll every 2 seconds

    // Cleanup interval on unmount
    return () => clearInterval(interval);
  }, [lessonId]);

  const formatTime = (seconds: number) => {
    if (seconds < 60) {
      return `${seconds}s`;
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  if (error) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <div className="container mx-auto px-4 py-8">
          <Card className="max-w-2xl mx-auto">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-destructive">
                <AlertCircle className="h-5 w-5" />
                Error Processing Report
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground mb-4">{error}</p>
              <div className="flex gap-2">
                <Button onClick={() => navigate("/")}>Back to Home</Button>
                <Button
                  variant="outline"
                  onClick={() => window.location.reload()}
                >
                  Try Again
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <div className="container mx-auto px-4 py-8">
          <Card className="max-w-2xl mx-auto">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                AI Analysis in Progress
              </CardTitle>
            </CardHeader>
            <CardContent className="text-center py-8">
              <div className="mb-6">
                <Loader2 className="h-16 w-16 animate-spin text-primary mx-auto mb-4" />
                <h3 className="text-xl font-semibold mb-2">
                  Processing Your Report
                </h3>
                <p className="text-muted-foreground mb-4">
                  Our AI is analyzing your incident report and generating
                  insights...
                </p>
                <div className="text-2xl font-bold text-primary">
                  {formatTime(processingTime)}
                </div>
                <p className="text-sm text-muted-foreground mt-2">
                  Processing time
                </p>
              </div>

              <div className="space-y-3 text-left">
                <div className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span className="text-sm">Report submitted successfully</span>
                </div>
                <div className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg">
                  <Loader2 className="h-5 w-5 animate-spin text-primary" />
                  <span className="text-sm">
                    AI analyzing incident details...
                  </span>
                </div>
                <div className="flex items-center gap-3 p-3 bg-muted/30 rounded-lg">
                  <div className="h-5 w-5 rounded-full border-2 border-muted-foreground" />
                  <span className="text-sm text-muted-foreground">
                    Generating insights and recommendations
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // AI analysis is complete, show results
  if (lesson && lesson.ai_analysis) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <div className="container mx-auto px-4 py-8">
          <Card className="max-w-4xl mx-auto mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                AI Analysis Complete
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Your incident report has been successfully analyzed. Processing
                took {formatTime(processingTime)}.
              </p>
            </CardContent>
          </Card>

          <div className="max-w-4xl mx-auto space-y-6">
            {/* Incident Summary */}
            <Card>
              <CardHeader>
                <CardTitle>Incident Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-semibold text-foreground mb-2">
                      Commodity
                    </h4>
                    <p className="text-muted-foreground">{lesson.commodity}</p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-foreground mb-2">
                      Department
                    </h4>
                    <p className="text-muted-foreground">
                      {formatDepartmentName(lesson.department)}
                    </p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-foreground mb-2">
                      Severity
                    </h4>
                    <Badge variant="outline" className="capitalize">
                      {lesson.severity}
                    </Badge>
                  </div>
                  <div>
                    <h4 className="font-semibold text-foreground mb-2">
                      Reporter
                    </h4>
                    <p className="text-muted-foreground">
                      {lesson.reporter_name}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* AI Analysis Results */}
            <Card className="border-primary/20">
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
                    Lesson Summary
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

            {/* Action Buttons */}
            <div className="flex gap-4 justify-center">
              <Button onClick={() => navigate("/")}>
                Submit Another Report
              </Button>
              <Button
                variant="outline"
                onClick={() =>
                  navigate(
                    `/department/${lesson.department}/incident/${lesson.id}`
                  )
                }
              >
                View Full Details
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default AIProcessing;
