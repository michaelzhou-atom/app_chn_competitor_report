"use client"
import axios from "axios";
import ManagerCard from "../components/managercard";
import { cache, useEffect, useState } from "react";
import FullScreenLoader from "../components/fullscreenloader";
import { useAppConfigContext } from "../appcontext/appConfig";

type Manager = {
  manager: string;
  manager_code: string;
  store_count: string
};

interface ManagersListResponse {
  success: boolean;
  data: Manager[];
}

const Managers = () => {
  const [managers, setManagers] = useState<Manager[]>([]);
  const [isFetched, setIsFetched] = useState(false);
  const [isLoading, setIsloading] = useState(true);
  const { destinationUrl } = useAppConfigContext();
  
  useEffect(() => {
    const fetchManagers = async (): Promise<Manager[]> => {
      try {
        const response = await axios.post<ManagersListResponse>("/api/managers-list", {
          endpoint: '/managers-list',
          destinationEnvLink: destinationUrl,
        });
        return response.data.data;
      } catch (error) {
        console.error("Error fetching managers:", error);
        return [];
      }
    };
    if(!isFetched && destinationUrl) {
      async function fetchData() {
        const managersList = await fetchManagers();
        setManagers(managersList);
        setIsFetched(true)
        setIsloading(false)
      }
      fetchData();
    }
    
  }, [destinationUrl]);

  return (
    <div className="managerslist grid grid-cols-5 gap-4 px-20 py-6">
      {
        isLoading ? <FullScreenLoader/> : (
        <>
          {
            managers?.length > 0 ? (managers.map((manager, index) => (
              <ManagerCard key={index} name={manager.manager} code={manager.manager_code} storeCount={manager.store_count} />
          ))
        ) : (
            <p className="col-span-5 text-center text-gray-500">No managers found.</p>
          )}
        </>
        )
      }
    </div>
  );
};

export default Managers;
