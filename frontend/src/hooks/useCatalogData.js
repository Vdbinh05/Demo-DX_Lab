// SPDX-License-Identifier: MIT
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
  return {
    items: (query.data?.items || []).map(mapItem),
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
