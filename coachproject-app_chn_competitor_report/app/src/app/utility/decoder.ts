export function decodeJWT(token: string) {
  if (!token) {
    throw new Error("Invalid token: Token is empty");
  }
  
  try {
    const base64Payload = token.split(".")[1]; 
    const payload = Buffer.from(base64Payload, "base64").toString();
    return JSON.parse(payload);
  } catch (error) {
    throw new Error("Invalid token: Failed to decode JWT");
  }
}
