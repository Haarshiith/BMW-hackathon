import { useEffect, useState } from "react";
import {
  CheckCircle,
  Clock,
  Database,
  FileText,
  Globe,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { solutionSearchService } from "@/services/solutionSearchService";
import type { SearchStatusResponse } from "@/types/solutionSearch";

interface SearchProgressProps {
  searchId: number;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

interface SearchSource {
  id: string;
  name: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
  completed: boolean;
  estimatedTime: number; // in seconds
}

export const SearchProgress = ({
  searchId,
  onComplete,
  onError,
}: SearchProgressProps) => {
  const [status, setStatus] = useState<SearchStatusResponse | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [isPolling, setIsPolling] = useState(true);

  const searchSources: SearchSource[] = [
    {
      id: "database",
      name: "Internal Database",
      icon: Database,
      description: "Searching our incident database for similar problems",
      completed: false,
      estimatedTime: 3,
    },
    {
      id: "rag",
      name: "Knowledge Base",
      icon: FileText,
      description: "Analyzing Excel data and historical cases",
      completed: false,
      estimatedTime: 4,
    },
    {
      id: "web",
      name: "Web Search",
      icon: Globe,
      description: "Searching the web for external solutions",
      completed: false,
      estimatedTime: 6,
    },
  ];

  // Update search sources based on status
  const updatedSources = searchSources.map((source) => ({
    ...source,
    completed:
      status?.progress[
        `${source.id}_completed` as keyof typeof status.progress
      ] || false,
  }));

  // Determine which source is currently being processed
  const getCurrentSourceIndex = () => {
    for (let i = 0; i < updatedSources.length; i++) {
      if (!updatedSources[i].completed) {
        return i;
      }
    }
    return -1; // All completed
  };

  const totalSources = updatedSources.length;
  const completedSources = updatedSources.filter(
    (source) => source.completed
  ).length;
  const currentSourceIndex = getCurrentSourceIndex();

  // Calculate more accurate progress including current source progress
  let progressPercentage = (completedSources / totalSources) * 100;

  // Add partial progress for current source
  if (currentSourceIndex >= 0 && currentSourceIndex < updatedSources.length) {
    const currentSource = updatedSources[currentSourceIndex];
    const currentSourceProgress = Math.min(
      (elapsedTime / currentSource.estimatedTime) * 100,
      100
    );
    progressPercentage += currentSourceProgress / totalSources;
  }

  // Elapsed time counter
  useEffect(() => {
    const interval = setInterval(() => {
      setElapsedTime((prev) => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // Poll for search status
  useEffect(() => {
    let pollInterval: NodeJS.Timeout;

    const pollStatus = async () => {
      try {
        const statusResponse = await solutionSearchService.getSearchStatus(
          searchId
        );
        setStatus(statusResponse);

        // Check if search is completed or failed
        if (statusResponse.status === "completed") {
          setIsPolling(false);
          onComplete?.();
        } else if (statusResponse.status === "failed") {
          setIsPolling(false);
          onError?.("Search failed");
        }
      } catch (error) {
        console.error("Error polling search status:", error);
        onError?.(
          error instanceof Error ? error.message : "Failed to get search status"
        );
      }
    };

    // Start polling immediately, then every 2 seconds
    pollStatus();
    pollInterval = setInterval(pollStatus, 2000);

    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [searchId, onComplete, onError]);

  // Format time display
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  // Get estimated total time
  const estimatedTotalTime = updatedSources.reduce((total, source) => {
    return source.completed ? total : total + source.estimatedTime;
  }, 0);

  // Get current status
  const getStatusIcon = (completed: boolean, isCurrent: boolean) => {
    if (completed) {
      return <CheckCircle className="h-5 w-5 text-green-500" />;
    } else if (isCurrent) {
      return <Loader2 className="h-5 w-5 text-primary animate-spin" />;
    } else {
      return <Clock className="h-5 w-5 text-muted-foreground" />;
    }
  };

  const getStatusText = (completed: boolean, isCurrent: boolean) => {
    if (completed) {
      return "Completed";
    } else if (isCurrent) {
      return "Searching...";
    } else {
      return "Waiting...";
    }
  };

  const getStatusColor = (completed: boolean, isCurrent: boolean) => {
    if (completed) {
      return "bg-green-100 text-green-800 border-green-200";
    } else if (isCurrent) {
      return "bg-primary/10 text-primary border-primary/20";
    } else {
      return "bg-muted text-muted-foreground border-muted";
    }
  };

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Loader2 className="h-5 w-5 animate-spin text-primary" />
          {status?.status === "completed"
            ? "Search Completed"
            : status?.status === "failed"
            ? "Search Failed"
            : "Searching for Solutions"}
        </CardTitle>
        <div className="flex items-center justify-between">
          <p className="text-muted-foreground">
            Search ID: #{searchId} • Elapsed: {formatTime(elapsedTime)}
          </p>
          <Badge variant="outline" className="text-sm">
            {completedSources}/{totalSources} sources completed
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Overall Progress</span>
            <span>{Math.round(progressPercentage)}%</span>
          </div>
          <Progress value={progressPercentage} className="h-2" />
        </div>

        {/* Search Sources */}
        <div className="space-y-4">
          {updatedSources.map((source, index) => {
            const Icon = source.icon;
            const isCurrent = index === currentSourceIndex;
            const isCompleted = source.completed;

            return (
              <div
                key={source.id}
                className={`p-4 rounded-lg border transition-all duration-300 ${
                  isCurrent
                    ? "border-primary/50 bg-primary/5"
                    : isCompleted
                    ? "border-green-200 bg-green-50"
                    : "border-muted bg-muted/30"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(isCompleted, isCurrent)}
                    <Icon
                      className={`h-5 w-5 ${
                        isCompleted
                          ? "text-green-600"
                          : isCurrent
                          ? "text-primary"
                          : "text-muted-foreground"
                      }`}
                    />
                    <div>
                      <h3 className="font-medium">{source.name}</h3>
                      <p className="text-sm text-muted-foreground">
                        {source.description}
                      </p>
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={getStatusColor(isCompleted, isCurrent)}
                  >
                    {getStatusText(isCompleted, isCurrent)}
                  </Badge>
                </div>
              </div>
            );
          })}
        </div>

        {/* Status Messages */}
        {status?.status === "failed" && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Search failed. Please try again.
            </AlertDescription>
          </Alert>
        )}

        {status?.status === "completed" && (
          <Alert>
            <CheckCircle className="h-4 w-4" />
            <AlertDescription>Search completed successfully!</AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};
