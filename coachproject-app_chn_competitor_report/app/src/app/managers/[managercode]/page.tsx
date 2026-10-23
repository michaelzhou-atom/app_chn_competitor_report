"use client";

import { useAppConfigContext } from "@/app/appcontext/appConfig";
import CompetitorPane from "@/app/components/competitorpane";
import FullScreenLoader from "@/app/components/fullscreenloader";
import Sidebar from "@/app/components/sidebar";
import axios from "axios";
import { useEffect, useState } from "react";
import { use } from "react";

export type Store = {
  status: string,
  store: string,
  store_name: string
};
export type salesDataRes = {
  is_last_year_data_editable?: boolean,
  month?: number,
  store_code?: string,
  year?: number,
  sales_data?: salesData[]
}
export type salesData = {
  brand: string,
  brand_code: string,
  comment: string,
  comp: string,
  growth_rate: number,
  ly_sales: number,
  ly_update_enable_status: null | string,
  manager: string,
  month: number,
  sales: number,
  status: string,
  store: string,
  store_category: string,
  store_name: string,
  year: number
}



const Managers = ({ params }: { params: Promise<{ managercode: string }> }) => {
  const [storesList, setStoresList] = useState<Store[]>([]);
  const [salesData, setSalesData] = useState<salesDataRes>({sales_data:[]});
  const [isFetched, setIsFetched] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [currentStoreCode, setrCurrentStoreCode] = useState('');
  const { destinationUrl } = useAppConfigContext();
  const { managercode } = use(params);
  
  useEffect(() => {
    if(!destinationUrl) return;
    if(!isFetched) {
      async function fetchData() {
        const stores = await getStores(managercode);
        setStoresList(stores);
        setIsFetched(true)
      }
      fetchData();
    }
  }, [managercode, destinationUrl]);

  const getSalesData = async (storeCode: string): Promise<salesDataRes> => {
    try {
      const response = await axios.post("/api/salesdata", { 
        storeCode,
        endpoint: `/sales-data/${storeCode}`,
        destinationEnvLink: destinationUrl,
      });
      
      const resData = typeof response.data === "string" ? JSON.parse(response.data) : response.data;
      
      return resData.data || { sales_data: [] };
    } catch (error) {
      console.error("Error fetching sales data:", error);
      return { sales_data: [] };
    }
  };
  
  const getStores = async (managerCode: string): Promise<Store[]> => {
    try {
      const response = await axios.post("/api/stores-list", {
        endpoint: `/stores-list/${managerCode}`,
        destinationEnvLink: destinationUrl
      });
      return response.data.data || [];
    } catch (error) {
      console.error("Error fetching stores:", error);
      return [];
    }
  }

  const storeData = async (storeCode: string) => {
    setrCurrentStoreCode(storeCode)
    setIsLoading(true);
    await getSalesData(storeCode).then(response => {setSalesData(response); setIsLoading(false)} );
  }


  return (
    <div className="managerslist flex px-20 py-6 gap-6">
      {isLoading && <FullScreenLoader /> }
      <Sidebar 
        storesList={storesList} 
        storeData={storeData} 
        managerCode={managercode}
      /> 
      <CompetitorPane salesData={salesData} 
      destinationUrl={destinationUrl}
      refreshAllData={()=> storeData(currentStoreCode)} />
    </div>
  );
};

export default Managers;
