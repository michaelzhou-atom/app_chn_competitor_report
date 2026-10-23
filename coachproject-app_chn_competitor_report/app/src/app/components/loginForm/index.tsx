'use client'
import React, { useState } from "react";
import { sha1 } from "js-sha1"; 
import { useRouter } from 'next/navigation'
import Icons from "../svgicons/index";
import Image from "next/image";
import { useAppConfigContext } from "@/app/appcontext/appConfig";
import AlertMsg from "../alertmsg";

export default function LoginForm() {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false);
  const [loginState, setLoginState] = useState({
    username: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [status, setStatus] = useState(false)

  const {destinationUrl, envVal, windowLocation} = useAppConfigContext();
  
  const encryptPassword = (pass: string) => {
    return sha1(pass);
  }

  const handleSubmit = async () => {
    const { username, password } = loginState;
    if (username && password) {
      const url = '/api/login';
      setIsLoading(true);

      const body = {
        username,
        password: password,
        destinationUrl
      }

      try {
        let data = await fetch(url, {
          method: 'POST',
          body: JSON.stringify(body),
        })
        let response = await data.json()
        if (response && response.success) {
          sessionStorage.setItem("token", response.data.token);
          const decodedToken = JSON.parse(atob(response.data.token.split(".")[1]));

          if (decodedToken.user === "admin") {
            router.push("/list-uploader");
          } else {
            router.push("/managers");
          }
        } else {
            setStatus(true);
            setTimeout(() => setStatus(false),3000)
        }
      }
      catch (ex) {
        setStatus(true);
        setTimeout(() => setStatus(false),3000)
      } finally {
        setIsLoading(false);
      }

    }
  }

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setLoginState((prevState) => ({
      ...prevState,
      [name]: value
    }))
  }

  const handleShowPassword = () => {
    setShowPassword(prev => !prev)
  }
  return (
    <div className="h-screen flex flex-col items-center justify-center lg:p-10">
      <div className="formholder bg-[#FAFAFA] px-14 py-8 rounded-xl">
        {/* <Image
          src="/images/logo.svg"
          alt="app logo"
          width={80}
          height={71} 
          className="mx-auto"
        /> */}
        <h2 className="text-2xl text-center">Compitetor Report</h2>
        <div className="logintext mt-4 text-center">
          <h3 className="barlow-semibold text-3xl text-[#101828] mb-1">Log in to your account</h3>
          <p className="text-base text-[#475467]">Please enter your details.</p>
        </div>
        <div className="mt-10 w-[452px]" onKeyDown={(e) => e.key === "Enter" && handleSubmit()}>
          <div>
            <label htmlFor="" className="text-[#221D3E] text-base mb-1 block">Username</label>
            <div className="relative w-full">
              <input type="text" required 
                name="username" 
                value={loginState.username} 
                onChange={e => handleInputChange(e)} 
                className="text-[#424242] text-base border rounded-lg 
                border-[--D0D5DD] h-11 py-2.5 px-3.5 w-full focus:outline-none" />
              <span className="absolute right-4 top-1/2 transform -translate-y-1/2">
                <Icons.UsernameIcon />
              </span>
            </div>
          </div>
          <div className="mt-5">
            <label htmlFor="" className="text-[#221D3E] text-base mb-1 block">Password</label>
            <div className="relative w-full">
              <input type={showPassword ? 'text' : 'password'} required
                name="password" 
                value={loginState.password} 
                onChange={e => handleInputChange(e)} 
                className="text-[#424242] text-base border rounded-lg 
                border-[--D0D5DD] h-11 py-2.5 px-3.5 w-full focus:outline-none" />
              <span className="absolute right-4 top-1/2 transform -translate-y-1/2 cursor-pointer"
                onClick={handleShowPassword}>
                {showPassword ?
                  <Icons.HidePassword /> : <Icons.ShowPassword />
                }
              </span>
            </div>
          </div>
          {/* <div className="flex justify-between mt-3.5">
            <div className="flex items-center">
              <input type="checkbox" id="login" name="login" className="w-[16px] h-[16px]  cursor-pointer" />
              <label htmlFor="login" className="text-sm text-[#221D3E] ms-2  cursor-pointer">Keep me logged in</label>
            </div>
            <div>
              <a className="text-sm text-[#1C1C1C] font-medium underline">Forgot Password?</a>
            </div>
          </div> */}
          <div className="mt-8">
            <button
              className={`text-base rounded-md w-full p-2.5 font-bold bg-[#221D3E] 
              text-white border border-0
              ${isLoading || loginState.username == '' || loginState.password == '' ? 'cursor-not-allowed' : ''}`}
              onClick={handleSubmit}
              disabled={isLoading || loginState.username == '' || loginState.password == ''}
            >
              {isLoading ? 'Loading...' : 'Login'}
            </button>
          </div>
          {status && 
            <div className="mt-8">
              <AlertMsg type={'danger'} note={'Login failed, invalid username or password'} />
            </div>
          }
        </div>
      </div>
    </div>
  )
}
