import { useEffect, useState } from "react";

export function useAsync<T>(loader: () => Promise<T>, dependencies: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    loader()
      .then((result) => { if (active) setData(result); })
      .catch((reason: unknown) => {
        if (active) setError(reason instanceof Error ? reason.message : "Terjadi kesalahan.");
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, dependencies);

  return { data, loading, error, setData };
}
