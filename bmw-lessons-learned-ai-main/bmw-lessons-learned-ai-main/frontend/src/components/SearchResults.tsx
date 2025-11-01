import { useState } from "react";
import { 
  Database, 
  FileText, 
  Globe, 
  ExternalLink, 
  RefreshCw,
  Filter,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Clock,
  Eye
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import IncidentDetailsModal from "./IncidentDetailsModal";
import type { SearchResult, SearchSource, SolutionSearchResponse } from "@/types/solutionSearch";

interface SearchResultsProps {
  searchResponse: SolutionSearchResponse;
  onRefineSearch?: () => void;
}

interface ResultGroup {
  source: SearchSource;
  results: SearchResult[];
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
}

export const SearchResults = ({ 
  searchResponse, 
  onRefineSearch
}: SearchResultsProps) => {
  const [activeTab, setActiveTab] = useState("summary");
  const [selectedIncidentId, setSelectedIncidentId] = useState<number | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Group results by source
  const resultGroups: ResultGroup[] = [
    {
      source: "database",
      results: searchResponse.results.filter(r => r.source === "database"),
      icon: Database,
      title: "Internal Solutions",
      description: "Solutions from our incident database"
    },
    {
      source: "rag",
      results: searchResponse.results.filter(r => r.source === "rag"),
      icon: FileText,
      title: "Knowledge Base",
      description: "Solutions from our Excel knowledge base"
    },
    {
      source: "web",
      results: searchResponse.results.filter(r => r.source === "web"),
      icon: Globe,
      title: "External Solutions",
      description: "Solutions found on the web"
    }
  ];

  // Get confidence color
  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return "bg-green-100 text-green-800 border-green-200";
    if (score >= 0.6) return "bg-yellow-100 text-yellow-800 border-yellow-200";
    if (score >= 0.4) return "bg-orange-100 text-orange-800 border-orange-200";
    return "bg-red-100 text-red-800 border-red-200";
  };

  // Get confidence label
  const getConfidenceLabel = (score: number) => {
    if (score >= 0.8) return "High";
    if (score >= 0.6) return "Medium";
    if (score >= 0.4) return "Low";
    return "Very Low";
  };



  // Handle view incident details
  const handleViewIncidentDetails = (incidentId: number) => {
    setSelectedIncidentId(incidentId);
    setIsModalOpen(true);
  };

  // Handle close modal
  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedIncidentId(null);
  };

  // Render individual result
  const renderResult = (result: SearchResult, index: number) => {
    return (
      <Card key={`${result.source}-${index}`} className="mb-4 hover:shadow-md transition-shadow">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className="text-lg mb-2">{result.title}</CardTitle>
              <div className="flex items-center gap-2 mb-2">
                <Badge variant="outline" className="text-xs">
                  {result.source.toUpperCase()}
                </Badge>
                <Badge className={getConfidenceColor(result.relevance_score)}>
                  {getConfidenceLabel(result.relevance_score)} Confidence
                </Badge>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {result.source === "database" && result.metadata?.incident_id && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleViewIncidentDetails(result.metadata!.incident_id!)}
                >
                  <Eye className="h-4 w-4 mr-1" />
                  View Details
                </Button>
              )}
              {result.url && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => window.open(result.url, '_blank')}
                >
                  <ExternalLink className="h-4 w-4 mr-1" />
                  View
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground mb-3">{result.description}</p>
          
          {/* Only show solution for internal database results, not for external web results */}
          {result.solution && result.source !== "web" && (
            <div className="bg-muted/50 p-3 rounded-lg mb-3">
              <h4 className="font-medium mb-2 flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                Suggested Solution
              </h4>
              <p className="text-sm">{result.solution}</p>
            </div>
          )}

          {result.metadata && (
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              {result.metadata.incident_id && (
                <span>Incident #{result.metadata.incident_id}</span>
              )}
              {result.metadata.department && (
                <span>Department: {result.metadata.department}</span>
              )}
              {result.metadata.severity && (
                <span>Severity: {result.metadata.severity}</span>
              )}
              {result.metadata.created_at && (
                <span>Date: {new Date(result.metadata.created_at).toLocaleDateString()}</span>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  // Render results for a specific source
  const renderSourceResults = (group: ResultGroup) => {
    if (group.results.length === 0) {
      return (
        <div className="text-center py-8 text-muted-foreground">
          <AlertCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>No results found from {group.title.toLowerCase()}</p>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {group.results.map((result, index) => renderResult(result, index))}
      </div>
    );
  };

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      {/* Summary Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-primary" />
                Search Results
              </CardTitle>
              <p className="text-muted-foreground mt-1">
                Found {searchResponse.results.length} potential solutions
              </p>
            </div>
            <div className="text-right">
              <Badge className="bg-primary/10 text-primary border-primary/20">
                {Math.round(searchResponse.confidence_score * 100)}% Confidence
              </Badge>
              <p className="text-xs text-muted-foreground mt-1">
                Overall solution quality
              </p>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div>
              <h4 className="font-medium mb-2">AI Summary</h4>
              <p className="text-muted-foreground">{searchResponse.summary}</p>
            </div>
            
            <Separator />
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {resultGroups.map((group) => {
                const Icon = group.icon;
                return (
                  <div key={group.source} className="text-center">
                    <Icon className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                    <p className="font-medium">{group.results.length}</p>
                    <p className="text-xs text-muted-foreground">{group.title}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="summary">Summary</TabsTrigger>
          <TabsTrigger value="internal">
            Internal ({resultGroups.find(g => g.source === "database")?.results.length || 0})
          </TabsTrigger>
          <TabsTrigger value="knowledge">
            Knowledge ({resultGroups.find(g => g.source === "rag")?.results.length || 0})
          </TabsTrigger>
          <TabsTrigger value="external">
            External ({resultGroups.find(g => g.source === "web")?.results.length || 0})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="summary" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Solution Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">AI-Generated Summary</h4>
                  <p className="text-muted-foreground">{searchResponse.summary}</p>
                </div>
                
                <Separator />
                
                <div>
                  <h4 className="font-medium mb-2">Confidence Analysis</h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Overall Confidence</span>
                      <span className="text-sm font-medium">
                        {Math.round(searchResponse.confidence_score * 100)}%
                      </span>
                    </div>
                    <Progress value={searchResponse.confidence_score * 100} className="h-2" />
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button onClick={onRefineSearch} variant="outline">
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Refine Search
                  </Button>
                  <Button variant="outline">
                    <Filter className="h-4 w-4 mr-2" />
                    Filter Results
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="internal">
          {renderSourceResults(resultGroups.find(g => g.source === "database") || resultGroups[0])}
        </TabsContent>

        <TabsContent value="knowledge">
          {renderSourceResults(resultGroups.find(g => g.source === "rag") || resultGroups[0])}
        </TabsContent>

        <TabsContent value="external">
          {renderSourceResults(resultGroups.find(g => g.source === "web") || resultGroups[0])}
        </TabsContent>
      </Tabs>

      {/* No Results Alert */}
      {searchResponse.results.length === 0 && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            No solutions found for your problem. Try refining your search terms or 
            contact support for assistance.
          </AlertDescription>
        </Alert>
      )}

      {/* Incident Details Modal */}
      {selectedIncidentId && (
        <IncidentDetailsModal
          incidentId={selectedIncidentId}
          isOpen={isModalOpen}
          onClose={handleCloseModal}
        />
      )}
    </div>
  );
};
