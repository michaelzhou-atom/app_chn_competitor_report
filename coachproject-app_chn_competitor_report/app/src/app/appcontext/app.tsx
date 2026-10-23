"use client"
import { usePathname } from 'next/navigation';
import { useRouter } from 'next/router';
import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';

interface AppProviderProps {
  children: ReactNode;
}

interface InprogressType {inProgress: boolean, title: string, message: string}

interface AppContextType {
  firstName: string | null,
  currentDataType: string,
  username: string | null,
  progress: InprogressType,
  handleInprogress: (progressVal: InprogressType) => void
}



const AppContext = createContext<AppContextType | undefined>(undefined);



export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [firstName, setFirstName] = useState<string | null>(null);
  const [username, setUsername] = useState<string | null>(null);
  const [currentDataType, setCurrentDataType] = useState('sample-allocation');
  const [progress, setProgress] = useState({ inProgress: false, title: '', message: '' });
  const pathname  = usePathname();
  
  useEffect(() => {
    if (pathname.includes("sample-allocation")) {
      setCurrentDataType("sample-allocation");
    } else if (pathname.includes("production-allocation")) {
      setCurrentDataType("production-allocation");
    } else {
      setCurrentDataType("");
    }
  }, [pathname]);

  useEffect(() => {
    const cookies = document.cookie.split('; ').reduce((acc, cookie) => {
      const [key, value] = cookie.split('=');
      acc[key] = decodeURIComponent(value);
      return acc;
    }, {} as Record<string, string>);
    setFirstName(cookies['firstname'] || null);
    setUsername(cookies['username'] || null);
  }, []);

  const handleInprogress = (progressVal:InprogressType) => setProgress({ 
    inProgress: progressVal.inProgress, 
    title: progressVal.title,
    message: progressVal.message 
  })

  return (
    <AppContext.Provider value={{ 
        firstName, 
        currentDataType,
        username,
        progress,
        handleInprogress
    }}>
      {children}
    </AppContext.Provider>
  );
};

// Custom hook for accessing the context
export const useAppContext = (): AppContextType => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};
