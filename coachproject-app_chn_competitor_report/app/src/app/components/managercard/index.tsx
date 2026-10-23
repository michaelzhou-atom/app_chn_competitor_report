import Link from 'next/link';
import React from 'react'
  
interface ManagerCardProp {
    name: string,
    code: string,
    storeCount: string
}

const ManagerCard: React.FC<ManagerCardProp> = ({name, code, storeCount }) => {
    const getInitials = (name: string) => {
        return name
            .split(" ")
            .map(word => word[0].toUpperCase()) 
            .join("");
    }
    return (
        <Link href={`/managers/${code}`} className="h-28 p-4 bg-[#f8f9fb] rounded-lg flex items-center gap-3">
              <span className="w-[60px] h-[60px] bg-white rounded-full justify-center items-center flex text-[#221d3e] text-[28px] font-bold">
                {getInitials(name)}
              </span>
              <span className="w-auto relative">
                  <span className="text-[#221d3e] text-lg mb-1 block">{name}</span>
                  <span className="w-max px-2 pb-0.5 bg-[#3152ff]/5 rounded-2xl shadow-[0px_4px_4px_0px_rgba(0,0,0,0.02)] border border-[#3253ff]/20 justify-start items-center">
                      <span className="text-center text-[#3152ff] text-[10px]">Operating {storeCount} stores</span>
                  </span>
              </span>
        </Link>
    )
    
}

export default ManagerCard
