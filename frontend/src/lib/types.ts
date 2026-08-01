export interface PiiFinding {
  type: string;
  severity: "critical" | "warning" | "info";
  field: string;
  message: string;
  piiType?: string;
}

export interface PiiScan {
  passed: boolean;
  score: number;
  findings: PiiFinding[];
  redactedPreview: string;
  timestamp: string;
  summary: {
    criticalCount: number;
    warningCount: number;
    infoCount: number;
    totalFindings: number;
  };
}

export interface PipelineStep {
  agent: string;
  status: string;
  [key: string]: unknown;
}

export interface FormPreviewResult {
  status: string;
  formData: Record<string, unknown>;
  confidence: Record<string, number>;
  requiresReview: boolean;
  piiScan: PiiScan;
  pipelineSteps: PipelineStep[];
  redactedPreview: string;
}

export interface RoiResult {
  physicianCount: number;
  province: string;
  formsAutomated: string[];
  useAiScribe: boolean;
  hoursSavedPerYear: number;
  hoursSavedPerPhysician: number;
  fteRecovered: number;
  costSavingsPerYear: number;
  aiScribeBonusHours: number;
  formAutomationHours: number;
  patientVisitsRecovered: number;
  formBreakdown: Record<string, {
    formName: string;
    hoursPerPhysicianPerYear: number;
    totalHoursSaved: number;
    automationRate: number;
  }>;
  summary: {
    headline: string;
    source: string;
  };
}

export interface ComplianceDashboard {
  auditLogs: AuditLogEntry[];
  submissionStats: {
    total: number;
    passed: number;
    blocked: number;
    passRate: number;
  };
  compliancePosture: {
    encryptionAtRest: boolean;
    encryptionInTransit: boolean;
    piiRedactionBeforeLlm: boolean;
    auditTrailEnabled: boolean;
    minimumNecessaryEnforced: boolean;
    retentionPolicyDays: number;
  };
}

export interface AuditLogEntry {
  id: number;
  userId: string;
  action: string;
  piiFields: string[];
  endpoint: string;
  patientId: string | null;
  ipAddress: string;
  timestamp: string;
}
