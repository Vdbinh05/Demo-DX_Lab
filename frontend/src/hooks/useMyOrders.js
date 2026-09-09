import { useEffect, useState } from "react";

import { apiRequest } from "../api";


export function useMyOrders(token) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    let active = true;
    const controller = new AbortController();

    apiRequest("/orders/my-orders", { token, signal: controller.signal })
      .then((response) => {
        if (!active) return;
        setData(response);
        setError("");
      })
      .catch((requestError) => {
        if (!active || requestError.name === "AbortError") return;
        setError(requestError.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
      controller.abort();
    };
  }, [revision, token]);

  return { data, loading, error, reload: () => setRevision((value) => value + 1) };
}
