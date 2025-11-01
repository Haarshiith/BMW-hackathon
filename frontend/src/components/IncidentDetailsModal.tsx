import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  X,
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
  ExternalLink,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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

interface IncidentDetailsModalProps {
  incidentId: number;
  isOpen: boolean;
  onClose: () => void;
}

const IncidentDetailsModal = ({
  incidentId,
  isOpen,
  onClose,
}: IncidentDetailsModalProps) => {
  const navigate = useNavigate();
  const [lesson, setLesson] = useState<LessonLearned | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchLesson = async () => {
      if (!incidentId || !isOpen) return;

      try {
        setLoading(true);
        setError(null);
        const data = await lessonService.getLessonById(incidentId.toString());
        setLesson(data);
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
  }, [incidentId, isOpen]);

  const handleDownloadAttachment = async (filename: string) => {
    try {
      await fileService.downloadFile(filename);
    } catch (error) {
      console.error("Error downloading file:", error);
      toast.error("Failed to download file");
    }
  };

  const handleViewFullPage = () => {
    if (lesson) {
      navigate(`/department/${lesson.department}/incident/${lesson.id}`);
      onClose();
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case "critical":
        return "bg-red-100 text-red-800 border-red-200";
      case "high":
        return "bg-orange-100 text-orange-800 border-orange-200";
      case "medium":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "low":
        return "bg-green-100 text-green-800 border-green-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  if (!isOpen) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-primary" />
              Incident Details
            </DialogTitle>
            {lesson && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleViewFullPage}
                className="flex items-center gap-2"
              >
                <ExternalLink className="h-4 w-4" />
                View Full Page
              </Button>
            )}
          </div>
        </DialogHeader>

        {loading && (
          <div className="flex items-center justify-center py-8">
            <div className="text-center">
              <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto mb-2" />
              <p className="text-muted-foreground">
                Loading incident details...
              </p>
            </div>
          </div>
        )}

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {lesson && !loading && (
          <div className="space-y-6">
            {/* Incident Header */}
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="space-y-2">
                    <CardTitle className="text-xl">
                      {lesson.commodity}
                    </CardTitle>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Calendar className="h-4 w-4" />
                        {new Date(lesson.created_at).toLocaleDateString()}
                      </div>
                      <div className="flex items-center gap-1">
                        <User className="h-4 w-4" />
                        {lesson.reporter_name}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={getSeverityColor(lesson.severity)}>
                      {lesson.severity.toUpperCase()}
                    </Badge>
                    <Badge variant="outline">
                      {formatDepartmentName(lesson.department)}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-6 space-y-6">
                {/* Basic Information */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {lesson.part_number && (
                    <div>
                      <h4 className="font-semibold text-foreground mb-2">
                        Part Number
                      </h4>
                      <p className="text-muted-foreground">
                        {lesson.part_number}
                      </p>
                    </div>
                  )}
                  {lesson.supplier && (
                    <div>
                      <h4 className="font-semibold text-foreground mb-2">
                        Supplier
                      </h4>
                      <p className="text-muted-foreground">{lesson.supplier}</p>
                    </div>
                  )}
                  <div>
                    <h4 className="font-semibold text-foreground mb-2">
                      Error Location
                    </h4>
                    <p className="text-muted-foreground">
                      {lesson.error_location}
                    </p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-foreground mb-2">
                      Missed Detection
                    </h4>
                    <p className="text-muted-foreground">
                      {lesson.missed_detection}
                    </p>
                  </div>
                </div>

                {/* Problem Description */}
                <div>
                  <h4 className="font-semibold text-foreground mb-2">
                    Problem Description
                  </h4>
                  <p className="text-muted-foreground leading-relaxed bg-muted/50 p-4 rounded-lg">
                    {lesson.problem_description}
                  </p>
                </div>

                {/* Provided Solution */}
                <div>
                  <h4 className="font-semibold text-foreground mb-2">
                    Provided Solution
                  </h4>
                  <p className="text-muted-foreground leading-relaxed bg-muted/50 p-4 rounded-lg">
                    {lesson.provided_solution}
                  </p>
                </div>

                {/* Attachments */}
                {lesson.attachments && lesson.attachments.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-foreground mb-3">
                      Attachments
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {lesson.attachments.map((attachment, index) => (
                        <div
                          key={index}
                          className="flex items-center justify-between p-3 border rounded-lg bg-muted/30"
                        >
                          <div className="flex items-center gap-2">
                            <ImageIcon className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm font-medium truncate">
                              {attachment}
                            </span>
                          </div>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDownloadAttachment(attachment)}
                          >
                            <Download className="h-3 w-3" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* AI Analysis */}
            {lesson.ai_analysis && (
              <Card className="border-primary/20">
                <CardHeader className="bg-gradient-to-r from-primary/10 to-accent/10">
                  <CardTitle className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-primary" />
                    AI Analysis
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
                          <ShieldCheck className="h-4 w-4 text-primary" />
                          Best Practices
                        </h3>
                        <div className="space-y-2">
                          {lesson.ai_analysis.best_practice.map(
                            (practice, index) => (
                              <div
                                key={index}
                                className="flex items-start gap-3 p-3 bg-green-50 border border-green-200 rounded-lg"
                              >
                                <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                                <p className="text-sm text-green-800">
                                  {practice}
                                </p>
                              </div>
                            )
                          )}
                        </div>
                      </div>
                    )}

                  {/* Preventive Actions */}
                  {lesson.ai_analysis.preventive_actions &&
                    lesson.ai_analysis.preventive_actions.length > 0 && (
                      <div>
                        <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
                          <ShieldCheck className="h-4 w-4 text-primary" />
                          Preventive Actions
                        </h3>
                        <div className="space-y-2">
                          {lesson.ai_analysis.preventive_actions.map(
                            (action, index) => (
                              <div
                                key={index}
                                className="flex items-start gap-3 p-3 bg-blue-50 border border-blue-200 rounded-lg"
                              >
                                <CheckCircle2 className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                                <p className="text-sm text-blue-800">
                                  {action}
                                </p>
                              </div>
                            )
                          )}
                        </div>
                      </div>
                    )}
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default IncidentDetailsModal;
