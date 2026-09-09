import { useEffect, useState } from "react";

import { apiRequest } from "../api";


function useLiveCollection(path, token, mapItem) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    let active = true;
    let requestController = null;

    const load = async ({ silent = false } = {}) => {
      requestController?.abort();
      requestController = new AbortController();
      if (!silent) setLoading(true);
      try {
        const data = await apiRequest(path, { token, signal: requestController.signal });
        if (!active) return;
        setItems(data.items.map(mapItem));
        setError("");
      } catch (requestError) {
        if (!active || requestError.name === "AbortError") return;
        setError(requestError.message);
      } finally {
        if (active && !silent) setLoading(false);
      }
    };

    load();
    const refresh = () => load({ silent: true });
    const refreshWhenVisible = () => {
      if (document.visibilityState === "visible") refresh();
    };
    const interval = window.setInterval(refresh, 15000);
    window.addEventListener("focus", refresh);
    document.addEventListener("visibilitychange", refreshWhenVisible);

    return () => {
      active = false;
      requestController?.abort();
      window.clearInterval(interval);
      window.removeEventListener("focus", refresh);
      document.removeEventListener("visibilitychange", refreshWhenVisible);
    };
  }, [mapItem, path, revision, token]);

  return { items, loading, error, reload: () => setRevision((value) => value + 1) };
}


const mapProduct = (product) => ({
  id: product.product_id,
  name: product.name,
  category: product.category,
  price: Number(product.price),
  stock: Number(product.stock),
  reorder: Number(product.reorder_level),
  status: Number(product.stock) === 0
    ? "Hết hàng"
    : Number(product.stock) <= Number(product.reorder_level)
      ? "Sắp hết"
      : "Còn hàng",
});

const mapCustomer = (customer) => ({
  id: customer.customer_id,
  name: customer.name,
  contact: customer.contact_name || "—",
  phone: customer.phone || "—",
  tier: customer.tier || "Standard",
  status: customer.customer_status === "Active" ? "Hoạt động" : customer.customer_status,
});

const mapPromotion = (promotion) => ({
  id: promotion.promotion_id,
  title: promotion.title,
  description: promotion.description,
  tag: promotion.tag,
  customerTier: promotion.customer_tier || "Tất cả khách hàng",
  startDate: promotion.start_date,
  endDate: promotion.end_date,
  expires: `Đến ${new Intl.DateTimeFormat("vi-VN").format(new Date(`${promotion.end_date}T00:00:00`))}`,
  color: ["violet", "blue", "orange"].includes(promotion.color) ? promotion.color : "blue",
});


export function useCatalogProducts(token) {
  return useLiveCollection("/catalog/products", token, mapProduct);
}


export function useCatalogCustomers(token) {
  return useLiveCollection("/catalog/customers", token, mapCustomer);
}


export function usePromotions(token) {
  return useLiveCollection("/catalog/promotions", token, mapPromotion);
}
