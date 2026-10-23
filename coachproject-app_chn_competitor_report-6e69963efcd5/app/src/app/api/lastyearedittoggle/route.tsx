import axios from 'axios';
import https from 'https';
import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  const cookieStore = await cookies();
  const userCookies = cookieStore.get("isAuthenticated")?.value || '';
  try {

    const { endpoint, destinationEnvLink } = await request.json();
    
    const API_URL = `${destinationEnvLink}${endpoint}`;
    
    const httpsAgent = new https.Agent({
      rejectUnauthorized: false,
    });

    const response = await axios({
      method: 'POST',
      url: API_URL,
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": `Bearer ${userCookies}`
      },
      httpsAgent
  });
    const { data, status } = response;
    console.log('API Response:', response);

    if (status === 200) {
      return NextResponse.json(
        { success: true, data },
        { status: 200 }
      );
    } else {
      console.error('Non-200 status received:', status);
      return NextResponse.json(
        {
          success: false,
          data: { error: 'API did not return a successful status' },
        },
        { status: status || 502 }
      );
    }
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error('Axios Error:', {
        message: error.message,
        status: error.response?.status,
        data: error.response?.data,
      });
    } else {
      console.error('Unexpected Error:', error);
    }

    return NextResponse.json(
      {
        success: false,
        error: 'Internal Server Error',
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 500 }
    );
  }
}
