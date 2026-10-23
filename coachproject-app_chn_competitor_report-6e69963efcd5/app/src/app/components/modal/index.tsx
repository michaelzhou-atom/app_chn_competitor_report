import React from 'react'
import Icons from '../svgicons';


interface ModalProp {
    title: string,
    message: string,
    type: 'success' | 'warning' | 'error' |  string,
    handleModalProcess?: (e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => void;
    handleModalDiscard?: (e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => void;
    handleModalClose?: (e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => void;
}

const Modal:React.FC<ModalProp> = ({title, message, type,handleModalProcess, handleModalDiscard, handleModalClose}) => {

  return (
    <div className="fixed top-0 left-0 w-screen h-screen z-30">
        <div className="backdrop fixed top-0 left-0 bg-black/25 w-screen h-screen"></div>
        <div className="w-[400px] p-6 bg-white rounded-xl -translate-y-2/4 -translate-x-2/4 left-1/2 top-1/2 absolute">
            {handleModalClose && <>
                <button type='button' className='closemodal cursor-pointer absolute right-2.5 top-2.5' 
                onClick={(e) =>  handleModalClose(e as React.MouseEvent<HTMLButtonElement,MouseEvent>)}>
                    <Icons.CloseModal />
                </button>
            </>}
            <div className="flex-col justify-start items-center flex mb-8">
                <div className='modalicon mb-5'>
                    {type == 'warning' ? <Icons.SavingIcon/> : 
                    type == 'success' ?  <Icons.SuccessIcon /> : 
                    type == 'error' ?  <Icons.ErrorModalIcon /> : <Icons.SavingIcon/> }
                </div>
                <div className="text-center text-[#0f1728] text-lg font-bold mb-2">{title}</div>
                <div className="text-center text-[#475466] text-sm font-normal">{message}</div>
            </div>
            <div className="items-center gap-3 flex">
                {type == 'warning' ? (
                    <>
                        {handleModalDiscard &&  <button type='button' 
                                    className='h-11 bg-white rounded-lg text-[#344053] 
                                    text-base font-bold rounded-lg border border-[#cfd4dc] w-full'  onClick={(e) => 
                                        handleModalDiscard(e as React.MouseEvent<HTMLButtonElement,MouseEvent>)}>
                                            Discard
                                </button>
                        }
                        {handleModalProcess && 
                            <button type='button' 
                                className='h-11  bg-[#221d3e] rounded-lg text-white 
                                text-base font-bold rounded-lg w-full' 
                                onClick={(e) => 
                                    handleModalProcess(e as React.MouseEvent<HTMLButtonElement, MouseEvent>)}>
                                        Save changes
                            </button>
                        }
                    </>
                ): (
                    <>
                        {handleModalClose && 
                            <button type='button' 
                                className='h-11  bg-[#221d3e] rounded-lg text-white 
                                text-base font-bold rounded-lg w-full' 
                                onClick={(e) => 
                                    handleModalClose(e as React.MouseEvent<HTMLButtonElement, MouseEvent>)}>
                                        OK
                            </button>
                        }
                    </>
                )}
                
            </div>
        </div>
    </div>
  )
}

export default Modal