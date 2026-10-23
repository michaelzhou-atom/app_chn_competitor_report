import React from 'react'

interface AlertMsg {
    type: 'info' | 'warning' | 'danger' | 'success',
    heading?: string,
    title?: string
    note?: string,
}

const AlertMsg: React.FC<AlertMsg> = ({type,heading,title,note}) => {
  return (
    <div 
        className={`border-l-4 p-4 
            ${
                type == 'info' ?  'bg-sky-100 border-sky-400 text-slate-700' : 
                type == 'warning' ?  'bg-orange-100 border-orange-500 text-orange-700' : 
                type == 'danger' ?  'bg-red-100 border-red-500 text-red-700' : 
                type == 'success' ?  'bg-green-100 border-green-500 text-green-700' : 
                'bg-gray-100 border-gray-500 text-gray-700'
            }`} role="alert">
        {heading && 
            <p className="font-bold text-base">{heading}</p>
        }
        {note && 
            <p className='text-sm'>{title} status : {note}</p>
        }
    </div>
  )
}

export default AlertMsg;