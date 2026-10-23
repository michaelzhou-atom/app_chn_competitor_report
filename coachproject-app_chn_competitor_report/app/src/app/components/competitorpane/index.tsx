import Image from 'next/image'
import React, { useEffect, useState } from 'react'
import Icons from '../svgicons'
import { salesData, salesDataRes } from '@/app/managers/[managercode]/page';
import EmptyPane from './emptypane';
import axios from 'axios';
import Modal from '../modal';
import FullScreenLoader from '../fullscreenloader';

type ViewStyle = 'grid' | 'list';

interface CompetitorPaneProps {
    salesData: salesDataRes,
    refreshAllData: () => void,
    destinationUrl: string
}

type ModalAccessType = {
    show: boolean,
    title: string,
    message: string,
    type: string
}

const resetModal:ModalAccessType = {
    show: false,
    title:'',
    message:'',
    type:''
}

const CompetitorPane:React.FC<CompetitorPaneProps> = ({salesData, refreshAllData, destinationUrl}) => {
    const [selectedView, setSelectedView] = useState('list' as ViewStyle);
    const [competitorSalesData, setCompetitorSalesData] = useState<salesDataRes>(salesData);
    const [modifiedSalesData, setModifiedSalesData] = useState<salesDataRes>(salesData);
    const [showModal, setShowModal] = useState(resetModal);
    const [isLoading, setIsLoading] = useState(false);
    useEffect(() => {
        if (salesData) {
            setCompetitorSalesData({ ...salesData }); 
            setModifiedSalesData({ ...salesData });
        }
    }, [salesData]);
    

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
    }
    const status = true;

    const isNegative = (num:number) => {
        return num < 0;
    }

    if(salesData?.sales_data?.length == 0 ) {
        return <EmptyPane />
    }

    const lastYearEditable = salesData?.is_last_year_data_editable;

    const handleDatachange = (index: number, field: keyof salesData, value: number | string) => {
        setModifiedSalesData((prev: salesDataRes) => {
            const updatedSalesData = prev?.sales_data?.map((item, i) =>{

                // Calculate growth rate on sales data change
                let growth_rate = item.growth_rate
                let sales = item.sales
                let ly_sales = item.ly_sales
                if(field=='sales'){
                    sales = Number(value)
                }
                else if(field=='ly_sales'){
                    ly_sales = Number(value)
                }

                if(!Number.isNaN(sales) && !Number.isNaN(ly_sales)){
                    growth_rate = (sales - ly_sales) / ly_sales * 100
                    console.log("growth_rate", field, sales, ly_sales, sales - ly_sales);
                    
                }

                
                return i === index ? { ...item, [field]: value, growth_rate } : item
            }
            );
    
            return { ...prev, sales_data: updatedSalesData };
        });
    };
    

    const handleDataSubmit = async (): Promise<salesDataRes> => {
        setIsLoading(true);
        setShowModal(resetModal)
        try {
            const response = await axios.post("/api/updatesalesdata", { 
                modifiedSalesData,
                endpoint: `/update-data`,
                destinationEnvLink: destinationUrl
            });
            if(response.data.success) {
                setIsLoading(false);
                setShowModal({
                    show: true,
                    title:'Successfully submitted',
                    message:'Report has been successfully submitted.',
                    type:'success'
                });
                refreshAllData()
            }
            return response.data || {};
        } catch (error) {
            console.error("Error fetching stores:", error);
            return {};
        } finally {
            setIsLoading(false);
            setTimeout(() => setShowModal(resetModal), 3000)
        }
    }

    const handleModalToggle = () => {
        setShowModal({
            show: true,
            title:'Unsaved Changes',
            message:'Do you want to save or discard changes?',
            type:'warning'
        });
    }

    const handleModalProcess = (e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
        if(e) {
            handleDataSubmit();
        }
    }
    const handleModalDiscard = (e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
        if(e) {
            setModifiedSalesData(competitorSalesData);
            setShowModal({
                show: false,
                title:'',
                message:'',
                type:''
            });
        }
    }
    const handleModalClose = (e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
        if(e) {
           setShowModal({
                show: false,
                title:'',
                message:'',
                type:''
            })
        }
    }

    return (
        <div className="w-auto bg-gray-50 rounded-lg px-4 grow pb-4">
            { isLoading && <FullScreenLoader /> }
            {showModal.show && <Modal 
                    title={showModal.title} 
                    message={showModal.message} 
                    type={showModal.type}  
                    handleModalProcess={handleModalProcess} 
                    handleModalDiscard={handleModalDiscard} 
                    handleModalClose={handleModalClose}
                />
            }
            
            <div className="actionbar flex pt-4">
                <div className="rightpart ml-auto flex gap-3">
                <button className="text-white text-sm h-10 px-4 py-2.5 bg-[#221d3e] rounded-lg border 
                        border-[#221d3e] justify-center items-center" 
                        onClick={refreshAllData}><Icons.RefreshBtn color='#ffffff' /></button>
                    <button className="text-white text-sm h-10 px-4 py-2.5 bg-[#221d3e] rounded-lg border 
                        border-[#221d3e] justify-center items-center" 
                        onClick={() => setModifiedSalesData(competitorSalesData)}>Cancel</button>
                    <button className="text-white text-sm h-10 px-4 py-2.5 bg-[#221d3e] rounded-lg border 
                        border-[#221d3e] justify-center items-center" 
                        onClick={handleModalToggle}>Submit</button>
                </div>
            </div>
            <div className="titlebar flex justify-between py-5 px-3 mt-4 bg-white border-t border-[#EAECF0]">
                <div className="flex gap-2 items-center">
                    <div className="text-[#0f1728] text-lg font-bold">Competitor List</div>
                    <div className="w-[77px] px-2 py-1 bg-[#3152ff]/5 rounded-2xl border-[0.2px] border-[#3253ff]/20 justify-center items-center flex text-[#3152ff] text-[10px] font-bold">{salesData?.sales_data?.length} Brands</div>
                </div>
                <div className="flex switchview gap-3">
                    <button type="button" className={`w-10 h-10 flex items-center justify-center 
                    rounded-lg ${selectedView == 'grid' ? 'bg-[#221D3E]': 'border border-[#D0D5DD]'}`} 
                    onClick={() => setSelectedView('grid')}>
                        <Icons.GridView 
                            color={selectedView == 'grid' ? '#ffffff': '#667085'} />
                    </button>
                    <button type="button" className={`w-10 h-10 flex items-center justify-center 
                    rounded-lg ${selectedView == 'list' ? 'bg-[#221D3E]': 'border border-[#D0D5DD]'}`} 
                    onClick={() => setSelectedView('list')}>
                        <Icons.ListView  
                            color={selectedView == 'list' ? '#ffffff': '#667085'} />
                    </button>
                </div>
            </div>
            {
                selectedView == 'list' && (
                    <div className="tableheader flex border-b border-[#eaecf0]">
                        <div className="w-3/12 px-5 py-3 bg-[#f8f9fb]">
                            <div className="text-[#475466] text-base">Name</div>
                        </div>
                        <div className="w-3/12 px-5 py-3 bg-[#f8f9fb]">
                            <div className="text-[#475466] text-base">This Year Sales</div>
                        </div>
                        <div className="w-3/12 px-5 py-3 bg-[#f8f9fb]">
                            <div className="text-[#475466] text-base">Last Year Sales</div>
                        </div>
                        <div className="w-3/12 px-5 py-3 bg-[#f8f9fb]">
                            <div className="text-[#475466] text-base">Comments</div>
                        </div>
                    </div>
                )
            }
            
            <div className="hidden h-0 w-0 grid grid-cols-3 gap-4"></div>
            <div className={`tablebody ${selectedView == 'grid' ? 'grid grid-cols-3 gap-6 py-4' : ''}`}>
                {modifiedSalesData && modifiedSalesData?.sales_data?.map((item: salesData,index:number) => (
                    <div key={index} className="tablerow flex border-b border-[#eaecf0] bg-white" 
                        style={{
                            flexDirection: selectedView == 'grid' ? 'column' : 'row',
                            alignItems: selectedView == 'grid' ? 'start' : 'center',
                            border: selectedView == 'grid' ? '0.5px solid #D0D5DD' : '',
                            borderRadius: selectedView == 'grid' ? '8px' : '',
                            padding: selectedView == 'grid' ? '1rem' : '0',
                        }}>
                        <div className="w-3/12 px-5 py-4" 
                            style={{
                                width: selectedView == 'grid' ? '100%' : '25%',
                                padding: selectedView == 'grid' ? '0' :  '1rem 1.25rem 1rem 1.25rem',
                                margin: selectedView == 'grid' ? '0 0 0.75rem' :  '',
                            }}>
                            <div className="competitorinfo flex gap-3">
                                {/* <div className="image">
                                    <Image className="border border-[#EAECF0] rounded-md"
                                        src={'/images/nikelogo.png'} 
                                        width={40} 
                                        height={40} alt="" />
                                </div> */}
                                <div className="info">
                                    <div className="text-[#0f1728] text-base font-bold">{item.brand}</div>
                                    <div 
                                        className="px-2 py-0.5 rounded-2xl items-center gap-1 inline-flex"
                                        style={{
                                            background: isNegative(item.growth_rate) ? '#FEF3F2' : '#ebfdf2',
                                        }}>
                                        <div className="relative">
                                            <svg width="12" height="13" viewBox="0 0 12 13" fill="none" 
                                            xmlns="http://www.w3.org/2000/svg"> 
                                                <path 
                                                    d={isNegative(item.growth_rate) ? "M6 3.00024L6 10.0002M6 10.0002L9.5 6.50024M6 10.0002L2.5 6.50024" : "M6 10.0002V3.00024M6 3.00024L2.5 6.50024M6 3.00024L9.5 6.50024"}
                                                    stroke={isNegative(item.growth_rate) ? '#B42318' : '#027A48'} 
                                                    strokeWidth="1.5" 
                                                    strokeLinecap="round" 
                                                    strokeLinejoin="round"
                                                />
                                            </svg>
                                        </div>
                                        <div className="text-center">
                                            <span 
                                                className="text-sm"
                                                style={{
                                                    color: isNegative(item.growth_rate) ? '#B42318' : '#027A48',
                                                }}>{item.growth_rate.toFixed(1)}% </span>
                                            <span className="text-[#667085] text-xs">vs last year</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="w-3/12 px-5 py-4" 
                            style={{
                                width: selectedView == 'grid' ? '100%' : '25%',
                                padding: selectedView == 'grid' ? '0' :  '1rem 1.25rem 1rem 1.25rem',
                                margin: selectedView == 'grid' ? '0 0 0.75rem' :  '',
                            }}>

                            {selectedView == 'grid' && 
                                <label className="text-sm text-[#221D3E] mb-1.5">This Year Sales</label>}
                            <input type="text" className="h-10 w-full border border-[#B9B9B9] px-3 py-2 text-[#221D3E] text-xs rounded-lg focus:outline-none" value={item.sales}  onChange={(e) => handleDatachange(index, "sales", e.target.value)}/>
                        </div>
                        {/*NOt updating*/}
                        <div className="w-3/12 px-5 py-4"
                            style={{
                                width: selectedView == 'grid' ? '100%' : '25%',
                                padding: selectedView == 'grid' ? '0' :  '1rem 1.25rem 1rem 1.25rem',
                                margin: selectedView == 'grid' ? '0 0 0.75rem' :  '',
                            }}>
                            {selectedView == 'grid' && 
                                <label className="text-sm text-[#221D3E] mb-1.5">Last Year Sales</label>}
                            <input 
                                type="text" 
                                className="h-10 w-full border border-[#B9B9B9] px-3 py-2 text-[#221D3E] text-xs rounded-lg focus:outline-none" 
                                value={item.ly_sales} disabled={!lastYearEditable} 
                                onChange={(e) => handleDatachange(index, "ly_sales", e.target.value)}/>
                        </div>
                        {/*NOt updating*/}
                        <div className="w-3/12 px-5 py-4"
                            style={{
                                width: selectedView == 'grid' ? '100%' : '25%',
                                padding: selectedView == 'grid' ? '0' :  '1rem 1.25rem 1rem 1.25rem',
                                margin: selectedView == 'grid' ? '0 0 0.75rem' :  '',
                            }}>
                            {selectedView == 'grid' && 
                                <label className="text-sm text-[#221D3E] mb-1.5">Comment</label>}
                            <textarea 
                                className="h-10 w-full border border-[#B9B9B9] px-3 py-2 text-[#221D3E] text-xs rounded-lg focus:outline-none" 
                                value={item.comment ? (item.comment =='nan' ? '' : item.comment ) : ''} 
                                onChange={(e) => handleDatachange(index, "comment", e.target.value)}></textarea>
                        </div>
                    </div>
                ))}
            </div>
        </div>
       
    )
}

export default CompetitorPane;
