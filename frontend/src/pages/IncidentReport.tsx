import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { Upload, Send, Loader2, X } from "lucide-react";
import Navigation from "@/components/Navigation";
import { lessonService } from "@/services";
import { fileService } from "@/services";
import type { SeverityLevel } from "@/types/api";

const formSchema = z.object({
  commodity: z.string().min(1, "Commodity is required"),
  partNumber: z.string().optional(),
  supplier: z.string().optional(),
  problemDescription: z
    .string()
    .min(10, "Problem description must be at least 10 characters"),
  missedDetection: z.string().min(1, "Missed detection is required"),
  errorLocation: z.string().min(1, "Error location is required"),
  providedSolution: z.string().min(1, "Provided solution is required"),
  department: z.string().min(1, "Department is required"),
  severity: z.string().min(1, "Severity is required"),
  reporterName: z.string().min(1, "Reporter name is required"),
  attachments: z.any().optional(),
});

type FormData = z.infer<typeof formSchema>;

const departments = [
  "Engineering",
  "Manufacturing",
  "Sales",
  "Quality",
  "IT",
  "HR",
];

const severityLevels: { value: SeverityLevel; label: string }[] = [
  { value: "critical", label: "Critical" },
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
];

const IncidentReport = () => {
  const navigate = useNavigate();
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
    reset,
  } = useForm<FormData>({
    resolver: zodResolver(formSchema),
  });

  const department = watch("department");
  const severity = watch("severity");

  const onSubmit = async (data: FormData) => {
    setIsSubmitting(true);
    
    try {
      // Validate files if any
      if (selectedFiles.length > 0) {
        const validation = fileService.validateFiles(selectedFiles);
        if (!validation.valid) {
          validation.errors.forEach(error => toast.error(error));
          setIsSubmitting(false);
          return;
        }
      }

      // Prepare lesson data
      const lessonData = {
        commodity: data.commodity,
        part_number: data.partNumber || undefined,
        supplier: data.supplier || undefined,
        error_location: data.errorLocation,
        problem_description: data.problemDescription,
        missed_detection: data.missedDetection,
        provided_solution: data.providedSolution,
        department: data.department,
        severity: data.severity.toLowerCase() as SeverityLevel,
        reporter_name: data.reporterName,
      };

      // Submit to backend (with AI processing happening automatically)
      const createdLesson = await lessonService.createLessonWithFiles(
        lessonData,
        selectedFiles.length > 0 ? selectedFiles : undefined
      );

      // Redirect to AI processing page
      navigate(`/ai-processing/${createdLesson.id}`);
    } catch (error) {
      console.error("Error submitting report:", error);
      toast.error("Failed to submit report", {
        description: error instanceof Error ? error.message : "Please try again later.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);
      
      // Validate each file
      const validFiles: File[] = [];
      let hasErrors = false;

      newFiles.forEach(file => {
        const validation = fileService.validateFile(file);
        if (validation.valid) {
          validFiles.push(file);
        } else {
          toast.error(`${file.name}: ${validation.error}`);
          hasErrors = true;
        }
      });

      if (validFiles.length > 0) {
        setSelectedFiles(prev => {
          const combined = [...prev, ...validFiles];
          if (combined.length > 5) {
            toast.error("Maximum 5 files allowed");
            return combined.slice(0, 5);
          }
          return combined;
        });
      }
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="bg-card rounded-lg shadow-lg p-8 border border-border">
          <h1 className="text-3xl font-bold text-foreground mb-2">
            Incident Report Form
          </h1>
          <p className="text-muted-foreground mb-8">
            Fill out this form to report any incidents or issues
          </p>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <Label htmlFor="commodity" className="text-foreground">
                  Commodity <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="commodity"
                  {...register("commodity")}
                  className="mt-1.5"
                  placeholder="Enter commodity"
                />
                {errors.commodity && (
                  <p className="text-destructive text-sm mt-1">
                    {errors.commodity.message}
                  </p>
                )}
              </div>

              <div>
                <Label htmlFor="partNumber" className="text-foreground">
                  Part Number
                </Label>
                <Input
                  id="partNumber"
                  {...register("partNumber")}
                  className="mt-1.5"
                  placeholder="Enter part number (optional)"
                />
              </div>

              <div>
                <Label htmlFor="supplier" className="text-foreground">
                  Supplier
                </Label>
                <Input
                  id="supplier"
                  {...register("supplier")}
                  className="mt-1.5"
                  placeholder="Enter supplier (optional)"
                />
              </div>

              <div>
                <Label htmlFor="department" className="text-foreground">
                  Department <span className="text-destructive">*</span>
                </Label>
                <Select
                  onValueChange={(value) => setValue("department", value)}
                  value={department}
                >
                  <SelectTrigger className="mt-1.5">
                    <SelectValue placeholder="Select department" />
                  </SelectTrigger>
                  <SelectContent>
                    {departments.map((dept) => (
                      <SelectItem key={dept} value={dept}>
                        {dept}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.department && (
                  <p className="text-destructive text-sm mt-1">
                    {errors.department.message}
                  </p>
                )}
              </div>

              <div>
                <Label htmlFor="severity" className="text-foreground">
                  Severity <span className="text-destructive">*</span>
                </Label>
                <Select
                  onValueChange={(value) => setValue("severity", value)}
                  value={severity}
                >
                  <SelectTrigger className="mt-1.5">
                    <SelectValue placeholder="Select severity" />
                  </SelectTrigger>
                  <SelectContent>
                    {severityLevels.map((level) => (
                      <SelectItem key={level.value} value={level.value}>
                        {level.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.severity && (
                  <p className="text-destructive text-sm mt-1">
                    {errors.severity.message}
                  </p>
                )}
              </div>

              <div>
                <Label htmlFor="reporterName" className="text-foreground">
                  Reporter Name <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="reporterName"
                  {...register("reporterName")}
                  className="mt-1.5"
                  placeholder="Enter your name"
                />
                {errors.reporterName && (
                  <p className="text-destructive text-sm mt-1">
                    {errors.reporterName.message}
                  </p>
                )}
              </div>
            </div>

            <div>
              <Label htmlFor="problemDescription" className="text-foreground">
                Problem Description <span className="text-destructive">*</span>
              </Label>
              <Textarea
                id="problemDescription"
                {...register("problemDescription")}
                className="mt-1.5 min-h-[120px]"
                placeholder="Provide a detailed description of the problem"
              />
              {errors.problemDescription && (
                <p className="text-destructive text-sm mt-1">
                  {errors.problemDescription.message}
                </p>
              )}
            </div>

            <div>
              <Label htmlFor="errorLocation" className="text-foreground">
                Error Location <span className="text-destructive">*</span>
              </Label>
              <Input
                id="errorLocation"
                {...register("errorLocation")}
                className="mt-1.5"
                placeholder="Describe the error location"
              />
              {errors.errorLocation && (
                <p className="text-destructive text-sm mt-1">
                  {errors.errorLocation.message}
                </p>
              )}
            </div>

            <div>
              <Label htmlFor="missedDetection" className="text-foreground">
                Missed Detection <span className="text-destructive">*</span>
              </Label>
              <Input
                id="missedDetection"
                {...register("missedDetection")}
                className="mt-1.5"
                placeholder="Describe what was missed"
              />
              {errors.missedDetection && (
                <p className="text-destructive text-sm mt-1">
                  {errors.missedDetection.message}
                </p>
              )}
            </div>

            <div>
              <Label htmlFor="providedSolution" className="text-foreground">
                Provided Solution <span className="text-destructive">*</span>
              </Label>
              <Textarea
                id="providedSolution"
                {...register("providedSolution")}
                className="mt-1.5 min-h-[120px]"
                placeholder="Describe the solution or proposed fix"
              />
              {errors.providedSolution && (
                <p className="text-destructive text-sm mt-1">
                  {errors.providedSolution.message}
                </p>
              )}
            </div>

            <div>
              <Label htmlFor="attachments" className="text-foreground">
                Attachments (Images/PDFs)
              </Label>
              <div className="mt-1.5 space-y-3">
                <label
                  htmlFor="attachments"
                  className="flex items-center justify-center w-full px-4 py-8 border-2 border-dashed border-border rounded-lg cursor-pointer hover:border-primary transition-colors bg-muted/30"
                >
                  <div className="text-center">
                    <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-2" />
                    <p className="text-sm text-muted-foreground">
                      Click to upload images/PDFs or drag and drop
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Max 5 files, 10MB each (JPEG, PNG, PDF)
                    </p>
                    {selectedFiles.length > 0 && (
                      <p className="text-sm text-primary mt-2 font-medium">
                        {selectedFiles.length} file(s) selected
                      </p>
                    )}
                  </div>
                  <input
                    id="attachments"
                    type="file"
                    multiple
                    accept="image/jpeg,image/png,application/pdf"
                    className="hidden"
                    onChange={handleFileChange}
                  />
                </label>
                
                {selectedFiles.length > 0 && (
                  <div className="space-y-2">
                    {selectedFiles.map((file, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between p-3 bg-muted rounded-lg"
                      >
                        <div className="flex items-center space-x-2 flex-1 min-w-0">
                          <Upload className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                          <span className="text-sm text-foreground truncate">
                            {file.name}
                          </span>
                          <span className="text-xs text-muted-foreground flex-shrink-0">
                            ({(file.size / 1024).toFixed(1)} KB)
                          </span>
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removeFile(index)}
                          className="ml-2 flex-shrink-0"
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <Button type="submit" className="w-full" size="lg" disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Submitting Report...
                </>
              ) : (
                <>
                  <Send className="mr-2 h-5 w-5" />
                  Submit Incident Report
                </>
              )}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default IncidentReport;
