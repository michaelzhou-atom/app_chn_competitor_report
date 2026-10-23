import axios from "axios";
import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
    const cookieStore = await cookies();
    const userCookies = cookieStore.get("isAuthenticated")?.value || '';
  
    const { endpoint, destinationEnvLink } = await req.json();
    
    const API_URL = `${destinationEnvLink}${endpoint}`;
    try {
        const rawResponse = await axios({
            method: 'GET',
            url: API_URL,
            headers: {
              "Content-Type": "application/json",
              "Accept": "application/json",
              "Authorization": `Bearer ${userCookies}`
            },
        });

        const { data, status } = await rawResponse;
    
        const response = {
            success: false,
            data: data.data.managers_list
        };

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
