import axios from 'axios';
import https from 'https';
import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';



export async function POST(req: Request): Promise<NextResponse> {
  const cookieStore = await cookies();
  const userCookies = cookieStore.get("isAuthenticated")?.value || '';
  try {
    const formData = await req.formData();


    const httpsAgent = new https.Agent({
      rejectUnauthorized: false,
    });

    let destinationEnvLink = formData.get('destinationEnvLink') as string;
    let endpoint = formData.get('endpoint') as string;
    let userFile = formData.get('user_file') as File;
    const API_URL = `${destinationEnvLink}${endpoint}`;

    console.log('API_URL================>', API_URL);


    const uploadFormData = new FormData();
    uploadFormData.append('file', userFile);



    const rawResponse = await axios({
      method: 'POST',
      url: API_URL,
      data: uploadFormData,
      headers: {
        'Content-Type': 'multipart/form-data',
        'Authorization': `Bearer ${userCookies}`
      },
      httpsAgent,
    });

    console.log("rawResponse", rawResponse);

    const { data, status } = await rawResponse;

    const response = {
      success: false,
      data,
      status
    };

    if (data && status == 200) {
      response.success = true
      return new NextResponse(JSON.stringify(response));
    } else {
      // Pass through the actual error from backend
      return NextResponse.json(
        {
          success: false,
          data: data || { error: 'Upload failed' }
        },
        { status: status || 400 }
      );
    }

  } catch (error: unknown) {
    console.error('Upload error:', error);
    
    if (axios.isAxiosError(error)) {
      // Extract the actual error response from Flask backend
      const backendError = error.response?.data;
      const statusCode = error.response?.status || 500;
      
      // Handle specific error types
      if (String(backendError?.error).includes("UNIQUE constraint")) {
        return NextResponse.json(
          { 
            error: 'Sheet contains duplicates: ' + JSON.stringify(backendError?.messages),
            success: false 
          },
          { status: statusCode }
        );
      }
      
      // Pass through other backend errors (like validation errors)
      if (backendError?.error || backendError?.message) {
        // Concatenate error and message for better user feedback
        let fullErrorMessage = backendError.error || '';
        if (backendError.message && backendError.message !== backendError.error) {
          fullErrorMessage += (fullErrorMessage ? ': ' : '') + backendError.message;
        }
        
        return NextResponse.json(
          { 
            error: fullErrorMessage || backendError.message,
            message: backendError.message,
            success: false 
          },
          { status: statusCode }
        );
      }
    }
    
    // Fallback for unexpected errors
    return NextResponse.json(
      { error: 'Internal Server Error', success: false },
      { status: 500 }
    );
  }
}
