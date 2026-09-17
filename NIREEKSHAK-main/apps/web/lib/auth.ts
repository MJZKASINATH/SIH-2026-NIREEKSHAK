"use client";

export type UserRole =
  | "MP"
  | "APPROVING_AUTHORITY"
  | "CONTRACTOR"
  | "FIELD_OFFICER"
  | "AUDITOR"
  | "ADMIN";

export interface UserProfile {
  user_id?: number;
  username: string;
  role: UserRole;
  full_name: string;
  designation: string;
  official_id: string;
  email?: string;
  avatarColor?: string;
}

export interface DemoAccountInfo {
  username: string;
  name: string;
  role: UserRole;
  roleLabel: string;
  designation: string;
  officialId: string;
}

export const PRESET_DEMO_ACCOUNTS: DemoAccountInfo[] = [
  {
    username: "mp.demo",
    name: "Rahul Verma",
    role: "MP",
    roleLabel: "Member of Parliament",
    designation: "MP (Wayanad Constituency)",
    officialId: "MP-LS-2024-541"
  },
  {
    username: "authority.demo",
    name: "Dr. Rajesh Sharma, IAS",
    role: "APPROVING_AUTHORITY",
    roleLabel: "Approving Authority",
    designation: "District Magistrate & Collector",
    officialId: "IAS-KL-2015-4091"
  },
  {
    username: "contractor.demo",
    name: "Vikramaditya Rao",
    role: "CONTRACTOR",
    roleLabel: "Tender Contractor",
    designation: "Chief Project Engineer (Apex Infra)",
    officialId: "REG-KL-2018-9941"
  },
  {
    username: "field.demo",
    name: "Suresh Patel",
    role: "FIELD_OFFICER",
    roleLabel: "Field Officer",
    designation: "Assistant Executive Engineer (PWD)",
    officialId: "PWD-ENG-7721"
  },
  {
    username: "auditor.demo",
    name: "Anita Verma",
    role: "AUDITOR",
    roleLabel: "Vigilance Auditor",
    designation: "Senior Vigilance & Audit Officer",
    officialId: "CAG-AUD-9912"
  },
  {
    username: "admin.demo",
    name: "National Administrator",
    role: "ADMIN",
    roleLabel: "System Admin",
    designation: "Director General (Vigilance)",
    officialId: "SYS-ADMIN-001"
  }
];

const TOKEN_KEY = "nireekshak_token";
const USER_KEY = "nireekshak_user";

export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getAuthHeaders(): Record<string, string> {
  const token = getAuthToken();
  if (token) {
    return {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json"
    };
  }
  return {
    "Content-Type": "application/json"
  };
}

export function getStoredUser(): UserProfile {
  if (typeof window === "undefined") {
    return {
      username: "admin.demo",
      role: "ADMIN",
      full_name: "National Administrator",
      designation: "Director General",
      official_id: "SYS-ADMIN-001"
    };
  }

  const raw = localStorage.getItem(USER_KEY);
  if (raw) {
    try {
      return JSON.parse(raw);
    } catch {
      // Fall through
    }
  }

  // Default demo user
  return {
    username: "admin.demo",
    role: "ADMIN",
    full_name: "National Administrator",
    designation: "Director General (Vigilance)",
    official_id: "SYS-ADMIN-001"
  };
}

export function setStoredAuth(token: string, user: UserProfile) {
  if (typeof window !== "undefined") {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    window.dispatchEvent(new Event("nireekshak_auth_changed"));
  }
}

export function logout() {
  if (typeof window !== "undefined") {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    window.dispatchEvent(new Event("nireekshak_auth_changed"));
    window.location.href = "/login";
  }
}

export function checkAuthOrRedirect(router: any): boolean {
  if (typeof window !== "undefined") {
    const token = getAuthToken();
    if (!token) {
      router.push("/login");
      return false;
    }
    return true;
  }
  return false;
}

export const getStoredRole = getStoredUser;

// Permission helpers
export function canProposeProject(role: UserRole): boolean {
  return role === "MP" || role === "ADMIN";
}

export function canApproveProject(role: UserRole): boolean {
  return role === "APPROVING_AUTHORITY" || role === "ADMIN";
}

export function canAwardTender(role: UserRole): boolean {
  return role === "APPROVING_AUTHORITY" || role === "ADMIN";
}

export function canAddExpenditure(role: UserRole): boolean {
  return role === "APPROVING_AUTHORITY" || role === "CONTRACTOR" || role === "ADMIN";
}

export function canSubmitProgress(role: UserRole): boolean {
  return role === "CONTRACTOR" || role === "FIELD_OFFICER" || role === "ADMIN";
}

export function canVerifyCheckpoints(role: UserRole): boolean {
  return role === "FIELD_OFFICER" || role === "ADMIN";
}

export function canManageInvestigation(role: UserRole): boolean {
  return role === "AUDITOR" || role === "ADMIN";
}
