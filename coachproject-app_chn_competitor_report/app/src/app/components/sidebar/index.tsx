import Link from 'next/link'
import React, { useState } from 'react'
import Icons from '../svgicons'
import { Store } from '@/app/managers/[managercode]/page';
import { usePathname } from 'next/navigation';

interface SideBarProp {
    storesList: Store[],
    storeData: (storeCode:string) => void,
    managerCode: string

}

const Sidebar:React.FC<SideBarProp> = ({storesList, storeData, managerCode}) => {
    const pathname = usePathname();
    const statusColor = {
        error: {
            background: '#FEF3F2',
            text: '#B42318',
            pointer: '#F04438'
        },
        success: {
            background: '#ECFDF3',
            text: '#027A48',
            pointer: '#12B76A'
        }
    };


    const [startIndex, setStartIndex] = useState(0);
    // const visibleStores = storesList.slice(startIndex, startIndex + 4);
    const visibleStores = storesList


    const scrollUp = () => {
        if (startIndex > 0) {
            setStartIndex(startIndex - 1);
        }
    };

    const scrollDown = () => {
        if (startIndex + 3 < storesList.length) {
            setStartIndex(startIndex + 1);
        }
    };

    const handleStoreData = (storeCode: string) => {
        storeData(storeCode)
    }

    const formatName = (str:string) => {
        return str
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }
    
    

    return (
        <div className="sidebar w-[334px] h-[537px] sticky top-0">
            <div className="managertitle">
                <div className="px-4 py-6 bg-gray-50 rounded-lg relative flex justify-between items-center"> 
                    <h4 className="text-[#221d3e] text-lg font-bold">Manager: {formatName(managerCode)}</h4>
                    <div className="text-[#3152ff] text-xs">
                        <Link href="/managers">Change</Link>
                    </div>
                </div>
            </div>
            <div className="storesholder bg-gray-50 rounded-lg p-4 mt-2 block relative">
                <div className="text-[#221d3e] text-base font-bold mb-4">List of stores</div>
                <div className="storeslist h-[400px] overflow-auto flex flex-col cursor-pointer" style={{scrollbarWidth: 'none'}}>
                    {visibleStores.map((store, index) => (
                        <div onClick={() => handleStoreData(store.store)} key={index} className="storeitem my-2 p-4 bg-white rounded-lg">
                            <div className="storestatus px-2 py-0.5 rounded-2xl items-center gap-1 inline-flex mb-2"
                                style={{ 
                                    background: store.status == 'Open' ? 
                                        statusColor.success.background : statusColor.error.background
                                }}>
                                <div className="w-1.5 h-1.5 rounded-full" 
                                    style={{ 
                                        background: store.status == 'Open'  ? 
                                            statusColor.success.pointer :  statusColor.error.pointer  }}/>
                                <div className="text-xs" style={{ 
                                        color: store.status == 'Open'  ? 
                                            statusColor.success.text : statusColor.error.text }}>
                                    {store.status.charAt(0).toUpperCase() + store.status.slice(1)}
                                </div>
                            </div>
                            <div className="storetitle mb-2">
                                <div className="text-[#221d3e] text-base font-bold">{store.store_name}</div>
                                <div className="text-[#475466] text-sm">{store.store}</div>
                            </div>
                            {/* <div className="storelocation flex items-center gap-1">
                                <Icons.MapMarker />
                                <div className="text-[#221d3e] text-xs">{store.location}</div>
                            </div> */}
                        </div>
                    ))}
                </div>

                <div className='sliderbtn flex flex-col gap-5 absolute -left-14 bottom-0 hidden'>
                    <button 
                        className={`${startIndex === 0 ? 'opacity-50 cursor-not-allowed' : ''}`}
                        onClick={scrollUp}
                        disabled={startIndex === 0}
                    >
                        <Icons.ChevronUp className="text-[#3152ff]" />
                
                    </button>
                    <button 
                        className={`${startIndex + 4 >= storesList.length ? 'opacity-50 cursor-not-allowed' : ''}`}
                        onClick={scrollDown}
                        disabled={startIndex + 3 >= storesList.length}
                    >
                        <Icons.ChevronDown className="text-[#3152ff]" />
                    </button>
                </div>
               

            </div>
        </div>
    );
}

export default Sidebar;
