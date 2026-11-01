import { Badge } from "@/components/ui/badge";
import type { QuoteStatus, VendorStatus } from "../types";

interface VendorStatusBadgeProps {
  status: VendorStatus | string;
  className?: string;
}

export function VendorStatusBadge({ status, className }: VendorStatusBadgeProps) {
  switch (status) {
    case "booked":
      return <Badge className={`bg-emerald-600 text-white hover:bg-emerald-700 ${className || ""}`}>Booked</Badge>;
    case "shortlisted":
      return <Badge className={`bg-purple-600 text-white hover:bg-purple-700 ${className || ""}`}>Shortlisted</Badge>;
    case "quoted":
      return <Badge className={`bg-blue-600 text-white hover:bg-blue-700 ${className || ""}`}>Quoted</Badge>;
    case "contacted":
      return <Badge variant="outline" className={`text-amber-600 border-amber-300 ${className || ""}`}>Contacted</Badge>;
    case "declined":
      return (
        <Badge variant="muted" className={`text-destructive border-destructive/20 bg-destructive/10 ${className || ""}`}>
          Declined
        </Badge>
      );
    default:
      return <Badge variant="secondary" className={className}>Identified</Badge>;
  }
}

interface QuoteStatusBadgeProps {
  status: QuoteStatus | string;
  className?: string;
}

export function QuoteStatusBadge({ status, className }: QuoteStatusBadgeProps) {
  switch (status) {
    case "accepted":
      return <Badge className={`bg-emerald-600 text-white ${className || ""}`}>Accepted</Badge>;
    case "shortlisted":
      return <Badge className={`bg-purple-600 text-white ${className || ""}`}>Shortlisted</Badge>;
    case "rejected":
      return (
        <Badge variant="muted" className={`text-destructive border-destructive/20 bg-destructive/10 ${className || ""}`}>
          Rejected
        </Badge>
      );
    case "expired":
      return <Badge variant="outline" className={`text-muted-foreground ${className || ""}`}>Expired</Badge>;
    default:
      return <Badge variant="secondary" className={className}>Draft</Badge>;
  }
}

