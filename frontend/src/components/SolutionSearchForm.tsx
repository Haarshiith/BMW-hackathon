import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Search, Lightbulb, User, Building, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import type { SolutionSearchFormData } from "@/types/solutionSearch";

const solutionSearchSchema = z.object({
  problem_description: z
    .string()
    .min(10, "Problem description must be at least 10 characters")
    .max(1000, "Problem description must be less than 1000 characters"),
  department: z.string().min(1, "Please select a department"),
  severity: z.enum(["low", "medium", "high", "critical"], {
    required_error: "Please select a severity level",
  }),
  reporter_name: z
    .string()
    .min(2, "Reporter name must be at least 2 characters")
    .max(100, "Reporter name must be less than 100 characters"),
});

interface SolutionSearchFormProps {
  onSubmit: (data: SolutionSearchFormData) => void;
  isLoading?: boolean;
}

const departments = [
  "Engineering",
  "Manufacturing",
  "Quality",
  "IT",
  "HR",
  "Sales",
];

const severityLevels = [
  { value: "low", label: "Low", color: "bg-green-100 text-green-800" },
  { value: "medium", label: "Medium", color: "bg-yellow-100 text-yellow-800" },
  { value: "high", label: "High", color: "bg-orange-100 text-orange-800" },
  { value: "critical", label: "Critical", color: "bg-red-100 text-red-800" },
];

export const SolutionSearchForm = ({
  onSubmit,
  isLoading = false,
}: SolutionSearchFormProps) => {
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isValid },
  } = useForm<SolutionSearchFormData>({
    resolver: zodResolver(solutionSearchSchema),
    defaultValues: {
      problem_description: "",
      department: "",
      severity: "medium",
      reporter_name: "",
    },
  });

  const problemDescription = watch("problem_description");

  const handleFormSubmit = (data: SolutionSearchFormData) => {
    onSubmit(data);
  };

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-2xl">
          <Search className="h-6 w-6 text-primary" />
          Find Solution for Your Problem
        </CardTitle>
        <p className="text-muted-foreground">
          Describe your problem and we'll search across our database, knowledge
          base, and the web to find potential solutions.
        </p>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
          {/* Problem Description */}
          <div className="space-y-2">
            <Label
              htmlFor="problem_description"
              className="flex items-center gap-2"
            >
              <AlertTriangle className="h-4 w-4" />
              Problem Description *
            </Label>
            <Textarea
              id="problem_description"
              placeholder="Describe the problem you're facing in detail. Include what happened, when it occurred, and any relevant context..."
              className="min-h-[120px] resize-none"
              {...register("problem_description")}
            />
            {errors.problem_description && (
              <p className="text-sm text-destructive">
                {errors.problem_description.message}
              </p>
            )}
            <p className="text-xs text-muted-foreground">
              {problemDescription?.length || 0}/1000 characters
            </p>
          </div>

          {/* Department and Severity */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="department" className="flex items-center gap-2">
                <Building className="h-4 w-4" />
                Department *
              </Label>
              <Select onValueChange={(value) => setValue("department", value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select department" />
                </SelectTrigger>
                <SelectContent>
                  {departments.map((dept) => (
                    <SelectItem key={dept} value={dept}>
                      {dept.charAt(0).toUpperCase() + dept.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.department && (
                <p className="text-sm text-destructive">
                  {errors.department.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="severity" className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                Severity Level *
              </Label>
              <Select
                onValueChange={(value) => setValue("severity", value as any)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select severity" />
                </SelectTrigger>
                <SelectContent>
                  {severityLevels.map((level) => (
                    <SelectItem key={level.value} value={level.value}>
                      <div className="flex items-center gap-2">
                        <Badge className={level.color}>{level.label}</Badge>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.severity && (
                <p className="text-sm text-destructive">
                  {errors.severity.message}
                </p>
              )}
            </div>
          </div>

          {/* Reporter Name */}
          <div className="space-y-2">
            <Label htmlFor="reporter_name" className="flex items-center gap-2">
              <User className="h-4 w-4" />
              Your Name *
            </Label>
            <Input
              id="reporter_name"
              placeholder="Enter your name"
              {...register("reporter_name")}
            />
            {errors.reporter_name && (
              <p className="text-sm text-destructive">
                {errors.reporter_name.message}
              </p>
            )}
          </div>

          {/* Info Alert */}
          <Alert>
            <Lightbulb className="h-4 w-4" />
            <AlertDescription>
              Our system will search across three sources: our internal incident
              database, our knowledge base (Excel data), and the web to find the
              most relevant solutions for your problem.
            </AlertDescription>
          </Alert>

          {/* Submit Button */}
          <Button
            type="submit"
            className="w-full"
            disabled={!isValid || isLoading}
          >
            {isLoading ? (
              <>
                <Search className="h-4 w-4 mr-2 animate-spin" />
                Searching for Solutions...
              </>
            ) : (
              <>
                <Search className="h-4 w-4 mr-2" />
                Find Solutions
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};
