import { useState } from "react";
import { AlertCircle, ArrowLeft, Search, Lightbulb } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Navigation from "@/components/Navigation";
import { SolutionSearchForm } from "@/components/SolutionSearchForm";
import { SearchProgress } from "@/components/SearchProgress";
import { SearchResults } from "@/components/SearchResults";
import { solutionSearchService } from "@/services/solutionSearchService";
import type {
  SolutionSearchFormData,
  SolutionSearchResponse,
  SearchStatusResponse,
} from "@/types/solutionSearch";
import { toast } from "sonner";

type SearchState = "form" | "searching" | "results" | "error";

const SolutionSearch = () => {
  const [searchState, setSearchState] = useState<SearchState>("form");
  const [searchId, setSearchId] = useState<number | null>(null);
  const [searchResponse, setSearchResponse] =
    useState<SolutionSearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleFormSubmit = async (formData: SolutionSearchFormData) => {
    try {
      setIsSubmitting(true);
      setError(null);

      // Submit the search request
      const response = await solutionSearchService.submitSolutionSearch({
        problem_description: formData.problem_description,
        department: formData.department,
        severity: formData.severity,
        reporter_name: formData.reporter_name,
      });

      setSearchId(response.search_id);
      setSearchState("searching");

      // Start polling for results
      const finalResponse = await solutionSearchService.pollSearchStatus(
        response.search_id,
        (status: SearchStatusResponse) => {
          // Update progress in real-time
          console.log("Search progress:", status);
        }
      );

      setSearchResponse(finalResponse);
      setSearchState("results");

      toast.success("Search completed!", {
        description: `Found ${finalResponse.results.length} potential solutions.`,
      });
    } catch (err) {
      console.error("Error during solution search:", err);
      const errorMessage =
        err instanceof Error ? err.message : "An unexpected error occurred";
      setError(errorMessage);
      setSearchState("error");

      toast.error("Search failed", {
        description: errorMessage,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRefineSearch = () => {
    // Reset to form with current search data
    setSearchState("form");
    setSearchId(null);
    setSearchResponse(null);
    setError(null);
  };

  const handleSaveSolution = async (resultId: string, notes?: string) => {
    if (!searchId) return;

    try {
      await solutionSearchService.saveSolution(searchId, resultId, notes);
      toast.success("Solution saved!", {
        description: "You can find it in your saved solutions.",
      });
    } catch (err) {
      console.error("Error saving solution:", err);
      toast.error("Failed to save solution", {
        description: "Please try again later.",
      });
    }
  };

  const handleStartNewSearch = () => {
    setSearchState("form");
    setSearchId(null);
    setSearchResponse(null);
    setError(null);
  };

  const renderContent = () => {
    switch (searchState) {
      case "form":
        return (
          <div className="space-y-6">
            <div className="text-center space-y-4">
              <div className="flex items-center justify-center gap-2">
                <Search className="h-8 w-8 text-primary" />
                <h1 className="text-3xl font-bold">Find Solutions</h1>
              </div>
              <p className="text-muted-foreground max-w-2xl mx-auto">
                Describe your problem and our AI will search across our
                database, knowledge base, and the web to find the most relevant
                solutions for you.
              </p>
            </div>

            <SolutionSearchForm
              onSubmit={handleFormSubmit}
              isLoading={isSubmitting}
            />
          </div>
        );

      case "searching":
        return (
          <div className="space-y-6">
            <div className="text-center space-y-4">
              <div className="flex items-center justify-center gap-2">
                <Search className="h-8 w-8 text-primary animate-pulse" />
                <h1 className="text-3xl font-bold">Searching for Solutions</h1>
              </div>
              <p className="text-muted-foreground">
                We're analyzing your problem across multiple sources...
              </p>
            </div>

            {searchId && (
              <SearchProgress
                searchId={searchId}
                onComplete={() => {
                  // This will be handled by the polling in handleFormSubmit
                }}
                onError={(error) => {
                  setError(error);
                  setSearchState("error");
                }}
              />
            )}
          </div>
        );

      case "results":
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Lightbulb className="h-8 w-8 text-primary" />
                <h1 className="text-3xl font-bold">Search Results</h1>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={handleRefineSearch}>
                  <Search className="h-4 w-4 mr-2" />
                  Refine Search
                </Button>
                <Button variant="outline" onClick={handleStartNewSearch}>
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  New Search
                </Button>
              </div>
            </div>

            {searchResponse && (
              <SearchResults
                searchResponse={searchResponse}
                onRefineSearch={handleRefineSearch}
                onSaveSolution={handleSaveSolution}
              />
            )}
          </div>
        );

      case "error":
        return (
          <div className="space-y-6">
            <div className="text-center space-y-4">
              <AlertCircle className="h-16 w-16 text-destructive mx-auto" />
              <h1 className="text-3xl font-bold">Search Failed</h1>
              <p className="text-muted-foreground">
                We encountered an error while searching for solutions.
              </p>
            </div>

            <Card className="max-w-2xl mx-auto">
              <CardHeader>
                <CardTitle>Error Details</CardTitle>
              </CardHeader>
              <CardContent>
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    {error ||
                      "An unexpected error occurred during the search process."}
                  </AlertDescription>
                </Alert>

                <div className="flex gap-2 mt-4">
                  <Button onClick={handleStartNewSearch} className="flex-1">
                    Try Again
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setSearchState("form")}
                  >
                    Back to Form
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      <div className="container mx-auto px-4 py-8">{renderContent()}</div>
    </div>
  );
};

export default SolutionSearch;
