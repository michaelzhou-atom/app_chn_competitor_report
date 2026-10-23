import React from 'react'

const FullScreenLoader = () => {
  return (
    <div className='bg-black bg-opacity-50 z-10 h-full w-full flex items-center justify-center fixed top-0 right-0 left-0'>
      <div className="text-center">
          <div 
              className="w-16 h-16 border-4 border-dashed 
              rounded-full animate-spin border-yellow-500 mx-auto"></div>
          <h2 className="text-white mt-4 text-lg">Loading...</h2>
          <p className="text-white">Please wait</p>
      </div>
    </div>
  )
}

export default FullScreenLoader;