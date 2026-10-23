import axios from "axios";
import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

export async function POST(req: Request): Promise<NextResponse> {
    console.log(req.headers.get('origin'));
    const cookieStore = await cookies();
    const userCookies = cookieStore.get("isAuthenticated")?.value || '';
  
    const { endpoint, destinationEnvLink } = await req.json();
    
    const API_URL = `${destinationEnvLink}${endpoint}`;
    try { 
        const rawResponse = await axios({
            method: 'GET',
            url: API_URL,
            headers: {
                'Authorization': `Bearer ${userCookies}`
            }
        });

        const { data, status } = await rawResponse;
    
        const response = {
            success: false,
            data: data.data
        };

        console.log(data)
        if(data && status == 200) {
            response.success = true
            return new NextResponse(JSON.stringify(response), { status });
        } else {
            return NextResponse.json(
                {
                    success: false,
                    data: {
                        error: 'Please check api',
                    }
                },
                { status: 404 }
            );
        };
    } catch (caught) {
        let error = "";
        return NextResponse.json({ data: error }, {status: 500});
    }
}
