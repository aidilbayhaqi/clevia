import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { publicApi } from "../api/publicApi";
import type { Clinic, Service, Staff } from "../types";

type PublicData = {
  clinic: Clinic | null;
  services: Service[];
  staff: Staff[];
  loading: boolean;
  error: string;
};

const PublicDataContext = createContext<PublicData | null>(null);

export function PublicDataProvider({ children }: { children: ReactNode }) {
  const [clinic, setClinic] = useState<Clinic | null>(null);
  const [services, setServices] = useState<Service[]>([]);
  const [staff, setStaff] = useState<Staff[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([publicApi.clinic(), publicApi.services(), publicApi.staff()])
      .then(([clinicData, serviceData, staffData]) => {
        setClinic(clinicData);
        setServices(serviceData);
        setStaff(staffData);
      })
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "Gagal memuat data klinik.");
      })
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo(() => ({ clinic, services, staff, loading, error }), [clinic, services, staff, loading, error]);

  return <PublicDataContext.Provider value={value}>{children}</PublicDataContext.Provider>;
}

export function usePublicData(): PublicData {
  const context = useContext(PublicDataContext);
  if (!context) throw new Error("usePublicData must be used inside PublicDataProvider");
  return context;
}
