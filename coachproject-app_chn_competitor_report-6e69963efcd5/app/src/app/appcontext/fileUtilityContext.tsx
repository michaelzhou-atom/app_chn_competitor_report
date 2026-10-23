"use client"
import axios from 'axios';
import { usePathname } from 'next/navigation';
import { useRouter } from 'next/router';
import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';

interface FileUtilityContextType {
  folderName: string,
  folderPath: string
  folderData: any[],
  destinationUrl: string,
  envVal: string,
  folderAnalyzer: boolean,
  getDestinationUrl: (val:string) => void;
  getEnvVal: (val:string) => void;
  handleSetFoldername: (val:string) => void;
  handleSetFolderPath: (val:string) => void;
  handleSetFolderAnalyzer: (val: boolean) => void;
  fetchData: (val: string) => void;
}

const FileUtilityContext = createContext<FileUtilityContextType | undefined>(undefined);

interface FileUtilityProviderProps {
  children: ReactNode;
}

export const FileUtilityProvider: React.FC<FileUtilityProviderProps> = ({ children }) => {
  const [folderName, setFolderName] = useState<string>('');
  const [folderPath, setFolderPath] = useState<string>('');
  const [folderData, setFolderData] = useState<any[]>([]);
  const [destinationUrl, setDestinationUrl] = useState('');
  const [folderAnalyzer, setFolderAnalyzer] = useState(true)
  const [envVal, setEnvVal] = useState('dev');
  const pathname  = usePathname();

  useEffect(() => {
    fetchData(folderPath)
  }, [pathname]);

  const fetchData = async (folderPath: string) => {
    setFolderAnalyzer(true)
    if(!folderPath || !pathname.includes('viewfolder')) return;
    const endpoint = destinationUrl+"display_adhoc_contents/sca/?s3_url="+folderPath;
    try {
      const response  = await axios.get(endpoint);
      const data = await response.data.InterfaceNames;
      if(data) {
        setFolderData(data)
      } else {
        setFolderData([])
      }
    } catch (error) {
      console.log(error)
    } finally {
      setFolderAnalyzer(false)
    }
  }
  

  const handleSetFoldername = (val:string) => {
    //setFolderName('');
    setFolderName(val)
  };
  const handleSetFolderPath = (val:string) => setFolderPath(val);
  const handleSetFolderAnalyzer = (val:boolean) => setFolderAnalyzer(val);
  const getDestinationUrl = (val:string) => setDestinationUrl(val);
  const getEnvVal = (val:string) => setEnvVal(val);


  return (
    <FileUtilityContext.Provider value={{ 
        folderName, 
        folderPath,
        folderData,
        destinationUrl,
        envVal,
        folderAnalyzer,
        getDestinationUrl,
        getEnvVal,
        handleSetFoldername,
        handleSetFolderPath,
        handleSetFolderAnalyzer,
        fetchData
    }}>
      {children}
    </FileUtilityContext.Provider>
  );
};

export const useFileUtilityContext = (): FileUtilityContextType => {
  const context = useContext(FileUtilityContext);
  if (!context) {
    throw new Error('useFileUtilityContext must be used within an FileUtilityProvider');
  }
  return context;
};
