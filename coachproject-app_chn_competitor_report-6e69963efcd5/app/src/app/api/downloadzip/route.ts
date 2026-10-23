import axios from 'axios';
import https from 'https';
import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  const cookieStore = await cookies();
  const userCookies = cookieStore.get("isAuthenticated")?.value || '';

  try {
    const { endpoint, destinationEnvLink } = await request.json();
    
    const API_URL = `${destinationEnvLink}${endpoint}&token=${userCookies}`;
    
    const httpsAgent = new https.Agent({
      rejectUnauthorized: false,
    });

    const response = await axios({
      method: 'GET',
      url: API_URL,
      responseType: 'stream', 
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/zip", 
      },
      httpsAgent
    });

    const stream = new ReadableStream({
      async start(controller) {
        response.data.on('data', (chunk: any) => controller.enqueue(chunk));
        response.data.on('end', () => controller.close());
        response.data.on('error', (err: any) => controller.error(err));
      }
    });

    return new Response(stream, {
      status: response.status,
      headers: {
        "Content-Disposition": `attachment; filename="download.zip"`,
        "Content-Type": "application/zip",
      },
    });

  } catch (error: any) {
    console.error("Download API Error:", error.message);
    
    // Pass through the actual error from backend
    if (error.response) {
      const status = error.response.status;
      let errorData: any = { error: 'Unknown error', message: 'An error occurred' };
      
      try {
        // For stream responses, we need to read the stream to get the error
        if (error.response.data && typeof error.response.data.on === 'function') {
          // It's a stream - collect chunks and parse
          const chunks: Buffer[] = [];
          await new Promise<void>((resolve, reject) => {
            error.response.data.on('data', (chunk: Buffer) => chunks.push(chunk));
            error.response.data.on('end', () => resolve());
            error.response.data.on('error', (err: Error) => reject(err));
          });
          const text = Buffer.concat(chunks).toString('utf-8');
          errorData = JSON.parse(text);
        } else if (Buffer.isBuffer(error.response.data)) {
          // It's a buffer
          errorData = JSON.parse(error.response.data.toString());
        } else if (typeof error.response.data === 'string') {
          // It's a string
          errorData = JSON.parse(error.response.data);
        } else if (typeof error.response.data === 'object') {
          // It's already an object
          errorData = error.response.data;
        }
      } catch (parseError) {
        console.error("Error parsing response:", parseError);
        errorData = { error: 'Request failed', message: `Server returned status ${status}` };
      }
      
      console.error("Backend error:", errorData);
      
      return NextResponse.json(
        { success: false, ...errorData },
        { status: status }
      );
    }
    
    return NextResponse.json(
      { success: false, error: "Internal Server Error", message: error.message },
      { status: 500 }
    );
  }
}
