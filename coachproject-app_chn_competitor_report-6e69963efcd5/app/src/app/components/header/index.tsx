"use client"
import React, { useEffect, useRef, useState } from 'react'
import Icons from '../svgicons'
import axios from 'axios'
import Modal from '../modal'
import { constrainedMemory } from 'process'
import { useAppConfigContext } from '@/app/appcontext/appConfig'

interface HeaderProps {
    heading: string,
    subheading: string,
    headerButtons: boolean,
    calculationformula?: string
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

const Header: React.FC<HeaderProps> = ({heading, subheading, headerButtons, calculationformula}) => {
    const [showModal, setShowModal] = useState(resetModal);
    const [isLoading, setIsLoading] = useState(false);
    const { destinationUrl } = useAppConfigContext();
    const [lastYearEdit, setLatYearEdit] = useState(false);
    const [yearAndMonth, setYearAndMonth] = useState("YYYY-MM");
    const [etlStatusBtn, setEtlStatusBtn] = useState({disable:false, status:'Start'})
    const downloadLinkRef = useRef<HTMLAnchorElement>(null);

    useEffect(() => {
        if(destinationUrl){
            getYearAndMonth()
            
        }
        if(headerButtons && destinationUrl) {
            getLatYearEditValue()
        }
        if((localStorage.getItem("runningProcessId")) && destinationUrl) {
            poll(
                async () => checkEltStatusCall()
            , 10000);
        } else {
            console.log('no process')
        }
    },[destinationUrl])
    
    const handleDownloadFiles = async() => {
        setIsLoading(true); 
        setShowModal({
            show: true,
            title:'Generating files to download',
            message:'Please wait, downloading files in process',
            type:'warning'
        });       
        
        const currentDate = new Date();
        let month, startYear, endYear;

        if (currentDate.getMonth() === 0) {
            month = 12;
            endYear = currentDate.getFullYear() - 1;
            startYear = endYear - 1;
        } else {
            month = currentDate.getMonth();
            endYear = currentDate.getFullYear();
            startYear = endYear - 1;
        }

        const url = `/download-data?start_year=${startYear}&end_year=${endYear}&month=${month}`;
        
        try {
            const response = await axios.post('/api/downloadzip', 
                {
                    endpoint: url,
                    destinationEnvLink: destinationUrl,
                },
                {
                    responseType: 'blob'
                }
            );

            if (response.status === 200) {
                setShowModal(resetModal);    
                const blob = response.data;
                const blobUrl = window.URL.createObjectURL(blob);
                
                // Use ref-based approach instead of direct DOM manipulation
                if (downloadLinkRef.current) {
                    downloadLinkRef.current.href = blobUrl;
                    downloadLinkRef.current.download = 'download.zip';
                    downloadLinkRef.current.click();
                    window.URL.revokeObjectURL(blobUrl);
                }
            } else {
                console.error("Failed to download file", response);
                setShowModal({
                    show: true,
                    title: 'Download Failed',
                    message: 'Failed to download files. Please try again.',
                    type: 'error'
                });
            }
        } catch (error: any) {
            console.error("Download error:", error);
            
            // Try to parse error message from blob response
            let errorMessage = 'An error occurred while downloading files.';
            if (error.response?.data instanceof Blob) {
                try {
                    const text = await error.response.data.text();
                    const errorData = JSON.parse(text);
                    errorMessage = errorData.message || errorData.error || errorMessage;
                } catch {
                    // Keep default message
                }
            } else if (error.response?.data?.message) {
                errorMessage = error.response.data.message;
            }
            
            setShowModal({
                show: true,
                title: 'Download Failed',
                message: errorMessage,
                type: 'error'
            });
        } finally {
            setIsLoading(false);
        }
    }

    const handleStartetl = async () => {
        localStorage.removeItem("runningProcessId");
        setShowModal({
            show: true,
            title:'Process submitted',
            message:'Please wait, process submitted',
            type:'warning'
        });   
        setEtlStatusBtn({
            disable: true,
            status: "Processing"
        })
        try {
            const { data } = await axios.post('/api/startetl', 
                {
                    endpoint: '/etl-pipeline',
                    destinationEnvLink: destinationUrl,
                }
            );
            if(data.success) {
                setShowModal({
                    show: true,
                    title:'Pipeline Status',
                    message:'Pipeline started successfully',
                    type:'success'
                });  
                setTimeout(() => {
                    setShowModal(resetModal)
                }, 2000);
                const  run_id =  data.data.response.dag_run_id
                localStorage.setItem("runningProcessId", run_id);
                await poll(
                    async () => checkEltStatusCall()
                , 10000);
            }
        } catch (error: any) {
            console.log(error)
            setShowModal({
                show: true,
                title:'Process Failed ' + error.response.data.data.status_code ,
                message:error.response.data.data.error,
                type:'error'
            });
            // Reset button state on failure
            setEtlStatusBtn({
                disable: false,
                status: "Start"
            })
        } finally {
            setTimeout(() => {
                setShowModal(resetModal)
            }, 3000);
        }
    }

    const checkEltStatusCall = async () => {
        const runningId = await localStorage.getItem("runningProcessId");

        if(!runningId) return false;

        setEtlStatusBtn({
            disable: true,
            status: "Running"
        })
        
        try {
            const { data } = await axios.post('/api/startetlstatus', 
                {
                    endpoint: '/check_status',
                    destinationEnvLink: destinationUrl,
                    run_id : runningId
                }
            );
            
            // Check if the status is failed
            if(data.data.status === "failed") {
                setEtlStatusBtn({
                    disable: false,
                    status: "Start"
                })
                localStorage.removeItem("runningProcessId");
                setShowModal({
                    show: true,
                    title:'Pipeline Failed',
                    message:'ETL pipeline execution failed',
                    type:'error'
                });
                setTimeout(() => {
                    setShowModal(resetModal)
                }, 3000);
                return true; // Stop polling
            }
            
            if(data.data.status != "success") {
                setEtlStatusBtn({
                    disable: true,
                    status: data.data.status
                })
                return false; // Continue polling
            } else {
                setEtlStatusBtn({
                    disable: false,
                    status: data.data.status
                })
                setTimeout(() => {
                    setEtlStatusBtn({
                        disable: false,
                        status: "Start"
                    })
                    localStorage.removeItem("runningProcessId");
                }, 2000);
                return true; // Stop polling
            }
        } catch (error) {
            console.error("Error checking ETL status:", error);
            // On error, reset button and stop polling
            setEtlStatusBtn({
                disable: false,
                status: "Start"
            })
            localStorage.removeItem("runningProcessId");
            return true; // Stop polling
        }
    }

    const poll = async (fn: () => Promise<boolean>, interval: number, max = 20) => {
        for (let i = 0; i < max; i++) {
          if (await fn()) return true;
          await new Promise((res) => setTimeout(res, interval));
        }
        // Polling timed out - reset button state
        setEtlStatusBtn({
            disable: false,
            status: "Start"
        })
        localStorage.removeItem("runningProcessId");
        return false;
    };


    const handleLatYearEditToggle = async () => {
        setShowModal({
            show: true,
            title:'Process submitted',
            message:'Please wait, process submitted',
            type:'warning'
        });   
        try{
            const { data } = await axios.post('/api/lastyearedittoggle', 
                {
                    endpoint: '/toggle-edit-settings',
                    destinationEnvLink: destinationUrl,
                }
            );
            if(data.success) {
                setShowModal({
                    show: true,
                    title:'Process Successful',
                    message: `Last year edit set to "${
                        data.data.data.is_last_year_data_editable == 'true' ? 'Enabled' : 'Disabled'}", successfully`,
                    type:'success'
                });  
                setLatYearEdit(data.data.data.is_last_year_data_editable == 'true' ? true : false)
            }
        } catch (error) {
            console.log(error)
        } finally {
            setTimeout(() => {
                setShowModal(resetModal)
            }, 3000);
        }
    }

    const getLatYearEditValue = async () => {
        const { data } = await axios.post('/api/lastyeareditvalue', 
            {
                endpoint: '/get-edit-settings',
                destinationEnvLink: destinationUrl,
            }
        );

        if(data.success) {
            if (data.data.data.is_last_year_data_editable) {
                setLatYearEdit(true)
            }
        }
    }

    const getYearAndMonth = async () => {
        //@TODO: Currently reusing lastyeareditvalue api here, renaming could help more understand. 
        const { data } = await axios.post('/api/lastyeareditvalue', 
            {
                endpoint: '/get-year-and-month',
                destinationEnvLink: destinationUrl,
            }
        );

        if(data.success) {

            if (data.data.data) {
                
                const apiData = data.data.data
                if(apiData?.year >0 && apiData?.month > 0){
                    const yearStr = String(apiData.year)
                    const monthStr = apiData.month<10? `0${apiData.month}`: `${apiData.month}`
                    setYearAndMonth(`${yearStr}-${monthStr}`)
                }
            }
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

    const handleLogout = async () => {
        setIsLoading(true)
        try {
            const response = await fetch('/api/logout', { method: 'GET' });
            if (response.ok) {
                window.location.href = "/";
                setIsLoading(false)
            } else {
                console.error('Logout failed');
            }
        } catch (error) {
            console.error('Error during logout:', error);
        } finally {
            setIsLoading(false)
        }
    };


    return (
        <>
            {showModal.show && <Modal 
                    title={showModal.title} 
                    message={showModal.message} 
                    type={showModal.type}  
                    handleModalClose={handleModalClose}
                />
            }
            {/* Hidden download link using ref */}
            <a ref={downloadLinkRef} style={{display: 'none'}} />
            <div className="bg-[#221d3e]">

                <div className="data-svg-wrapper flex items-center 
                    relative overflow-hidden border-[1px] border-b-[#7F56D9] justify-between">
                    <div className="headerarrow absolute left">
                        <svg width="62" height="8" viewBox="0 0 62 8" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M-16 0H16.5H53.5L61.5 4L53.5 8H16.5H-16L-25 4L-16 0Z" fill="#FFCD00"/>
                        </svg>
                    </div>
                    <div className="logosvg py-5 px-20">
                        <Icons.HeaderLogo />
                    </div>
                    <button type='button' onClick={handleLogout} className="h-10 mx-20 py-2.5 bg-none rounded-lg flex items-center jusity-center text-[#ffffff] text-sm gap-1.5">Logout</button>
                </div>
                <div className="py-6 px-20 flex justify-between items-center gap-6 border-[1px] border-t-[#D0D5DD]">
                    <div className="flex-col justify-start items-start gap-1 inline-flex">
                        <div className="self-stretch text-white text-3xl font-bold font-[--DIN] leading-[38px]">
                            {heading}
                        </div>
                        <div className="self-stretch text-[#c7c7c7] text-base font-normal font-['DIN 2014'] leading-normal">{subheading} {yearAndMonth}</div>
                        {calculationformula && 
                            <div className="self-stretch text-[#c7c7c7] text-base font-normal font-['DIN 2014'] leading-normal mt-10">{calculationformula}</div>
                        }
                        
                    </div>
                    {headerButtons && 
                        (
                            <div className="gap-3 flex">
                                <label className="h-10 inline-flex items-center cursor-pointer border border-[#667085] rounded-lg px-4">
                                    <span className="mr-3 text-sm font-medium text-white">Last Year Edit</span>
                                    <input type="checkbox" value="" 
                                        onChange={handleLatYearEditToggle}  className="sr-only peer" checked={lastYearEdit} />
                                    <div className="relative w-11 h-6 bg-gray-200 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-[#FFCD00] dark:peer-checked:bg-yellow-400"></div>
                                </label>
                                <button onClick={handleStartetl} disabled={etlStatusBtn.disable} className="h-10 px-4 py-2.5 bg-white rounded-lg flex items-center jusity-center text-[#667085] text-sm gap-1.5">
                                    {(etlStatusBtn.status).charAt(0).toUpperCase() + etlStatusBtn.status.slice(1) } ETL
                                </button>

                                <button onClick={handleDownloadFiles} className="h-10 px-4 py-2.5 bg-white rounded-lg flex items-center jusity-center text-[#667085] text-sm gap-1.5">
                                    <Icons.DownloadFile /> <span>Download Files</span>
                                </button>
                            
                            </div>
                        )
                    }
        
                </div>
            </div>
        </>
    )
}

export default Header
