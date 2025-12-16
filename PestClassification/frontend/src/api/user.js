import api from "./axios";

export function deleteUser(id) {
  return api.delete(`/admin/users/${id}`);
}

export function getAllUsers() {
  return api.get("/admin/users");
}
