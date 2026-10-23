
import { NextRequest, NextResponse } from 'next/server'
import { cookies } from "next/headers";

export async function GET(req: NextRequest) {
    const _cookies = cookies();

    try {

        (await _cookies).delete('isAuthenticated');
        const response = {
            success: true,
        }
        return NextResponse.json(response, { status: 200 });

    }
    catch (err) {
        console.log('err: ', err)
        const data = {
            success: false,
        }
        return NextResponse.json({ data }, { status: 500 });
    }
}

