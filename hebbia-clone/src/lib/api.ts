import { useAuth } from "@clerk/nextjs";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export function useBackendApi() {
  const { getToken } = useAuth();

  const callBackendApi = async (
    endpoint: string,
    method: string = "GET",
    data?: unknown
  ) => {
    try {
      const token = await getToken(); // Get the session token
      console.log("Clerk Token retrieved:", token); // Log the token

      if (!token) {
        throw new Error("No Clerk token found. User might not be authenticated.");
      }

      const headers: HeadersInit = {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      };

      const config: RequestInit = {
        method,
        headers,
        body: data ? JSON.stringify(data) : undefined,
      };

      console.log(`Making API call to: ${BACKEND_URL}${endpoint}`);
      const response = await fetch(`${BACKEND_URL}${endpoint}`, config);

      // Check if response is HTML (authentication page)
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("text/html")) {
        throw new Error("Backend requires authentication. Please check Vercel deployment protection settings.");
      }

      if (!response.ok) {
        let errorMessage;
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || `API call failed with status ${response.status}`;
        } catch {
          errorMessage = `API call failed with status ${response.status}`;
        }
        throw new Error(errorMessage);
      }

      return response.json();
    } catch (error) {
      console.error("API call error:", error);
      throw error;
    }
  };

  return { callBackendApi };
}
