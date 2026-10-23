import Image from 'next/image';
import React from 'react'

const EmptyPane = () => {
  return (
    <div className="w-auto bg-gray-50 rounded-lg px-4 grow pb-4">
        <div className="flex justify-center items-center h-full">
            <div className="flex-col justify-center items-center gap-5 flex">
                <div className="w-[172px] h-32 relative">
                  <Image src={'/images/emptycomppane.svg'} width={172} height={128} alt='' />
                </div>
                <h4 className='text-center text-[#0f1728] text-lg font-bold'>No data to show</h4>
                <p className='text-center text-[#475466] text-sm'>Please select any store to see the list of its <br/>competitors.</p>
            </div>
        </div>
    </div>
  )
}

export default EmptyPane;