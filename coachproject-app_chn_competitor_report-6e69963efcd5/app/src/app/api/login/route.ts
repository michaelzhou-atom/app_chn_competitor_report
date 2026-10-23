import axios from 'axios';
import https from 'https';
import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const { username, password, destinationUrl } = await request.json();
    // QA: competitorapp-mlc-qa.global.coach.com
 
    // prod: competitorapp-mlc.global.coach.com
 
    const apiUrl = `${destinationUrl}/auth/login`;

    const httpsAgent = new https.Agent({
      rejectUnauthorized: false,
    });

    const body = {
      username,
      password,
    }

    const rawResponse = await axios(apiUrl, {
      method: 'POST',
      data: body,
      httpsAgent,
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
      }
    })
    const { data, status } = rawResponse;
    
    const response = {
      success: true,
      data,
    };
    
    console.log(data)
    if (status === 200) {
      const headers = new Headers();
      
      headers.append(
        'Set-Cookie',
        `isAuthenticated=${response.data.token}; Path=/;`
      );

      return new NextResponse(JSON.stringify(response), {
        status,
        headers,
      });
    } else {
      return NextResponse.json(
        {
          success: false,
          data: {
            error: 'Please check your Username and Password',
          },
        },
        { status: 404 }
      );
    }
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error("Axios Error Status:", error.response?.status);
      console.error("Axios Error Data:", error.response?.data);
      return NextResponse.json(
        { error: error.response?.data || "External API Error" },
        { status: error.response?.status || 500 }
      );
    }
  
    console.error("Unexpected Error:", error);
    return NextResponse.json(
      { error: "Internal Server Error" },
      { status: 500 }
    );
  }
}
