import { Link, useLocation } from "react-router-dom";
import bmwLogo from "@/assets/bmw_logo.svg";
import thwsLogo from "@/assets/thws_logo.png";

const Navigation = () => {
  const location = useLocation();

  return (
    <nav className="bg-card border-b border-border sticky top-0 z-50 shadow-sm">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <img src={bmwLogo} alt="BMW" className="h-12 w-auto" />
            <div className="h-10 w-px bg-border" />
            <img src={thwsLogo} alt="THWS" className="h-10 w-auto" />
          </div>

          <h1 className="text-xl font-semibold text-foreground">
            BMW Incident Reporting System
          </h1>

          <div className="flex gap-2">
            <Link
              to="/"
              className={`px-6 py-2.5 rounded-md font-medium transition-colors ${
                location.pathname === "/"
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
              }`}
            >
              Incident Report
            </Link>
            <Link
              to="/solution-search"
              className={`px-6 py-2.5 rounded-md font-medium transition-colors ${
                location.pathname === "/solution-search"
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
              }`}
            >
              Find Solutions
            </Link>
            <Link
              to="/summary"
              className={`px-6 py-2.5 rounded-md font-medium transition-colors ${
                location.pathname === "/summary"
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
              }`}
            >
              Department Summary
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
