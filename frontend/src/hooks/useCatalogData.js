// SPDX-License-Identifier: MIT
import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { apiRequest } from "../api";


function useLiveCollection(path, token, mapItem) {
  const query = useQuery({
    queryKey: ["live-collection", path, token],
    queryFn: ({ signal }) => apiRequest(path, { token, signal }),
    enabled: Boolean(token),
    staleTime: 0,
    refetchInterval: 15_000,
    refetchIntervalInBackground: false,
    refetchOnWindowFocus: "always",
  });
  const items = useMemo(
    () => (query.data?.items || []).map(mapItem),
    [query.data?.items, mapItem],
  );
  return {
    items,
    total: Number(query.data?.total || 0),
    page: Number(query.data?.page || 1),
    pageSize: Number(query.data?.page_size || query.data?.items?.length || 0),
    totalPages: Number(query.data?.total_pages || 1),
    loading: query.isPending,
    error: query.error?.message || "",
    reload: query.refetch,
  };
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
  discountType: promotion.discount_type,
  discountValue: Number(promotion.discount_value),
  minOrderValue: Number(promotion.min_order_value),
  maxUses: promotion.max_uses == null ? null : Number(promotion.max_uses),
  usedCount: Number(promotion.used_count),
  appliedProductId: promotion.applied_product_id || null,
  appliedCategory: promotion.applied_category || null,
  startDate: promotion.start_date,
  endDate: promotion.end_date,
  expires: `Đến ${new Intl.DateTimeFormat("vi-VN").format(new Date(`${promotion.end_date}T00:00:00`))}`,
  color: ["violet", "blue", "orange"].includes(promotion.color) ? promotion.color : "blue",
});


export function useCatalogProducts(token, { q = "", page = 1, pageSize = 24 } = {}) {
  const params = new URLSearchParams({
    q: q.trim(),
    page: String(page),
    page_size: String(pageSize),
  });
  return useLiveCollection(`/catalog/products?${params}`, token, mapProduct);
}


export function useCatalogCustomers(token) {
  return useLiveCollection("/catalog/customers", token, mapCustomer);
}


export function usePromotions(token) {
  return useLiveCollection("/catalog/promotions", token, mapPromotion);
}
